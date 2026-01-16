from typing import List, Dict
from app.services.vector_store import vector_store
from app.services.gemini_service import gemini_service

class RAGService:
    
    RETRIEVAL_STRATEGIES = {
        "mindmap": {
            "levels": [2, 3],
            "top_k": 15,
        },
        "teach_sequential": {
            "levels": [2, 3],
            "top_k": 8,
        },
        "explain_concept": {
            "levels": [3, 4],
            "top_k": 10,
        },
        "quiz": {
            "levels": [2, 3],
            "top_k": 10,
        },
        "clarify": {
            "levels": [3, 4],
            "top_k": 5,
        }
    }
    
    async def retrieve_context(
        self,
        course_id: int,
        query: str,
        session_context: Dict
    ) -> List[Dict]:
        """Main retrieval function"""
        
        # Classify query intent
        intent_data = await gemini_service.classify_query_intent(query, session_context)
        intent = intent_data.get("intent", "explain_concept")
        
        # Get retrieval strategy
        strategy = self.RETRIEVAL_STRATEGIES.get(intent, self.RETRIEVAL_STRATEGIES["explain_concept"])
        
        # Build metadata filter - ChromaDB requires $and for multiple conditions
        conditions = []
        
        # Filter by hierarchy levels
        conditions.append({"hierarchy_level": {"$in": strategy["levels"]}})
        
        # Filter by current unit if in session context
        if session_context.get("current_unit_id"):
            conditions.append({"unit_id": session_context["current_unit_id"]})
        
        # Wrap in $and if multiple conditions, otherwise use single condition
        where_filter = {"$and": conditions} if len(conditions) > 1 else conditions[0] if conditions else None
        
        # Query vector store
        results = await vector_store.query(
            course_id=course_id,
            query_text=query,
            n_results=strategy["top_k"],
            where=where_filter
        )
        
        # Format results
        chunks = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else 0
                })
        
        return chunks
    
    async def generate_response(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        session_context: Dict,
        course_name: str
    ) -> str:
        """Generate response using retrieved context"""
        
        # Build context from chunks
        context_text = "\n\n".join([
            f"[Source: {chunk['metadata'].get('unit_name', 'Unknown')}]\n{chunk['content']}"
            for chunk in retrieved_chunks[:8]  # Limit context
        ])
        
        # Build system instruction
        system_instruction = f"""You are an expert tutor for the course: {course_name}.

Current Session Context:
- Current Unit: {session_context.get('current_unit_name', 'Not set')}
- Teaching Mode: {session_context.get('teaching_mode', 'qa')}
- Previous Topic: {session_context.get('last_topic', 'None')}

Your role:
1. Answer questions clearly and thoroughly
2. Use examples and analogies
3. Reference the source materials provided
4. Adapt to the student's level
5. Encourage deeper understanding

Guidelines:
- Always cite which unit/section your answer comes from
- If the context doesn't contain the answer, say so
- Ask follow-up questions to check understanding
- Suggest related topics to explore"""

        # Build prompt
        prompt = f"""Retrieved Content:
{context_text}

Student Question: {query}

Provide a comprehensive answer based on the retrieved content. If generating a mindmap, use mermaid syntax."""

        # Generate response
        response = await gemini_service.generate_text(prompt, system_instruction)
        return response
    
    async def generate_streaming_response(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        session_context: Dict,
        course_name: str
    ):
        """Generate streaming response"""
        
        context_text = "\n\n".join([
            f"[Source: {chunk['metadata'].get('unit_name', 'Unknown')}]\n{chunk['content']}"
            for chunk in retrieved_chunks[:8]
        ])
        
        system_instruction = f"""You are an expert tutor for: {course_name}.
Current Unit: {session_context.get('current_unit_name', 'Not set')}
Teaching Mode: {session_context.get('teaching_mode', 'qa')}"""

        prompt = f"""Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"""

        async for chunk in gemini_service.generate_streaming(prompt, system_instruction):
            yield chunk

rag_service = RAGService()
