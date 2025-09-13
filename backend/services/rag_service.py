# Production-Ready RAG Service for KinAura Chatbot
# Implements vector embeddings, semantic search, and RAG pipeline

import os
import json
import hashlib
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# OpenAI for embeddings and chat
import openai
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Supabase for vector storage 
from supabase import create_client, Client

# Vector operations
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    id: str
    content: str
    title: str
    similarity: float
    metadata: Dict[str, Any]
    source: str

@dataclass
class RAGResponse:
    response: str
    sources: List[SearchResult]
    confidence: float
    session_id: str
    response_time: float

class VectorEmbeddingService:
    """Service for generating and managing vector embeddings"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.environ.get('OPENAI_API_KEY')
        )
        self.embedding_model = "text-embedding-3-large"  # High quality embeddings
        self.dimensions = 3072  # text-embedding-3-large dimensions
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        try:
            # Preprocess text
            clean_text = self._preprocess_text(text)
            
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=clean_text,
                encoding_format="float"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        try:
            # Preprocess all texts
            clean_texts = [self._preprocess_text(text) for text in texts]
            
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=clean_texts,
                encoding_format="float"
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for embedding"""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (8191 tokens max for OpenAI)
        max_chars = 32000  # Conservative estimate
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters")
        
        return text

class SupabaseVectorStore:
    """Supabase vector storage with pgvector"""
    
    def __init__(self):
        # Use existing supabase configuration
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        # For now, we'll use MongoDB as primary storage and add vector search later
        # This allows us to implement the RAG system without requiring Supabase setup
        self.use_mongodb_fallback = True
        
        if self.supabase_url and self.supabase_key:
            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                self.use_mongodb_fallback = False
                logger.info("Supabase vector store initialized")
            except Exception as e:
                logger.warning(f"Supabase initialization failed, using MongoDB fallback: {e}")
                self.use_mongodb_fallback = True
        else:
            logger.info("Supabase credentials not configured, using MongoDB for vector storage")
    
    async def initialize_schema(self):
        """Initialize vector database schema"""
        if self.use_mongodb_fallback:
            return  # MongoDB schema handled elsewhere
            
        try:
            # Enable pgvector extension
            await self.client.rpc('enable_vector_extension').execute()
            
            # Create embeddings table if not exists
            schema_sql = """
            CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                kb_item_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                embedding VECTOR(3072) NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create HNSW index for fast similarity search
            CREATE INDEX IF NOT EXISTS knowledge_embeddings_embedding_idx 
            ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops)
            WITH (m = 32, ef_construction = 100);
            
            -- Create index on kb_item_id for fast lookups
            CREATE INDEX IF NOT EXISTS knowledge_embeddings_kb_item_id_idx 
            ON knowledge_embeddings (kb_item_id);
            """
            
            await self.client.rpc('execute_sql', {'sql': schema_sql}).execute()
            logger.info("Vector database schema initialized")
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            self.use_mongodb_fallback = True
    
    async def store_knowledge_embedding(self, kb_item_id: str, title: str, 
                                      content: str, embedding: List[float],
                                      metadata: Dict[str, Any] = None) -> str:
        """Store knowledge base item embedding"""
        try:
            if self.use_mongodb_fallback:
                return await self._store_mongodb_embedding(kb_item_id, title, content, embedding, metadata)
            
            data = {
                'kb_item_id': kb_item_id,
                'title': title,
                'content': content,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            result = await self.client.table('knowledge_embeddings').insert(data).execute()
            
            if result.data:
                return result.data[0]['id']
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"Failed to store embedding: {e}")
            raise
    
    async def search_similar(self, query_embedding: List[float], limit: int = 8, 
                           threshold: float = 0.7, 
                           filter_metadata: Dict[str, Any] = None) -> List[SearchResult]:
        """Search for similar embeddings"""
        try:
            if self.use_mongodb_fallback:
                return await self._search_mongodb_fallback(query_embedding, limit, threshold, filter_metadata)
            
            # Use Supabase RPC function for vector search
            search_params = {
                'query_embedding': query_embedding,
                'similarity_threshold': threshold,
                'match_count': limit
            }
            
            if filter_metadata:
                search_params['filter_metadata'] = filter_metadata
            
            result = await self.client.rpc('search_knowledge_embeddings', search_params).execute()
            
            search_results = []
            for row in result.data:
                search_results.append(SearchResult(
                    id=row['id'],
                    content=row['content'],
                    title=row['title'],
                    similarity=row['similarity'],
                    metadata=row['metadata'] or {},
                    source=f"KB-{row['kb_item_id']}"
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _store_mongodb_embedding(self, kb_item_id: str, title: str, 
                                     content: str, embedding: List[float],
                                     metadata: Dict[str, Any] = None) -> str:
        """Fallback: Store embedding in MongoDB"""
        # Import MongoDB here to avoid circular imports
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        db_name = os.environ.get('DB_NAME', 'kinaura_db')
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        embedding_doc = {
            'id': f"embed_{kb_item_id}_{hashlib.md5(content.encode()).hexdigest()[:8]}",
            'kb_item_id': kb_item_id,
            'title': title,
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        await db.knowledge_embeddings.insert_one(embedding_doc)
        client.close()
        
        return embedding_doc['id']
    
    async def _search_mongodb_fallback(self, query_embedding: List[float], limit: int,
                                     threshold: float, filter_metadata: Dict[str, Any] = None) -> List[SearchResult]:
        """Fallback: Simple similarity search in MongoDB"""
        # Import MongoDB here
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ['MONGO_URL']
        db_name = os.environ.get('DB_NAME', 'kinaura_db')
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        try:
            # Get all embeddings (in production, this would be optimized)
            embeddings = await db.knowledge_embeddings.find({}).to_list(1000)
            
            # Calculate similarities
            results = []
            query_vector = np.array(query_embedding)
            
            for emb_doc in embeddings:
                try:
                    stored_vector = np.array(emb_doc['embedding'])
                    
                    # Cosine similarity
                    similarity = np.dot(query_vector, stored_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(stored_vector)
                    )
                    
                    if similarity >= threshold:
                        results.append(SearchResult(
                            id=emb_doc['id'],
                            content=emb_doc['content'],
                            title=emb_doc['title'],
                            similarity=float(similarity),
                            metadata=emb_doc.get('metadata', {}),
                            source=f"KB-{emb_doc['kb_item_id']}"
                        ))
                        
                except Exception as e:
                    logger.warning(f"Error calculating similarity for {emb_doc.get('id')}: {e}")
                    continue
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x.similarity, reverse=True)
            client.close()
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"MongoDB vector search failed: {e}")
            client.close()
            return []

class ProductionRAGService:
    """Production-ready RAG service for KinAura chatbot"""
    
    def __init__(self):
        self.embedding_service = VectorEmbeddingService()
        self.vector_store = SupabaseVectorStore()
        
        # Initialize LLM chat
        self.llm_chat = LlmChat(
            api_key=os.environ.get('OPENAI_API_KEY'),
            session_id="kinaura_rag_system",
            system_message=self._get_system_prompt()
        ).with_model("openai", "gpt-4o-mini")
        
        self.max_context_tokens = 16000  # GPT-4o-mini context limit
        self.response_timeout = 30  # seconds
        
    def _get_system_prompt(self) -> str:
        """Get the sophisticated system prompt for KinAura"""
        return """You are the KinAura AI Concierge, an expert in regenerative medicine and luxury wellness protocols. You provide personalized guidance based on KinAura's cutting-edge treatments and protocols.

CORE IDENTITY:
- Luxury medical concierge for KinAura Institute for Regenerative Wellness
- Expert in advanced treatments: Morpheus8, NAD+ IV Therapy, HBOT, Exosomes, Laser Therapies
- Sophisticated, professional, and medically accurate
- Always cite sources from knowledge base using [KB-ID] format

RESPONSE GUIDELINES:
1. Provide evidence-based medical information with KinAura treatment recommendations
2. Always include citations [KB-ID] when referencing knowledge base content
3. Maintain luxury medical tone - sophisticated but accessible
4. Include treatment benefits, protocols, and personalized recommendations
5. Always end with medical disclaimer when discussing treatments

KNOWLEDGE INTEGRATION:
- Use provided knowledge base context for accurate, up-to-date information
- If no relevant context found, provide general guidance and flag for admin review
- Prioritize KinAura-specific protocols and treatments
- Include pricing and availability when mentioned in knowledge base

MEDICAL COMPLIANCE:
- All responses must include: "This information does not replace medical consultation. KinAura protocols are validated by clinicians."
- Never provide specific medical diagnoses
- Focus on wellness optimization and treatment education
- Encourage consultation for personalized protocol development

LANGUAGES: Respond in English or Italian based on user input language."""

    async def initialize(self):
        """Initialize the RAG service"""
        await self.vector_store.initialize_schema()
        logger.info("RAG service initialized")
    
    async def process_knowledge_base_update(self, kb_item: Dict[str, Any]) -> bool:
        """Process knowledge base item for vector storage"""
        try:
            # Only process approved items
            if not kb_item.get('is_approved', False):
                return False
            
            # Generate embedding for the content
            content_text = f"{kb_item.get('title', '')} {kb_item.get('content', '')}"
            embedding = await self.embedding_service.generate_embedding(content_text)
            
            # Store in vector database
            await self.vector_store.store_knowledge_embedding(
                kb_item_id=kb_item['id'],
                title=kb_item.get('title', ''),
                content=kb_item.get('content', ''),
                embedding=embedding,
                metadata={
                    'category': kb_item.get('category', ''),
                    'tags': kb_item.get('tags', []),
                    'source_type': kb_item.get('source_type', ''),
                    'approved_by': kb_item.get('approved_by', ''),
                    'approval_date': kb_item.get('approval_date', ''),
                    'version': kb_item.get('version', 1)
                }
            )
            
            logger.info(f"Processed KB item for RAG: {kb_item['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process KB item {kb_item.get('id')}: {e}")
            return False
    
    async def search_knowledge_base(self, query: str, limit: int = 8) -> List[SearchResult]:
        """Search knowledge base using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Search similar content
            results = await self.vector_store.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                threshold=0.7  # Reasonable similarity threshold
            )
            
            # Re-rank by recency and relevance
            results = self._rerank_results(results, query)
            
            return results
            
        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            return []
    
    def _rerank_results(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Re-rank results by relevance and recency"""
        try:
            # Simple re-ranking by combining similarity with recency
            for result in results:
                recency_score = 1.0  # Default score
                
                # Boost more recent content
                if 'approval_date' in result.metadata:
                    try:
                        approval_date = datetime.fromisoformat(result.metadata['approval_date'])
                        days_old = (datetime.utcnow() - approval_date).days
                        recency_score = max(0.5, 1.0 - (days_old / 365))  # Decay over year
                    except:
                        pass
                
                # Combine similarity and recency
                result.similarity = (result.similarity * 0.8) + (recency_score * 0.2)
            
            # Sort by combined score
            results.sort(key=lambda x: x.similarity, reverse=True)
            return results
            
        except Exception as e:
            logger.warning(f"Re-ranking failed: {e}")
            return results
    
    async def generate_rag_response(self, user_message: str, session_id: str,
                                  language: str = "en") -> RAGResponse:
        """Generate RAG response with knowledge base context"""
        start_time = datetime.utcnow()
        
        try:
            # Search relevant knowledge
            search_results = await self.search_knowledge_base(user_message, limit=8)
            
            # Build context from search results
            context = self._build_context(search_results, language)
            
            # Create enhanced prompt with context
            rag_prompt = self._build_rag_prompt(user_message, context, search_results, language)
            
            # Generate response using LLM
            user_msg = UserMessage(text=rag_prompt)
            
            # Create new chat instance for this session
            session_chat = LlmChat(
                api_key=os.environ.get('OPENAI_API_KEY'),
                session_id=session_id,
                system_message=self._get_system_prompt()
            ).with_model("openai", "gpt-4o-mini")
            
            llm_response = await session_chat.send_message(user_msg)
            
            # Calculate confidence based on search results quality
            confidence = self._calculate_confidence(search_results, user_message)
            
            # Response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RAGResponse(
                response=str(llm_response),
                sources=search_results,
                confidence=confidence,
                session_id=session_id,
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"RAG response generation failed: {e}")
            
            # Fallback response
            fallback_response = self._get_fallback_response(user_message, language)
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return RAGResponse(
                response=fallback_response,
                sources=[],
                confidence=0.3,
                session_id=session_id,
                response_time=response_time
            )
    
    def _build_context(self, search_results: List[SearchResult], language: str) -> str:
        """Build context string from search results"""
        if not search_results:
            return "No specific KinAura knowledge base information found for this query."
        
        context_parts = []
        for result in search_results:
            context_entry = f"[{result.source}] {result.title}\n{result.content}"
            context_parts.append(context_entry)
        
        context = "\n\n".join(context_parts)
        
        # Truncate if too long
        max_context_chars = 12000
        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "\n\n[Context truncated for length...]"
        
        return context
    
    def _build_rag_prompt(self, user_message: str, context: str, 
                         search_results: List[SearchResult], language: str) -> str:
        """Build the complete RAG prompt"""
        
        # Language-specific instructions
        lang_instructions = {
            "en": "Respond in English with professional medical terminology.",
            "it": "Rispondi in italiano con terminologia medica professionale."
        }
        
        prompt = f"""Based on the following KinAura knowledge base information, provide a comprehensive response to the patient's question.

KNOWLEDGE BASE CONTEXT:
{context}

PATIENT QUESTION: {user_message}

INSTRUCTIONS:
- Use the knowledge base context to provide accurate, personalized recommendations
- Cite sources using [KB-ID] format when referencing specific information
- Focus on KinAura treatments and protocols mentioned in the context
- Include specific benefits, procedures, and protocols when available
- {lang_instructions.get(language, lang_instructions['en'])}
- Always end with the medical disclaimer
- If context is insufficient, acknowledge limitations and suggest consultation

Response should be detailed, professional, and specifically tailored to KinAura's luxury regenerative medicine approach."""

        return prompt
    
    def _calculate_confidence(self, search_results: List[SearchResult], user_message: str) -> float:
        """Calculate response confidence based on search quality"""
        if not search_results:
            return 0.3
        
        # Base confidence on top result similarity
        top_similarity = search_results[0].similarity if search_results else 0.0
        
        # Adjust based on number of good results
        good_results = sum(1 for r in search_results if r.similarity > 0.8)
        result_bonus = min(0.2, good_results * 0.05)
        
        # Query length bonus (longer queries often more specific)
        length_bonus = min(0.1, len(user_message.split()) * 0.01)
        
        confidence = min(0.95, top_similarity + result_bonus + length_bonus)
        return round(confidence, 2)
    
    def _get_fallback_response(self, user_message: str, language: str) -> str:
        """Get fallback response when KB search fails"""
        
        if language == "it":
            return """Grazie per la tua domanda. Al momento non ho informazioni specifiche nel database delle conoscenze di KinAura per rispondere in dettaglio. 

Ti consiglio di:
1. Contattare direttamente il nostro team medico per una consulenza personalizzata
2. Prenotare una valutazione iniziale per discutere i protocolli più adatti a te
3. Esplorare i nostri trattamenti principali come Morpheus8, terapia NAD+ IV e HBOT

Il nostro team di esperti può fornirti informazioni dettagliate sui protocolli di medicina rigenerativa più adatti alle tue esigenze specifiche.

Questa informazione non sostituisce la consultazione medica. I protocolli KinAura sono validati da clinici specializzati."""
        
        else:  # English
            return """Thank you for your question. I currently don't have specific information in the KinAura knowledge base to provide a detailed response.

I recommend:
1. Speaking directly with our medical team for personalized guidance
2. Booking an initial consultation to discuss the most suitable protocols for you  
3. Exploring our core treatments including Morpheus8, NAD+ IV Therapy, and HBOT

Our expert team can provide detailed information about regenerative medicine protocols tailored to your specific wellness goals.

This information does not replace medical consultation. KinAura protocols are validated by clinicians."""

# Global RAG service instance
rag_service = ProductionRAGService()