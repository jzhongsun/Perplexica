import os
import json
import uuid
from typing import List
from fastapi import HTTPException, UploadFile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader
)

from app.core.config import get_settings
from app.features.embedding.service import EmbeddingService
from .schemas import FileUploadResponse, FileResponse

class FileService:
    """Service for handling file uploads and processing."""

    def __init__(self):
        self.settings = get_settings()
        self.upload_dir = os.path.join(os.getcwd(), "uploads")
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        self.embedding_service = EmbeddingService()

        # Ensure upload directory exists
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def process_files(
        self,
        files: List[UploadFile],
        embedding_model: str,
        embedding_model_provider: str
    ) -> FileUploadResponse:
        """
        Process uploaded files.
        
        Args:
            files: List of uploaded files
            embedding_model: Name of the embedding model to use
            embedding_model_provider: Provider of the embedding model
            
        Returns:
            FileUploadResponse containing processed file information
            
        Raises:
            HTTPException: If file processing fails
        """
        processed_files = []

        for file in files:
            file_extension = file.filename.split(".")[-1].lower()
            
            if file_extension not in ["pdf", "docx", "txt"]:
                raise HTTPException(
                    status_code=400,
                    detail="File type not supported"
                )

            # Generate unique file ID and save file
            file_id = str(uuid.uuid4())
            file_path = os.path.join(
                self.upload_dir,
                f"{file_id}.{file_extension}"
            )
            
            try:
                # Save uploaded file
                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                # Load and split document
                if file_extension == "pdf":
                    loader = PyPDFLoader(file_path)
                elif file_extension == "docx":
                    loader = Docx2txtLoader(file_path)
                else:  # txt
                    loader = TextLoader(file_path)

                docs = await loader.aload()
                splits = await self.splitter.asplit_documents(docs)

                # Save extracted text
                extracted_path = os.path.join(
                    self.upload_dir,
                    f"{file_id}-extracted.json"
                )
                with open(extracted_path, "w") as f:
                    json.dump({
                        "title": file.filename,
                        "contents": [split.page_content for split in splits]
                    }, f)

                # Generate embeddings
                embeddings = await self.embedding_service.create_embeddings(
                    [split.page_content for split in splits],
                    embedding_model,
                    embedding_model_provider
                )

                # Save embeddings
                embeddings_path = os.path.join(
                    self.upload_dir,
                    f"{file_id}-embeddings.json"
                )
                with open(embeddings_path, "w") as f:
                    json.dump({
                        "title": file.filename,
                        "embeddings": embeddings
                    }, f)

                processed_files.append(
                    FileResponse(
                        fileName=file.filename,
                        fileExtension=file_extension,
                        fileId=file_id
                    )
                )

            except Exception as e:
                # Clean up files in case of error
                for path in [file_path, extracted_path, embeddings_path]:
                    if os.path.exists(path):
                        os.remove(path)
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing file: {str(e)}"
                )

        return FileUploadResponse(files=processed_files) 