"""
OpenRouter API Generator for SINEMA Chatbot
Uses OpenRouter API (OpenAI-compatible) instead of local model

Features:
- Multiple API key rotation: automatically switches to next key on rate limit
- Supports OPENROUTER_API_KEYS (comma-separated) with fallback to OPENROUTER_API_KEY
"""

import os
import time
from typing import Tuple, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class APIGenerator:
    """Generator that uses OpenRouter API for LLM responses with key rotation"""
    
    # User-friendly error messages in Indonesian
    ERROR_MESSAGES = {
        'rate_limit': """⚠️ **Batas penggunaan harian tercapai**

Maaf, limit API gratis (50 request/hari) sudah habis. 
Silakan coba lagi besok atau hubungi admin untuk upgrade akun.

💡 **Tips:** Limit akan reset setiap hari pada pukul 00:00 UTC.""",
        
        'all_keys_exhausted': """⚠️ **Semua API key sudah mencapai batas limit**

Seluruh API key yang tersedia telah mencapai batas penggunaan harian.
Silakan coba lagi besok atau hubungi admin.

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
        self.model = os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini-2024-07-18')
        
        # Load API keys: prefer multi-key, fallback to single key
        keys_str = os.getenv('OPENROUTER_API_KEYS', '')
        if keys_str:
            self.api_keys: List[str] = [k.strip() for k in keys_str.split(',') if k.strip()]
        else:
            single_key = os.getenv('OPENROUTER_API_KEY', '')
            self.api_keys = [single_key] if single_key else []
        
        if not self.api_keys:
            raise ValueError("No API keys found. Set OPENROUTER_API_KEYS or OPENROUTER_API_KEY in .env")
        
        self.current_key_index = 0
        self.exhausted_keys = set()  # Track which keys are rate-limited
        
        # Initialize client with first key
        self._init_client()
        
        print(f"✅ OpenRouter API initialized with {len(self.api_keys)} key(s), model: {self.model}")
    
    def _init_client(self):
        """Initialize/reinitialize OpenAI client with current key"""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_keys[self.current_key_index],
        )
    
    def _rotate_key(self) -> bool:
        """
        Switch to the next available API key.
        Returns True if a new key is available, False if all keys are exhausted.
        """
        self.exhausted_keys.add(self.current_key_index)
        
        # Find next non-exhausted key
        for i in range(len(self.api_keys)):
            candidate = (self.current_key_index + 1 + i) % len(self.api_keys)
            if candidate not in self.exhausted_keys:
                self.current_key_index = candidate
                self._init_client()
                key_preview = self.api_keys[candidate][-8:]
                print(f"🔄 Switched to API key #{candidate + 1} (…{key_preview})")
                return True
        
        print("❌ All API keys exhausted!")
        return False
    
    def _parse_error(self, error: Exception) -> Tuple[str, str]:
        """
        Parse API error and return (error_type, user_message)
        """
        error_str = str(error).lower()
        
        # Check for rate limit (429)
        if '429' in error_str or 'rate limit' in error_str:
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
        Generate a response using OpenRouter API with automatic key rotation.
        
        Args:
            query: Current user question
            context: RAG context from retrieved documents
            system_prompt: System instructions
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        
        Returns:
            Tuple of (response_text, latency_seconds)
        """
        start = time.time()
        
        # Check if all keys are exhausted
        if len(self.exhausted_keys) >= len(self.api_keys):
            return self.ERROR_MESSAGES['all_keys_exhausted'], 0.0
        
        # Build the prompt
        if context:
            user_message = f"""KONTEKS DOKUMEN (SUMBER TUNGGAL KEBENARAN):
{context}

PERTANYAAN: {query}

INSTRUKSI JAWABAN (WAJIB DIPATUHI - PELANGGARAN AKAN DIPERIKSA):
1. Jawab HANYA berdasarkan KONTEKS di atas - DILARANG KERAS gunakan pengetahuan luar/pribadi
2. JANGAN mengarang informasi yang tidak ada di konteks - ini FATAL ERROR
3. Jika informasi tidak lengkap atau tidak ada di konteks, katakan: "Maaf, informasi ini tidak tersedia dalam dokumen"
4. Gunakan ANGKA PERSIS seperti tertulis di konteks (misal: "2,00" bukan "2")
5. JANGAN menambahkan detail yang tidak disebutkan di konteks
6. JAWABAN TIDAK BOLEH mengandung informasi di luar konteks di atas

INGAT: Konteks di atas adalah SATU-SATUNYA sumber kebenaran. JANGAN gunakan pengetahuan umum atau asumsi pribadi."""
        else:
            user_message = f"""PERTANYAAN: {query}

JAWABAN: Maaf, saya tidak memiliki akses ke dokumen untuk menjawab pertanyaan ini. Silakan hubungi admin atau cek dokumentasi resmi."""
        
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
        
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4096,  # Increased for longer responses
                    temperature=float(os.getenv('TEMPERATURE', '0.2')),  # Lowered to reduce hallucination
                )
                
                result = response.choices[0].message.content
                
                # Handle empty or None response
                if not result or not result.strip():
                    if attempt < max_retries:
                        print(f"⚠️ Empty response (attempt {attempt + 1}/{max_retries + 1}), retrying...")
                        time.sleep(0.5)  # Brief pause before retry
                        continue
                    else:
                        print("⚠️ Warning: Empty response after all retries")
                        latency = time.time() - start
                        return "Maaf, tidak ada respons dari sistem. Silakan coba lagi.", latency
                
                latency = time.time() - start
                return result.strip(), latency
                
            except Exception as e:
                error_type, user_msg = self._parse_error(e)
                
                # Rate limit → try rotating to next key
                if error_type == 'rate_limit':
                    key_num = self.current_key_index + 1
                    print(f"⚠️ Key #{key_num} rate limited, attempting rotation...")
                    
                    if self._rotate_key():
                        # Successfully switched key — retry immediately (don't count as attempt)
                        print(f"🔄 Retrying with new key...")
                        time.sleep(0.3)
                        # Recursive call with new key
                        return self.generate(query, context, system_prompt, conversation_history)
                    else:
                        # All keys exhausted
                        latency = time.time() - start
                        return self.ERROR_MESSAGES['all_keys_exhausted'], latency
                
                # Other errors: retry or return
                if attempt < max_retries:
                    print(f"⚠️ API Error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}, retrying...")
                    time.sleep(0.5)
                    continue
                
                latency = time.time() - start
                print(f"⚠️ API Error [{error_type}]: {str(e)}")
                return user_msg, latency
        
        # Fallback (should not reach here)
        latency = time.time() - start
        return "Maaf, terjadi kesalahan. Silakan coba lagi.", latency
    
    def is_loaded(self) -> bool:
        """Check if API is configured"""
        return len(self.api_keys) > 0
    
    def reset_rate_limit(self):
        """Reset rate limit flags for all keys (call when day changes)"""
        self.exhausted_keys.clear()
        self.current_key_index = 0
        self._init_client()
        print("🔄 All API keys reset")
    
    def get_status(self) -> dict:
        """Get current key rotation status"""
        return {
            "total_keys": len(self.api_keys),
            "current_key": self.current_key_index + 1,
            "exhausted_keys": len(self.exhausted_keys),
            "available_keys": len(self.api_keys) - len(self.exhausted_keys),
        }
