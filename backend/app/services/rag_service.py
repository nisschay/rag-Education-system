from typing import List, Dict
from app.services.vector_store import vector_store
from app.services.gemini_service import gemini_service
from app.utils.logging_config import get_logger

logger = get_logger("rag_service")

class RAGService:
    
    async def retrieve_context(
        self,
        course_id: int,
        query: str,
        session_context: Dict
    ) -> List[Dict]:
        """Main retrieval function - simple semantic search"""
        
        logger.info(f"Retrieving context for query: {query[:100]}...")
        
        # Simple query - just find relevant chunks by semantic similarity
        # No complex filtering that might exclude results
        results = await vector_store.query(
            course_id=course_id,
            query_text=query,
            n_results=10,
            where=None  # No filtering - let semantic search do the work
        )
        
        logger.info(f"Retrieved {len(results.get('documents', [[]])[0])} chunks")
        
        # Format results
        chunks = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0
                })
        
        logger.debug(f"Formatted {len(chunks)} chunks for response generation")
        return chunks
    
    async def generate_response(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        session_context: Dict,
        course_name: str
    ) -> str:
        """Generate response using retrieved context"""
        
        logger.info(f"Generating response for: {query[:100]}...")
        logger.info(f"Using {len(retrieved_chunks)} context chunks")
        
        # Analyze query complexity to adjust response length
        query_words = len(query.split())
        is_simple_query = query_words < 10 and not any(word in query.lower() for word in ['explain', 'describe', 'compare', 'analyze', 'list', 'all', 'everything', 'detail'])
        is_comprehensive_query = any(word in query.lower() for word in ['everything', 'all', 'comprehensive', 'detailed', 'complete', 'full'])
        
        # Build context from chunks with clear formatting
        if retrieved_chunks:
            # Use fewer chunks for simple queries
            num_chunks = 3 if is_simple_query else 8
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks[:num_chunks], 1):
                source = chunk['metadata'].get('source', chunk['metadata'].get('unit_name', 'Document'))
                context_parts.append(f"--- Context {i} (from: {source}) ---\n{chunk['content']}")
            context_text = "\n\n".join(context_parts)
        else:
            context_text = "No relevant context found in the documents."
        
        # Build system instruction - adjust based on query type
        length_instruction = ""
        if is_simple_query:
            length_instruction = "Keep your answer concise and to the point - a few sentences is often enough for simple questions."
        elif is_comprehensive_query:
            length_instruction = "Provide a comprehensive, detailed answer with examples and thorough explanations."
        else:
            length_instruction = "Match the depth and length of your response to the complexity of the question."
        
        # Check if we have relevant context (low distance = good match)
        has_relevant_context = False
        if retrieved_chunks:
            # Distance < 1.0 typically means good semantic match in ChromaDB
            min_distance = min(chunk.get('distance', 999) for chunk in retrieved_chunks)
            has_relevant_context = min_distance < 1.5 and len(retrieved_chunks) > 0
        
        if has_relevant_context:
            system_instruction = f"""You are an expert AI tutor helping students learn about: {course_name}.

Your responsibilities:
1. Answer the student's specific question directly
2. Use the provided context from their study materials
3. Use markdown formatting for better readability (headers, bullet points, bold text, etc.)
4. If the context doesn't fully cover the question, supplement with your general knowledge but mention this

Response guidelines:
- {length_instruction}
- For simple yes/no or factual questions, be brief
- For "what is" questions, give a clear definition and brief explanation
- For "explain" or "how" questions, provide more detail
- For requests for "everything" or "all", be comprehensive with structured formatting
- Use bullet points and headers to organize longer responses
- Always format code examples in code blocks"""
        else:
            # No relevant context found - use LLM's general knowledge
            logger.info("No relevant context found in documents, falling back to LLM knowledge")
            system_instruction = f"""You are an expert AI tutor helping students learn about: {course_name}.

IMPORTANT: The student's study materials don't contain information about this specific topic.
Use your general knowledge to provide a helpful answer.

Your responsibilities:
1. Answer the student's question using your general knowledge
2. Be clear that this information comes from general knowledge, not their uploaded materials
3. Use markdown formatting for better readability
4. Suggest they upload relevant materials if they want topic-specific answers

Response guidelines:
- {length_instruction}
- Start with a brief note like "📚 This topic isn't in your uploaded materials, but here's what I know:"
- Provide accurate, educational content
- Use bullet points and headers to organize responses"""

        # Build prompt with clear separation
        if has_relevant_context:
            prompt = f"""Context from study materials:

{context_text}

---

Student's question: "{query}"

Provide a helpful answer using the context above. Remember to match the response length to the question complexity."""
        else:
            prompt = f"""Student's question: "{query}"

The student is learning about {course_name} but this specific question isn't covered in their uploaded materials.
Provide a helpful answer using your general knowledge. Remember to match the response length to the question complexity."""

        # Generate response
        logger.debug(f"Sending prompt to Gemini (length: {len(prompt)})")
        response = await gemini_service.generate_text(prompt, system_instruction)
        logger.info(f"Generated response (length: {len(response)})")
        return response
    
    async def generate_streaming_response(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        session_context: Dict,
        course_name: str
    ):
        """Generate streaming response"""
        
        # Build context from chunks
        if retrieved_chunks:
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks[:8], 1):
                source = chunk['metadata'].get('source', chunk['metadata'].get('unit_name', 'Document'))
                context_parts.append(f"--- Context {i} (from: {source}) ---\n{chunk['content']}")
            context_text = "\n\n".join(context_parts)
        else:
            context_text = "No relevant context found."
        
        system_instruction = f"""You are an expert AI tutor for: {course_name}.
Answer the student's question using the provided context.
Be specific, helpful, and give answers relevant to their actual question."""

        prompt = f"""Context from study materials:
{context_text}

---

Student's question: "{query}"

Provide a helpful answer:"""

        async for chunk in gemini_service.generate_streaming(prompt, system_instruction):
            yield chunk

rag_service = RAGService()
