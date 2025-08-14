"""Document processing module."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import httpx

@dataclass
class Document:
    """Document class."""
    page_content: str
    metadata: Dict[str, Any]

async def get_documents_from_links(urls: List[str]) -> List[Document]:
    """Get documents from URLs.
    
    Args:
        urls: List of URLs
        
    Returns:
        List of documents
    """
    docs = []
    
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                response = await client.get(url)
                response.raise_for_status()
                
                # TODO: Add proper HTML/text extraction
                content = response.text
                
                docs.append(Document(
                    page_content=content,
                    metadata={
                        "title": url,
                        "url": url
                    }
                ))
            except Exception as e:
                print(f"Error getting document from URL {url}: {e}")
                continue
    
    return docs 