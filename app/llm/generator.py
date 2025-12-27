# -*- coding: utf-8 -*-
"""LLM Generator - SPEED OPTIMIZED VERSION"""
import time
from pathlib import Path
from typing import Tuple
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

class LLMGenerator:
    """Generate responses using local LLM with RAG context - Speed optimized"""
    
    def __init__(
        self,
        model_path: Path,
        device: str = "cuda",
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        use_4bit: bool = True  # Enable 4-bit quantization for speed
    ):
        self.model_path = Path(model_path)
        self.device = device if torch.cuda.is_available() else "cpu"
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.use_4bit = use_4bit and self.device == "cuda"
        
        self._model = None
        self._tokenizer = None
    
    def _load_model(self):
        """Lazy load the model with optimizations"""
        if self._model is not None:
            return
        
        print(f"Loading LLM from {self.model_path}...")
        start = time.time()
        
        self._tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_path),
            trust_remote_code=True
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        
        # Configure quantization for faster inference (Linux only, bitsandbytes doesn't work on Windows)
        import platform
        if self.use_4bit and platform.system() != "Windows":
            try:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                self._model = AutoModelForCausalLM.from_pretrained(
                    str(self.model_path),
                    quantization_config=quantization_config,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                print("Loaded with 4-bit quantization")
            except Exception as e:
                print(f"4-bit loading failed ({e}), falling back to float16")
                self.use_4bit = False
        else:
            self.use_4bit = False
            if platform.system() == "Windows":
                print("Windows detected - using float16 mode (bitsandbytes not supported)")
        
        if not self.use_4bit:
            self._model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
        
        self._model.eval()
        
        # Note: torch.compile disabled - causes issues on Windows and first inference is slower
        print(f"LLM loaded in {time.time() - start:.1f}s on {self.device.upper()}")
    
    @property
    def model(self):
        self._load_model()
        return self._model
    
    @property
    def tokenizer(self):
        self._load_model()
        return self._tokenizer
    
    def generate(
        self,
        query: str,
        context: str = "",
        system_prompt: str = ""
    ) -> Tuple[str, float]:
        """
        Generate a response using the LLM with optional RAG context.
        SPEED OPTIMIZED with greedy decoding.
        
        Returns:
            Tuple of (response_text, latency_seconds)
        """
        # Allow maximum context for detailed responses
        max_context_len = 8000
        if len(context) > max_context_len:
            context = context[:max_context_len] + "..."
        
        # Build prompt with context - Strict context adherence
        if context:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>
KONTEKS:
{context}

PERTANYAAN: {query}

Jawab singkat berdasarkan konteks.<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        else:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>
{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        
        # Tokenize with larger context window
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096).to(self.model.device)
        
        # Generate with balanced parameters for quality AND length
        start = time.time()
        with torch.no_grad():
            with torch.cuda.amp.autocast(enabled=self.device == "cuda"):
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    min_new_tokens=100,  # Force minimum output length
                    do_sample=True,  # Enable sampling for better quality
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.15,  # Prevent repetition
                    num_beams=1,
                    use_cache=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
        latency = time.time() - start
        
        # Decode only the new tokens (excluding prompt)
        new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        # Clean up response
        response = response.strip()
        
        # Remove any leftover tags
        for tag in ['<|eot_id|>', '<|end_header_id|>', '<|start_header_id|>']:
            response = response.replace(tag, '')
        
        return response.strip(), latency
    
    def is_loaded(self) -> bool:
        """Check if the model is loaded"""
        return self._model is not None
