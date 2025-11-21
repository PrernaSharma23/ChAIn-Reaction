import os
import time
import random
from src.util.logger import log
from openai import OpenAI
from google import genai


class LLMService:
    def __init__(
        self,
        provider: str = "openai",         
        model: str = None,               
        retries: int = 1,
        backoff_factor: float = 2.0
    ):
        self.provider = provider.lower()
        self.retries = max(1, int(retries))
        self.backoff_factor = max(0.0, float(backoff_factor))

        if self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY", "")
            self.client = OpenAI(api_key=self.api_key) if self.api_key else None
            self.model = model or "gpt-4.1"

        elif self.provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY", "")
            self.client = genai.Client()
            self.model = model or "gemini-2.5-flash"

        else:
            raise ValueError("provider must be 'openai' or 'gemini'")

    def call(self, prompt: str) -> str:
        for attempt in range(1, self.retries + 1):
            try:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message["content"]

                elif self.provider == "gemini":
                    response = self.client.models.generate_content(
                            model=self.model, contents=prompt
                        )
        
                    return response.text

            except Exception as e:
                log.error(f"LLMService.call attempt {attempt} error: {e}")

                if attempt == self.retries:
                    log.error("LLMService.call exhausted retries")
                    raise

                sleep_for = self.backoff_factor * (2 ** (attempt - 1))
                sleep_for += random.uniform(0, 0.5)
                time.sleep(sleep_for)
