from openai import OpenAI
import os
import time
import random
from src.util.logger import log


class LLMService:
    def __init__(self, retries: int = 2, backoff_factor: float = 1.0):
        self.api_key =  os.getenv("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.retries = max(1, int(retries))
        self.backoff_factor = max(0.0, float(backoff_factor))

    def call(self, prompt: str) -> str:
        for attempt in range(1, self.retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message["content"]
            except Exception as e:
                log.error(f"LLMService.call attempt {attempt} error: {e}")
                if attempt == self.retries:
                    log.error("LLMService.call exhausted retries")
                    raise
                sleep_for = self.backoff_factor * (2 ** (attempt - 1))
                sleep_for += random.uniform(0, 0.5)
                time.sleep(sleep_for)