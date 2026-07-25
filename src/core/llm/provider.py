"""
Groq-First LLM Provider using httpx for async operations
Providers: Groq (primary) → Claude Haiku → Rule-based fallback
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    import httpx
except ImportError:
    httpx = None

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class LLMProvider:
    """
    Async LLM Provider with Groq-first strategy and automatic fallback.
    Supports:
    - Groq API (llama3-70b-8192, mixtral-8x7b-32768)
    - Claude Haiku API (Anthropic)
    - Rule-based fallback
    """
    
    def __init__(self):
        """Initialize LLM Provider with API keys and configuration"""
        # API Keys
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        
        # Groq configuration
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_models = {
            'primary': "llama3-70b-8192",
            'secondary': "mixtral-8x7b-32768"
        }
        
        # Anthropic configuration
        self.anthropic_url = "https://api.anthropic.com/v1/messages"
        self.anthropic_model = "claude-3-5-haiku-20241022"
        
        # HTTP client configuration
        self.timeout = 30.0
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
        
        # Rate limit tracking
        self._rate_limit_reset: Dict[str, datetime] = {
            'groq': None,
            'anthropic': None
        }
    
    async def complete(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        """
        Generate text completion using async LLM.
        
        Args:
            prompt: User prompt
            system: System prompt/instructions
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text or empty string on failure
        """
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        return await self.chat(messages, max_tokens)
    
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """
        Chat-based LLM call with provider fallback chain.
        Priority: Groq → Claude Haiku → Rule-based
        
        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response or empty string on failure
        """
        # Try Groq first
        response = await self._try_groq(messages, max_tokens)
        if response:
            return response
        
        # Try Claude Haiku
        response = await self._try_anthropic(messages, max_tokens)
        if response:
            return response
        
        # Rule-based fallback
        return self._rule_based_fallback(messages, max_tokens)
    
    async def _try_groq(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Try Groq provider with retry logic"""
        if not self.groq_api_key:
            logger.debug("Groq API key not configured")
            return ""
        
        # Check rate limit
        if self._rate_limit_reset.get('groq') and datetime.now() < self._rate_limit_reset['groq']:
            logger.debug("Groq rate limited, skipping")
            return ""
        
        # Try primary model
        response = await self._call_groq(messages, self.groq_models['primary'], max_tokens)
        if response:
            return response
        
        # Try secondary model
        response = await self._call_groq(messages, self.groq_models['secondary'], max_tokens)
        if response:
            return response
        
        return ""
    
    async def _call_groq(self, messages: List[Dict[str, str]], model: str, max_tokens: int) -> str:
        """Call Groq API with exponential backoff retry"""
        if not httpx:
            logger.error("httpx not installed. Install with: pip install httpx")
            return ""
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    payload = {
                        "model": model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": 0.3,
                        "top_p": 0.9
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    response = await client.post(
                        self.groq_url,
                        json=payload,
                        headers=headers
                    )
                    
                    # Handle rate limit
                    if response.status_code == 429:
                        reset_after = int(response.headers.get('retry-after', 60))
                        self._rate_limit_reset['groq'] = datetime.now() + timedelta(seconds=reset_after)
                        logger.debug(f"Groq rate limited, retry after {reset_after}s")
                        return ""
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            return result['choices'][0]['message']['content'].strip()
                    else:
                        logger.debug(f"Groq returned status {response.status_code}")
                        return ""
            
            except asyncio.TimeoutError:
                logger.debug(f"Groq call timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
            except Exception as e:
                logger.debug(f"Groq call error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
        
        return ""
    
    async def _try_anthropic(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Try Anthropic/Claude provider with retry logic"""
        if not self.anthropic_api_key:
            logger.debug("Anthropic API key not configured")
            return ""
        
        # Check rate limit
        if self._rate_limit_reset.get('anthropic') and datetime.now() < self._rate_limit_reset['anthropic']:
            logger.debug("Anthropic rate limited, skipping")
            return ""
        
        return await self._call_anthropic(messages, max_tokens)
    
    async def _call_anthropic(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Call Anthropic API with exponential backoff retry"""
        if not httpx:
            logger.error("httpx not installed. Install with: pip install httpx")
            return ""
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Convert messages to Anthropic format
                    # Extract system message if present
                    system_msg = ""
                    chat_messages = []
                    
                    for msg in messages:
                        if msg['role'] == 'system':
                            system_msg = msg['content']
                        else:
                            chat_messages.append({
                                "role": msg['role'],
                                "content": msg['content']
                            })
                    
                    payload = {
                        "model": self.anthropic_model,
                        "max_tokens": max_tokens,
                        "messages": chat_messages
                    }
                    
                    if system_msg:
                        payload["system"] = system_msg
                    
                    headers = {
                        "x-api-key": self.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    }
                    
                    response = await client.post(
                        self.anthropic_url,
                        json=payload,
                        headers=headers
                    )
                    
                    # Handle rate limit
                    if response.status_code == 429:
                        reset_after = int(response.headers.get('retry-after', 60))
                        self._rate_limit_reset['anthropic'] = datetime.now() + timedelta(seconds=reset_after)
                        logger.debug(f"Anthropic rate limited, retry after {reset_after}s")
                        return ""
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'content' in result and len(result['content']) > 0:
                            content = result['content'][0].get('text', '')
                            return content.strip()
                    else:
                        logger.debug(f"Anthropic returned status {response.status_code}")
                        return ""
            
            except asyncio.TimeoutError:
                logger.debug(f"Anthropic call timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
            except Exception as e:
                logger.debug(f"Anthropic call error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.base_delay * (2 ** attempt))
        
        return ""
    
    def _rule_based_fallback(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        """Rule-based fallback when all LLM providers fail"""
        # Extract the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg['role'] == 'user':
                user_message = msg['content'].lower()
                break
        
        # Basic rule-based responses for common patterns
        if 'risk' in user_message or 'danger' in user_message:
            return "Based on the blood report analysis, please consult with a healthcare professional for a detailed risk assessment."
        
        if 'recommendation' in user_message or 'advice' in user_message or 'suggest' in user_message:
            return "Recommendations depend on your individual health profile. Consult with a physician for personalized medical advice."
        
        if 'normal' in user_message or 'abnormal' in user_message:
            return "Parameter interpretation requires clinical context. Please discuss results with your healthcare provider."
        
        if 'treatment' in user_message or 'medication' in user_message:
            return "Treatment decisions should be made with guidance from qualified healthcare professionals."
        
        # Generic fallback
        return "Unable to process at this time. Please consult with a healthcare professional for medical guidance."
    
    def get_status(self) -> Dict[str, Any]:
        """Get provider availability status"""
        return {
            "groq_configured": bool(self.groq_api_key),
            "groq_models": self.groq_models,
            "anthropic_configured": bool(self.anthropic_api_key),
            "anthropic_model": self.anthropic_model,
            "httpx_available": httpx is not None,
            "groq_rate_limited": self._rate_limit_reset.get('groq') is not None,
            "anthropic_rate_limited": self._rate_limit_reset.get('anthropic') is not None
        }


# Global singleton instance
_provider_instance: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    """Get or create global LLM provider instance"""
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = LLMProvider()
    return _provider_instance


async def complete(prompt: str, system: str = "", max_tokens: int = 1000) -> str:
    """Convenience async function for text completion"""
    provider = get_provider()
    return await provider.complete(prompt, system, max_tokens)


async def chat(messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
    """Convenience async function for chat"""
    provider = get_provider()
    return await provider.chat(messages, max_tokens)


def get_status() -> Dict[str, Any]:
    """Get provider status"""
    provider = get_provider()
    return provider.get_status()
