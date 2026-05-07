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

class FinancialResearchAgent(GenericResearchAgent):
    """
    Specialized research agent with MCP integration for financial data.
    """
    def __init__(self, provider: str = None, model: str = None):
        super().__init__(provider, model)
    
    async def perform_market_research(self, symbols: list = None) -> tuple[str, dict]:
        """
        Orchestrates research using MCP data connectors and returns a dual output:
        1. Human-readable Markdown trade journal.
        2. Machine-readable JSON target weights.
        """
        target_symbols = symbols or self.stocks
        
        system_prompt = """
        You are a senior quantitative researcher and macro strategist.
        Your goal is to analyze the provided financial data and news for the requested symbols.
        
        DUAL-OUTPUT REQUIREMENT:
        1. HUMAN-READABLE: Provide a 'Trade Journal' in Markdown format explaining your fundamental 
           and macroeconomic reasoning. Focus on why you are choosing these specific weights.
        2. MACHINE-READABLE: Provide a strict JSON object representing target portfolio weights.
           Format: {"weights": [{"ticker": "SYMBOL", "weight": PERCENTAGE_AS_FLOAT}, ...]}
           Ensure the total weight does not exceed 1.0 (100%).
        
        Respond with BOTH formats. Wrap the JSON in triple backticks with 'json' identifier.
        """
        
        user_prompt = f"Conduct research on {', '.join(target_symbols)} based on latest SEC filings, news, and market data."
        
        # In a real scenario, we would use MCP here to fetch data.
        # For this implementation, we simulate the data gathering via the LLM prompt.
        
        content = ""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model, max_tokens=2000, system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            content = response.content[0].text
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            )
            content = response.choices[0].message.content
        elif self.provider == "gemini":
            response = self.client.generate_content(f"{system_prompt}\n\n{user_prompt}")
            content = response.text
        else: # ollama
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            )
            content = response.message.content
            
        # Extract Markdown and JSON
        journal = content
        weights = {"weights": []}
        
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                weights = json.loads(json_str)
            elif "{" in content:
                # Fallback attempt if they didn't use backticks correctly
                json_str = content[content.find("{"):content.rfind("}")+1]
                weights = json.loads(json_str)
        except Exception as e:
            print(f"Failed to parse JSON weights: {e}")
            # Fallback: Equal weight for all requested symbols
            w = 1.0 / len(target_symbols)
            weights = {"weights": [{"ticker": s, "weight": w} for s in target_symbols]}
            
        return journal, weights
