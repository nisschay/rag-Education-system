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
        """Generate response using retrieved context with strict grounding."""

        logger.info(f"Generating response for: {query[:100]}...")
        logger.info(f"Using {len(retrieved_chunks)} context chunks")

        query_lower = query.lower()
        is_simple_query = len(query.split()) < 10 and not any(
            word in query_lower for word in [
                'explain', 'describe', 'compare', 'analyze', 'list',
                'all', 'everything', 'detail', 'how', 'why'
            ]
        )
        is_comprehensive_query = any(
            word in query_lower for word in [
                'everything', 'all', 'comprehensive', 'detailed', 'complete', 'full'
            ]
        )

        if retrieved_chunks:
            num_chunks = 3 if is_simple_query else 6
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks[:num_chunks], 1):
                source = chunk['metadata'].get('source', chunk['metadata'].get('unit_name', 'Document'))
                distance = chunk.get('distance', 0)
                relevance = "HIGH" if distance < 0.5 else "MEDIUM" if distance < 1.0 else "LOW"
                context_parts.append(
                    f"[Source {i}: {source}] [Relevance: {relevance}]\n{chunk['content']}"
                )
            context_text = "\n\n---\n\n".join(context_parts)
        else:
            context_text = "NO CONTEXT AVAILABLE"

        if is_simple_query:
            length_instruction = "Keep your answer concise - 2-3 sentences for simple factual questions."
        elif is_comprehensive_query:
            length_instruction = "Provide a thorough answer with examples, but only from the provided sources."
        else:
            length_instruction = "Match response length to question complexity. Be thorough but not verbose."

        has_relevant_context = False
        if retrieved_chunks:
            min_distance = min(chunk.get('distance', 999) for chunk in retrieved_chunks)
            has_relevant_context = min_distance < 1.2 and len(retrieved_chunks) > 0

        if has_relevant_context:
            system_instruction = f"""You are an AI tutor for: {course_name}.
## CRITICAL RULES - FOLLOW EXACTLY:
1. ONLY use information from the provided context blocks below
2. If the context doesn't contain specific information, say "The provided materials don't cover this specifically" - do not make up information
3. Always cite which source you're drawing from (e.g., "According to Source 1...")
4. If context is marked LOW relevance, treat it skeptically
5. Distinguish between:
   - Direct quotes/facts from sources (state confidently with citation)
   - Inferences from the sources (prefix with "Based on the context, it appears that...")
   - Information NOT in sources (state "This isn't covered in your materials" before using general knowledge)
## Response Guidelines:
- {length_instruction}
- Use markdown formatting (headers, bullets, bold) for readability
- For definitions: give the exact definition from sources if available
- For explanations: synthesize from sources, cite each major point
- For comparisons: only compare aspects covered in the sources
- Avoid speculation; if unsure, say so explicitly"""

            prompt = f"""## Student's Study Materials:
{context_text}
---
## Student's Question: "{query}"
Provide a helpful, grounded answer. Remember:
- Cite your sources (Source 1, Source 2, etc.)
- If unsure, say so rather than guessing
- Stay within what the materials actually say"""
        else:
            logger.info("No relevant context found; falling back to general knowledge with disclaimer")
            system_instruction = f"""You are an AI tutor helping with: {course_name}.
## IMPORTANT NOTICE:
The student's uploaded materials do NOT contain information about this specific question.
You MUST be transparent about this.
## Your Approach:
1. Start with: "📚 I couldn't find this in your uploaded materials. Here's what I know from general knowledge:"
2. Provide helpful, accurate information from your training
3. If uncertain about anything, say so
4. Suggest what materials they might upload to get source-specific answers
## Guidelines:
- {length_instruction}
- Use markdown formatting
- Be educational and helpful
- Recommend uploading relevant materials for verified answers"""

            prompt = f"""Student's Question: "{query}"
The student is studying {course_name} but their uploaded materials don't cover this topic.
Answer using general knowledge with the required disclaimer."""

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
        """Generate streaming response with grounded prompt."""

        if retrieved_chunks:
            context_parts = []
            for i, chunk in enumerate(retrieved_chunks[:6], 1):
                source = chunk['metadata'].get('source', chunk['metadata'].get('unit_name', 'Document'))
                distance = chunk.get('distance', 0)
                relevance = "HIGH" if distance < 0.5 else "MEDIUM" if distance < 1.0 else "LOW"
                context_parts.append(
                    f"[Source {i}: {source}] [Relevance: {relevance}]\n{chunk['content']}"
                )
            context_text = "\n\n---\n\n".join(context_parts)
        else:
            context_text = "NO CONTEXT AVAILABLE"

        has_relevant_context = False
        if retrieved_chunks:
            min_distance = min(chunk.get('distance', 999) for chunk in retrieved_chunks)
            has_relevant_context = min_distance < 1.2 and len(retrieved_chunks) > 0

        if has_relevant_context:
            system_instruction = f"""You are an AI tutor for: {course_name}.
Use ONLY the provided context blocks. Cite sources (Source 1, Source 2...). If context seems weak, say so and avoid guessing."""

            prompt = f"""## Student's Study Materials:
{context_text}
---
## Student's Question: "{query}"
Stream a grounded answer. If unsure, say so explicitly."""
        else:
            system_instruction = f"""You are an AI tutor helping with: {course_name}.
The uploaded materials don't cover this; respond with general knowledge and a clear disclaimer."""

            prompt = f"""Student's Question: "{query}"
No relevant uploaded context found. Start with the disclaimer, then answer concisely."""

        async for chunk in gemini_service.generate_streaming(prompt, system_instruction):
            yield chunk

rag_service = RAGService()
