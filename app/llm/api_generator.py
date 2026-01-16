"""
OpenRouter API Generator for SINEMA Chatbot
Uses OpenRouter API (OpenAI-compatible) instead of local model
"""

import os
import time
from typing import Tuple
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class APIGenerator:
    """Generator that uses OpenRouter API for LLM responses"""
    
    # User-friendly error messages in Indonesian
    ERROR_MESSAGES = {
        'rate_limit': """⚠️ **Batas penggunaan harian tercapai**

Maaf, limit API gratis (50 request/hari) sudah habis. 
Silakan coba lagi besok atau hubungi admin untuk upgrade akun.

💡 **Tips:** Limit akan reset setiap hari pada pukul 00:00 UTC.""",
        
        'auth_error': """🔐 **Masalah autentikasi API**

API key tidak valid atau expired. Silakan hubungi admin untuk memperbaiki konfigurasi.""",
        
        'timeout': """⏱️ **Server timeout**

Server sedang sibuk. Silakan coba lagi dalam beberapa saat.""",
        
        'server_error': """🔧 **Server sedang maintenance**

Layanan AI sedang dalam perbaikan. Silakan coba lagi nanti.""",
        
        'generic': """❌ **Terjadi kesalahan**

Maaf, terjadi masalah saat memproses pertanyaan Anda. Silakan coba lagi."""
    }
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini-2024-07-18')
        self.rate_limited = False  # Track rate limit status
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        print(f"✅ OpenRouter API initialized with model: {self.model}")
    
    def _parse_error(self, error: Exception) -> Tuple[str, str]:
        """
        Parse API error and return (error_type, user_message)
        """
        error_str = str(error).lower()
        
        # Check for rate limit (429)
        if '429' in error_str or 'rate limit' in error_str:
            self.rate_limited = True
            return 'rate_limit', self.ERROR_MESSAGES['rate_limit']
        
        # Check for authentication errors (401, 403)
        if '401' in error_str or '403' in error_str or 'unauthorized' in error_str:
            return 'auth_error', self.ERROR_MESSAGES['auth_error']
        
        # Check for timeout
        if 'timeout' in error_str or 'timed out' in error_str:
            return 'timeout', self.ERROR_MESSAGES['timeout']
        
        # Check for server errors (500, 502, 503)
        if any(code in error_str for code in ['500', '502', '503', '504']):
            return 'server_error', self.ERROR_MESSAGES['server_error']
        
        # Generic error
        return 'generic', self.ERROR_MESSAGES['generic']
    
    def generate(
        self,
        query: str,
        context: str = "",
        system_prompt: str = "",
        conversation_history: list = None
    ) -> Tuple[str, float]:
        """
        Generate a response using OpenRouter API.
        
        Args:
            query: Current user question
            context: RAG context from retrieved documents
            system_prompt: System instructions
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            Tuple of (response_text, latency_seconds)
        """
        start = time.time()
        
        # Check if we're already rate limited
        if self.rate_limited:
            return self.ERROR_MESSAGES['rate_limit'], 0.0
        
        # Build the prompt
        if context:
            user_message = f"""KONTEKS:
{context}

PERTANYAAN: {query}

Jawab berdasarkan konteks di atas."""
        else:
            user_message = query
        
        # Build messages array
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 6 messages for context window management)
        if conversation_history:
            # Limit to last 6 messages (3 exchanges) to avoid token limit
            recent_history = conversation_history[-6:]
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
            )
            
            latency = time.time() - start
            result = response.choices[0].message.content.strip()
            
            return result, latency
            
        except Exception as e:
            latency = time.time() - start
            error_type, user_message = self._parse_error(e)
            print(f"⚠️ API Error [{error_type}]: {str(e)}")
            return user_message, latency
    
    def is_loaded(self) -> bool:
        """Check if API is configured"""
        return self.api_key is not None
    
    def reset_rate_limit(self):
        """Reset rate limit flag (call when day changes)"""
        self.rate_limited = False

