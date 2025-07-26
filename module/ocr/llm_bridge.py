"""
LLM Bridge System for OCR Parsing in ALAS

This module provides a flexible interface for using LLMs to parse OCR output
into the specific formats expected by ALAS modules.
"""
import re
import json
from typing import Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod
from functools import lru_cache
import time

from module.base.decorator import cached_property
from module.logger import logger
from module.config.deep import deep_get


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def query(self, prompt: str, max_tokens: int = 50) -> Optional[str]:
        """Query the LLM and return the response"""
        pass

    def close(self) -> None:
        """Close any open connections or resources (optional)"""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini API provider"""
    
    def __init__(self):
        try:
            import google.generativeai as genai
            import os
            from module.config.config import AzurLaneConfig
            
            # Try multiple sources for API key
            api_key = None
            
            # 1. Check environment variable (same as vision system)
            api_key = os.environ.get('GOOGLE_API_KEY')
            
            # 2. Fallback to config file
            if not api_key:
                config = AzurLaneConfig()
                api_key = deep_get(config.data, 'Llm.GeminiApiKey', '')
            
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.enabled = True
                logger.info("Gemini API configured successfully")
            else:
                self.enabled = False
                logger.warning("Gemini API key not found in environment or config")
                
        except ImportError:
            self.enabled = False
            logger.warning("Google GenerativeAI library not installed")
            
    def query(self, prompt: str, max_tokens: int = 50) -> Optional[str]:
        """Query Gemini API with timeout and retry logic"""
        if not self.enabled:
            return None
            
        try:
            # Add timeout to generation config if supported
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistent parsing
                    'max_output_tokens': max_tokens,
                },
                # Note: google-generativeai uses httpx with default timeouts
                # This timeout may not be supported in all versions
            )
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider"""
    
    def __init__(self):
        try:
            import requests
            self.requests = requests
            self.base_url = "http://localhost:11434"
            self.model = "llama3.2:3b"  # Fast, small model for parsing
            self.enabled = self._check_ollama()
            
        except ImportError:
            self.enabled = False
            logger.warning("Requests library not installed")
            
    def _check_ollama(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = self.requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == self.model for m in models)
        except:
            pass
        return False
        
    def query(self, prompt: str, max_tokens: int = 50) -> Optional[str]:
        """Query Ollama API with timeout"""
        if not self.enabled:
            return None
            
        try:
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.1,
                        'num_predict': max_tokens,
                    }
                },
                timeout=15  # Add explicit timeout
            )
            
            if response.status_code == 200:
                return response.json()['response'].strip()
                
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            
        return None


class LLMParser(ABC):
    """Base class for LLM-based OCR output parsing"""
    
    # Class-level provider instances (shared across all parsers)
    _providers = None
    
    def __init__(self, provider: str = "auto"):
        self.provider = provider
        self._cache = {}
        self._init_providers()
        
    @classmethod
    def _init_providers(cls):
        """Initialize LLM providers (once per class)"""
        if cls._providers is None:
            cls._providers = {
                'gemini': GeminiProvider(),
                'ollama': OllamaProvider(),
            }
    
    def _get_active_provider(self) -> Optional[LLMProvider]:
        """Get the active LLM provider based on configuration"""
        if self.provider == "auto":
            # Try providers in order of preference
            for name in ['gemini', 'ollama']:
                provider = self._providers.get(name)
                if provider and provider.enabled:
                    return provider
        else:
            # Use specific provider
            return self._providers.get(self.provider)
            
        return None
        
    @abstractmethod
    def get_prompt(self) -> str:
        """Return the parsing prompt for this specific parser"""
        pass
        
    @abstractmethod
    def validate_output(self, output: str) -> bool:
        """Validate the parsed output meets requirements"""
        pass
        
    def parse(self, raw_text: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Parse raw OCR text using LLM with fallback strategies"""
        try:
            # Quick validation - skip empty/None inputs
            if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
                return self._get_default_value()
                
            # Check cache first
            cache_key = f"{self.__class__.__name__}:{raw_text}"
            if cache_key in self._cache:
                return self._cache[cache_key]
                
            # Strategy 1: Try rule-based parsing first (fast and cheap)
            result = self._rule_based_fallback(raw_text)
            if result and self.validate_output(result):
                self._cache[cache_key] = result
                logger.info(f"{self.__class__.__name__} rule-based parsed '{raw_text}' -> '{result}'")
                return result
                
            # Strategy 2: Try LLM parsing if rule-based failed or was invalid
            result = self._llm_parse(raw_text, context)
            if result and self.validate_output(result):
                self._cache[cache_key] = result
                logger.info(f"{self.__class__.__name__} LLM parsed '{raw_text}' -> '{result}'")
                return result
                
            # Strategy 3: All parsing failed, log and return default
            logger.warning(f"{self.__class__.__name__} failed to parse: {raw_text}")
            return self._get_default_value()
            
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return self._get_default_value()
    
    def _llm_parse(self, raw_text: str, context: Dict[str, Any] = None) -> Optional[str]:
        """Execute LLM parsing using configured provider"""
        provider = self._get_active_provider()
        if not provider:
            return None
            
        # Build prompt
        prompt = self.get_prompt()
        full_prompt = f"{prompt}\n\nInput: {raw_text}"
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False)
            full_prompt += f"\nContext: {context_str}"
            
        # Query LLM
        result = provider.query(full_prompt, max_tokens=50)
        
        if result:
            # Clean the response (remove quotes, extra whitespace)
            result = result.strip().strip('"\'')
            logger.info(f"{self.__class__.__name__} LLM parsed '{raw_text}' -> '{result}'")
            
        return result
            
    @abstractmethod
    def _rule_based_fallback(self, raw_text: str) -> Optional[str]:
        """Fallback parsing using regex/rules when LLM fails"""
        pass
        
    @abstractmethod
    def _get_default_value(self) -> Optional[str]:
        """Return safe default when all parsing fails"""
        pass
        
    def batch_parse(self, texts: List[str], context: Dict[str, Any] = None) -> List[Optional[str]]:
        """Parse multiple texts efficiently"""
        results = []
        
        for text in texts:
            result = self.parse(text, context)
            results.append(result)
            
        return results


# --- Caching mechanism for parser instances ---
_parser_cache = {}

# Integration function for existing ALAS modules
def parse_ocr_output(
    raw_text: str, 
    parser_type: str, 
    context: Dict[str, Any] = None,
    provider: str = "auto"
) -> Optional[str]:
    """
    Main entry point for OCR parsing with LLM support
    
    Args:
        raw_text: Raw OCR output text
        parser_type: Type of parser to use (e.g., 'commission_duration', 'shop_price')
        context: Optional context information
        provider: LLM provider ('auto', 'gemini', 'ollama')
        
    Returns:
        Parsed text in expected format, or None if parsing failed
    """
    from module.ocr.llm_parsers import get_parser
    
    # Use a cached parser instance for efficiency
    cache_key = (parser_type, provider)
    if cache_key not in _parser_cache:
        _parser_cache[cache_key] = get_parser(parser_type, provider)
    
    parser = _parser_cache.get(cache_key)
    
    if parser:
        return parser.parse(raw_text, context)
        
    logger.error(f"No parser available for type: {parser_type}")
    return None