import os
import ollama
import json
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai

class GenericResearchAgent:
    """
    A generalized agent wrapper supporting OpenAI, Anthropic, Gemini, and Ollama.
    """
    def __init__(self, provider: str = None, model: str = None):
        self.provider = (provider or os.environ.get("LLM_PROVIDER", "ollama")).lower()
        self.model = model or os.environ.get("LLM_MODEL", "llama3")
        
        # Load stock configuration
        try:
            with open("config.json", "r") as f:
                self.stocks = json.load(f).get("stocks", ["BTC-USD"])
        except FileNotFoundError:
            self.stocks = ["BTC-USD"]
        
        if self.provider == "anthropic":
            self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        elif self.provider == "openai":
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif self.provider == "gemini":
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "ollama":
            self.client = ollama
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def execute_task(self, system_prompt: str, user_prompt: str, symbols: list = None) -> dict:
        """
        Executes a task with a custom system and user prompt, focusing on the provided symbols.
        """
        target_symbols = symbols or self.stocks
        full_user_prompt = f"Focusing on the following stocks/assets: {', '.join(target_symbols)}.\n\n{user_prompt}"

        content = ""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model, max_tokens=1000, system=system_prompt,
                messages=[{"role": "user", "content": full_user_prompt}]
            )
            content = response.content[0].text
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_user_prompt}]
            )
            content = response.choices[0].message.content
        elif self.provider == "gemini":
            response = self.client.generate_content(f"{system_prompt}\n\n{full_user_prompt}")
            content = response.text
        else: # ollama
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_user_prompt}]
            )
            content = response.message.content
        
        print(f"Agent ({self.provider}) response for {target_symbols}: {content}")
        
        action = "BUY" if "BUY" in content.upper() else "SELL" if "SELL" in content.upper() else "HOLD"
        # Return the research data mapped to the requested symbols
        return {"action": action, "symbols": target_symbols, "research_summary": content}
