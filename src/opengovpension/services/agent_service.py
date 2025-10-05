"""AI agent service for OpenPension."""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx
import structlog
from openai import AsyncOpenAI

from ..core.config import get_settings

logger = structlog.get_logger(__name__)


class AgentService:
    """Service for managing AI agents and analysis."""

    def __init__(self):
        """Initialize agent service."""
        self.settings = get_settings()
        self.openai_client = None
        if self.settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def run_analysis(
        self,
        prompt: str,
        model: str = "gpt-4",
        provider: str = "openai"
    ) -> Dict[str, Any]:
        """Run AI analysis."""
        try:
            if provider == "openai" and self.openai_client:
                return await self._run_openai_analysis(prompt, model)
            elif provider == "ollama":
                return await self._run_ollama_analysis(prompt, model)
            else:
                return await self._run_mock_analysis(prompt)
        except Exception as e:
            logger.error("Analysis failed", error=str(e))
            raise

    async def _run_openai_analysis(self, prompt: str, model: str) -> Dict[str, Any]:
        """Run analysis using OpenAI."""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")

        system_prompt = """You are an expert pension benefits administrator analyzing retirement accounts and benefit calculations. Provide detailed benefit analysis, eligibility assessment, calculation verification, and compliance guidance."""

        try:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return {"analysis": result_text, "provider": "openai", "model": model}

        except Exception as e:
            logger.error("OpenAI analysis failed", error=str(e))
            return await self._run_mock_analysis(prompt)

    async def _run_ollama_analysis(self, prompt: str, model: str) -> Dict[str, Any]:
        """Run analysis using Ollama."""
        try:
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    try:
                        return json.loads(result.get("response", "{}"))
                    except json.JSONDecodeError:
                        return {
                            "analysis": result.get("response", ""),
                            "provider": "ollama",
                            "model": model
                        }
                else:
                    raise Exception(f"Ollama API error: {response.status_code}")

        except Exception as e:
            logger.error("Ollama analysis failed", error=str(e))
            return await self._run_mock_analysis(prompt)

    async def _run_mock_analysis(self, prompt: str) -> Dict[str, Any]:
        """Run mock analysis for testing."""
        return {
            "analysis": "Mock analysis result",
            "confidence": 0.85,
            "provider": "mock",
            "model": "mock-analysis"
        }

    async def chat(self, message: str) -> str:
        """Interactive chat with AI agent."""
        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful pension benefits assistant specializing in public employee retirement systems and regulatory compliance."}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            else:
                return "AI chat is not available. Please set up OpenAI API key or Ollama."
        except Exception as e:
            return f"Chat error: {str(e)}"