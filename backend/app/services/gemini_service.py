from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from app.utils.logging_config import get_logger

load_dotenv()
logger = get_logger("gemini_service")

class GeminiService:
    def __init__(self):
        # Initialize the new google.genai client
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        self.model_name = 'gemini-2.5-flash'
        self.embedding_model = 'text-embedding-004'
        logger.info(f"GeminiService initialized with model: {self.model_name}")
    
    async def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """Generate text using Gemini 2.5 Flash"""
        try:
            logger.debug(f"Generating text with prompt length: {len(prompt)}")
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            ) if system_instruction else None
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            logger.debug(f"Generated response length: {len(response.text)}")
            return response.text
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def generate_streaming(self, prompt: str, system_instruction: str = None):
        """Generate text with streaming"""
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            ) if system_instruction else None
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"Error in streaming: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> list:
        """Generate embedding for text"""
        try:
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    async def classify_query_intent(self, query: str, context: dict) -> dict:
        """Classify user query intent"""
        prompt = f"""Analyze this user query and classify its intent.

Query: "{query}"

Current context: {context}

Classify into ONE of these intents:
1. teach_sequential - User wants to learn a topic step by step
2. explain_concept - User wants explanation of a specific concept
3. quiz - User wants practice questions or testing
4. mindmap - User wants a visual overview/mindmap
5. clarify - Follow-up question on previous topic

Also identify:
- target_units: Which units/sections are relevant (list)
- detail_level: high/medium/low

Respond ONLY with JSON:
{{"intent": "...", "target_units": [...], "detail_level": "..."}}"""

        response = await self.generate_text(prompt)
        import json
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            return json.loads(json_str)
        except:
            return {"intent": "explain_concept", "target_units": [], "detail_level": "medium"}

gemini_service = GeminiService()
