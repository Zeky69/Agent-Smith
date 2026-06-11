import os, time, requests
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    retries: int = 0

class LLMClient:
    def __init__(self, base_url: str, model: str, api_key: str | None = None,
                 max_retries: int = 5):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.api_key = api_key or os.environ["OPENROUTER_API_KEY"]
        self.max_retries = max_retries

    def chat(self, messages: list[dict], stop: list[str] | None = None,
             max_tokens: int = 1024) -> LLMResponse:
        t0 = time.time()
        retries = 0
        delay = 10.0
        while True:
            r = requests.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages,
                      "stop": stop, "max_tokens": max_tokens, "temperature": 0.2},
                timeout=120,
            )
            if r.status_code == 429 and retries < self.max_retries:
                try:
                    retry_after = max(float(r.headers["Retry-After"]), 10.0)
                except (KeyError, ValueError):
                    retry_after = delay
                print(f"[llm] 429 rate-limited (attempt {retries+1}/{self.max_retries}), "
                      f"body={r.text[:200]!r}, waiting {retry_after:.0f}s")
                time.sleep(retry_after)
                retries += 1
                delay = min(delay * 2, 120.0)
                continue
            if r.status_code == 429:
                raise RuntimeError(
                    f"Rate limit not cleared after {self.max_retries} retries. "
                    f"Response: {r.text[:400]}"
                )
            r.raise_for_status()
            break

        d = r.json()
        return LLMResponse(
            text=d["choices"][0]["message"]["content"] or "",
            input_tokens=d["usage"]["prompt_tokens"],
            output_tokens=d["usage"]["completion_tokens"],
            latency_ms=(time.time() - t0) * 1000,
            retries=retries,
        )