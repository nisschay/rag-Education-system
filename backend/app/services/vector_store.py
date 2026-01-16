import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict
from app.services.gemini_service import gemini_service

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=os.getenv("CHROMA_DIR", "./storage/chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
    
    def get_or_create_collection(self, course_id: int):
        """Get or create collection for a course"""
        collection_name = f"course_{course_id}"
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"course_id": str(course_id)}
        )
    
    async def add_documents(
        self, 
        course_id: int, 
        documents: List[str], 
        metadatas: List[Dict],
        ids: List[str]
    ):
        """Add documents to vector store"""
        collection = self.get_or_create_collection(course_id)
        
        # Generate embeddings
        embeddings = []
        for doc in documents:
            embedding = await gemini_service.generate_embedding(doc)
            embeddings.append(embedding)
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
            ids=ids
        )
    
    async def query(
        self,
        course_id: int,
        query_text: str,
        n_results: int = 5,
        where: Dict = None
    ) -> Dict:
        """Query vector store"""
        collection = self.get_or_create_collection(course_id)
        
        # Generate query embedding
        query_embedding = await gemini_service.generate_embedding(query_text)
        
        # Query collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return results
    
    def delete_collection(self, course_id: int):
        """Delete a course collection"""
        try:
            self.client.delete_collection(f"course_{course_id}")
        except:
            pass

vector_store = VectorStore()
