import os
import ollama
import json
import yfinance as yf
from ddgs import DDGS
from anthropic import Anthropic
from openai import OpenAI
from google import genai

class GenericResearchAgent:
    """
    A generalized agent wrapper supporting OpenAI, Anthropic, Gemini, and Ollama.
    """
    def __init__(self, provider: str = None, model: str = None):
        # Load config to get LLM settings
        try:
            with open("config.json", "r") as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {}

        llm_cfg = self.config.get("llm", {})
        self.provider = (provider or llm_cfg.get("provider") or os.environ.get("LLM_PROVIDER", "ollama")).lower()
        self.model = model or llm_cfg.get("model") or os.environ.get("LLM_MODEL", "llama3")
        
        # Load stock configuration
        self.stocks = self.config.get("manual_watchlist")
        
        if self.provider == "anthropic":
            self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        elif self.provider == "openai":
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        elif self.provider == "gemini":
            self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        elif self.provider == "ollama":
            self.client = ollama
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def execute_task(self, system_prompt: str, user_prompt: str, symbols: list = None) -> dict:
        """
        Executes a task with a custom system and user prompt, focusing on the provided symbols.
        """
        target_symbols = symbols or self.stocks
        
        # If we have specific symbols, try to get fresh news for them via yfinance
        news_context = ""
        if symbols:
            for s in symbols:
                try:
                    ticker = yf.Ticker(s)
                    news = ticker.news[:3] # Get top 3 news items
                    for n in news:
                        news_context += f"\n[{s}] {n['title']}"
                except:
                    pass

        full_user_prompt = f"Focusing on the following stocks/assets: {', '.join(target_symbols)}.\n"
        if news_context:
            full_user_prompt += f"Recent News Context: {news_context}\n"
        full_user_prompt += f"\n{user_prompt}"

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
            response = self.client.models.generate_content(
                model=self.model, 
                contents=f"{system_prompt}\n\n{full_user_prompt}"
            )
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
    
    async def perform_market_research(self, symbols: list = None, active_sectors: list = None, current_portfolio: dict = None) -> tuple[str, dict]:
        """
        Orchestrates research focusing on active sectors and existing portfolio context.
        """
        target_symbols = symbols or self.stocks
        sectors_str = ", ".join(active_sectors) if active_sectors else "All"
        portfolio_str = json.dumps(current_portfolio) if current_portfolio else "Empty"
        
        system_prompt = f"""
        You are a senior quantitative researcher and macro strategist.
        ACTIVE SECTORS: {sectors_str}
        CURRENT PORTFOLIO: {portfolio_str}
        
        Your goal is to analyze the provided symbols AND suggest new ones within the ACTIVE SECTORS 
        if they offer better risk-adjusted returns or fit the current portfolio better.
        
        DUAL-OUTPUT REQUIREMENT:
        1. HUMAN-READABLE: Provide a 'Trade Journal' in Markdown format explaining your reasoning. 
        2. MACHINE-READABLE: Provide a strict JSON object representing target portfolio weights.
           Format: {{"weights": [{{"ticker": "SYMBOL", "weight": PERCENTAGE_AS_FLOAT}}, ...]}}
           Ensure the total weight does not exceed 1.0 (100%).
        
        Respond with BOTH formats. Wrap the JSON in triple backticks with 'json' identifier.
        """
        
        user_prompt = f"Conduct research on {', '.join(target_symbols)} and identify high-alpha opportunities in {sectors_str} based on latest SEC filings, news, and market data."
        
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
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"{system_prompt}\n\n{user_prompt}"
            )
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


class NewsScannerAgent(GenericResearchAgent):
    """
    Agent focused on scanning news for new catalysts using free sources (DuckDuckGo & YFinance).
    """
    async def scan_for_catalysts(self, active_sectors: list = None) -> list:
        """
        Fetches live news from free sources and uses the LLM to identify tickers and catalysts.
        """
        print(f"NewsScannerAgent: Fetching live news for {active_sectors} via DuckDuckGo...")
        
        all_headlines = []
        
        # 1. Fetch Global Headlines via DuckDuckGo
        try:
            with DDGS() as ddgs:
                for sector in active_sectors:
                    query = f"latest {sector} stock market news catalysts"
                    results = list(ddgs.news(query, max_results=5))
                    for r in results:
                        all_headlines.append(f"[{sector}] {r['title']}: {r['body']}")
        except Exception as e:
            print(f"NewsScannerAgent: DuckDuckGo error: {e}")
            # Fallback headlines for testing
            all_headlines = [
                "Intel (INTC) to shift chip strategy, focusing on mid-tier AI demand.",
                "Nvidia (NVDA) announces new H200 production ramp-up.",
                "Bitcoin (BTC) breaks all-time high amid spot ETF inflows."
            ]
        
        context_str = "\n".join(all_headlines)
        sectors_str = ", ".join(active_sectors) if active_sectors else "any"
        
        # 2. Use LLM to extract actionable data from the live headlines
        system_prompt = f"""
        You are a Financial News Analyst. Given these LIVE HEADLINES:
        {context_str}
        
        Identify companies with significant news catalysts in these sectors: {sectors_str}.
        
        OUTPUT REQUIREMENT:
        Provide a JSON list of tickers and their likely sector.
        Format: {{"catalysts": [{{"ticker": "SYMBOL", "sector": "tech|health|metals|crypto|other", "reason": "SHORT_DESCRIPTION"}}]}}
        """
        user_prompt = f"Extract tickers and catalysts for {sectors_str} from the headlines."
        
        content = ""
        if self.provider == "ollama":
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            )
            content = response.message.content
        else:
            return []

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str).get("catalysts", [])
            elif "{" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                return json.loads(json_str).get("catalysts", [])
        except:
            return []
        return []

class EarningsReviewerAgent(GenericResearchAgent):
    """
    Agent focused on deep fundamental analysis of earnings reports.
    """
    async def review_earnings(self, ticker: str) -> str:
        system_prompt = f"Analyze the latest earnings report and financial health of {ticker}. Provide a summary and a conviction score (1-10)."
        user_prompt = f"Focus on revenue growth, guidance, and margin trends for {ticker}."
        
        result = await self.execute_task(system_prompt, user_prompt, symbols=[ticker])
        return result.get("research_summary", "No research found.")
