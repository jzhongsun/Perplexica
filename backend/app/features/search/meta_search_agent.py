"""Meta search agent implementation."""
import json
import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from langchain_core.messages import BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableMap, RunnableSequence

from app.core.utils.compute_similarity import compute_similarity
from app.core.utils.format_history import format_chat_history_as_string
from app.features.searxng import search_searxng
from app.features.documents import Document, get_documents_from_links

# @register_agent_type("meta_search_agent")
# class MetaSearchAgent (Agent, DeclarativeSpecMixin):
@dataclass
class MetaSearchAgent:
    """Meta search agent class."""
    active_engines: List[str]
    query_generator_prompt: str
    response_prompt: str
    rerank: bool
    rerank_threshold: float
    search_web: bool
    summarizer: bool

    def __post_init__(self):
        """Post init setup."""
        self.str_parser = StrOutputParser()

    async def create_search_retriever_chain(
        self, 
        llm: BaseChatModel
    ) -> RunnableSequence:
        """Create search retriever chain.
        
        Args:
            llm: Language model
            
        Returns:
            Search retriever chain
        """
        return RunnableSequence.from_([
            RunnableMap({
                "chat_history": lambda x: x["chat_history"],
                "query": lambda x: x["query"]
            }),
            ChatPromptTemplate.from_messages([
                ["system", self.query_generator_prompt],
                MessagesPlaceholder(variable_name="chat_history"),
                ["user", "{query}"]
            ]),
            llm,
            self.str_parser,
            lambda question: self._process_search_results(question)
        ])

    async def _process_search_results(self, question: str) -> Dict[str, Any]:
        """Process search results.
        
        Args:
            question: Search query
            
        Returns:
            Processed search results
        """
        if "<think>" in question:
            # Extract URLs from think tags
            urls = []
            start = question.find("<think>") + 7
            end = question.find("</think>")
            while start != -1 and end != -1:
                urls.extend(question[start:end].strip().split("\n"))
                start = question.find("<think>", end) + 7
                end = question.find("</think>", start)

            # Get documents from URLs
            docs = []
            for url in urls:
                try:
                    doc = await get_documents_from_links([url])
                    if doc:
                        docs.extend(doc)
                except Exception as e:
                    print(f"Error getting document from URL {url}: {e}")

            return {"query": question, "docs": docs}
        else:
            # Remove think tags
            question = question.replace("<think>", "").replace("</think>", "")

            # Search using SearxNG
            try:
                results = await search_searxng(
                    question,
                    engines=self.active_engines,
                    language="en"
                )
                
                docs = [
                    Document(
                        page_content=result.get("content") or (
                            result.get("title") if "youtube" in self.active_engines else ""
                        ),
                        metadata={
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "img_src": result.get("img_src")
                        }
                    )
                    for result in results.get("results", [])
                ]
                
                return {"query": question, "docs": docs}
            except Exception as e:
                print(f"Error searching with SearxNG: {e}")
                return {"query": question, "docs": []}

    async def create_answering_chain(
        self,
        llm: BaseChatModel,
        file_ids: List[str],
        embeddings: Embeddings,
        optimization_mode: str,
        system_instructions: str
    ) -> RunnableSequence:
        """Create answering chain.
        
        Args:
            llm: Language model
            file_ids: List of file IDs
            embeddings: Embeddings model
            optimization_mode: Optimization mode
            system_instructions: System instructions
            
        Returns:
            Answering chain
        """
        return RunnableSequence.from_([
            RunnableMap({
                "system_instructions": lambda _: system_instructions,
                "query": lambda x: x["query"],
                "chat_history": lambda x: x["chat_history"],
                "date": lambda _: "",  # TODO: Add date handling
                "context": RunnableMap({
                    "input": lambda x: x,
                    "process": self._process_context
                })
            }),
            ChatPromptTemplate.from_messages([
                ["system", self.response_prompt],
                MessagesPlaceholder(variable_name="chat_history"),
                ["user", "{query}"]
            ]),
            llm,
            self.str_parser
        ])

    async def _process_context(
        self,
        query: str,
        chat_history: List[BaseMessage],
        file_ids: List[str],
        embeddings: Embeddings,
        optimization_mode: str
    ) -> str:
        """Process context for answering chain.
        
        Args:
            query: Search query
            chat_history: Chat history
            file_ids: List of file IDs
            embeddings: Embeddings model
            optimization_mode: Optimization mode
            
        Returns:
            Processed context
        """
        processed_history = format_chat_history_as_string(chat_history)
        
        docs = []
        if self.search_web:
            search_chain = await self.create_search_retriever_chain(llm)
            search_results = await search_chain.ainvoke({
                "chat_history": processed_history,
                "query": query
            })
            query = search_results["query"]
            docs = search_results["docs"]

        sorted_docs = await self._rerank_docs(
            query,
            docs,
            file_ids,
            embeddings,
            optimization_mode
        )

        return self._process_docs(sorted_docs)

    async def _rerank_docs(
        self,
        query: str,
        docs: List[Document],
        file_ids: List[str],
        embeddings: Embeddings,
        optimization_mode: str
    ) -> List[Document]:
        """Rerank documents.
        
        Args:
            query: Search query
            docs: List of documents
            file_ids: List of file IDs
            embeddings: Embeddings model
            optimization_mode: Optimization mode
            
        Returns:
            Reranked documents
        """
        if not docs and not file_ids:
            return docs

        # Load file data
        files_data = []
        for file_id in file_ids:
            try:
                file_path = Path("uploads") / file_id
                content_path = file_path.with_suffix(".json")
                embeddings_path = file_path.with_name(f"{file_path.stem}-embeddings.json")

                if content_path.exists() and embeddings_path.exists():
                    with open(content_path) as f:
                        content = json.load(f)
                    with open(embeddings_path) as f:
                        emb = json.load(f)

                    files_data.extend([
                        {
                            "fileName": content["title"],
                            "content": c,
                            "embeddings": e
                        }
                        for c, e in zip(content["contents"], emb["embeddings"])
                    ])
            except Exception as e:
                print(f"Error loading file data for {file_id}: {e}")

        if query.lower() == "summarize":
            return docs[:15]

        docs_with_content = [doc for doc in docs if doc.page_content]

        if optimization_mode == "speed" or not self.rerank:
            if files_data:
                query_embedding = await embeddings.embed_query(query)
                
                file_docs = [
                    Document(
                        page_content=data["content"],
                        metadata={
                            "title": data["fileName"],
                            "url": "File"
                        }
                    )
                    for data in files_data
                ]

                similarities = [
                    {
                        "index": i,
                        "similarity": compute_similarity(query_embedding, data["embeddings"])
                    }
                    for i, data in enumerate(files_data)
                ]

                sorted_docs = [
                    file_docs[sim["index"]]
                    for sim in sorted(
                        [s for s in similarities if s["similarity"] > self.rerank_threshold],
                        key=lambda x: x["similarity"],
                        reverse=True
                    )[:15]
                ]

                if docs_with_content:
                    sorted_docs = sorted_docs[:8]

                return sorted_docs + docs_with_content[:15 - len(sorted_docs)]
            else:
                return docs_with_content[:15]

        # Full reranking
        doc_embeddings = await embeddings.embed_documents(
            [doc.page_content for doc in docs_with_content]
        )
        query_embedding = await embeddings.embed_query(query)

        # Add file documents
        docs_with_content.extend([
            Document(
                page_content=data["content"],
                metadata={
                    "title": data["fileName"],
                    "url": "File"
                }
            )
            for data in files_data
        ])
        doc_embeddings.extend([data["embeddings"] for data in files_data])

        # Calculate similarities
        similarities = [
            {
                "index": i,
                "similarity": compute_similarity(query_embedding, emb)
            }
            for i, emb in enumerate(doc_embeddings)
        ]

        # Sort and filter documents
        sorted_docs = [
            docs_with_content[sim["index"]]
            for sim in sorted(
                [s for s in similarities if s["similarity"] > self.rerank_threshold],
                key=lambda x: x["similarity"],
                reverse=True
            )[:15]
        ]

        return sorted_docs

    def _process_docs(self, docs: List[Document]) -> str:
        """Process documents into string format.
        
        Args:
            docs: List of documents
            
        Returns:
            Processed documents string
        """
        return "\n".join(
            f"{i+1}. {doc.metadata['title']} {doc.page_content}"
            for i, doc in enumerate(docs)
        )

    async def search_and_answer(
        self,
        message: str,
        history: List[BaseMessage],
        llm: BaseChatModel,
        embeddings: Embeddings,
        optimization_mode: str,
        file_ids: List[str],
        system_instructions: str
    ) -> asyncio.Queue:
        """Search and answer query.
        
        Args:
            message: User message
            history: Chat history
            llm: Language model
            embeddings: Embeddings model
            optimization_mode: Optimization mode
            file_ids: List of file IDs
            system_instructions: System instructions
            
        Returns:
            Response queue
        """
        queue = asyncio.Queue()
        
        try:
            answering_chain = await self.create_answering_chain(
                llm,
                file_ids,
                embeddings,
                optimization_mode,
                system_instructions
            )

            async for event in answering_chain.astream({
                "chat_history": history,
                "query": message
            }):
                await queue.put({
                    "type": "response",
                    "data": event
                })

            await queue.put({"type": "done"})
        except Exception as e:
            print(f"Error in search_and_answer: {e}")
            await queue.put({
                "type": "error",
                "data": str(e)
            })

        return queue 