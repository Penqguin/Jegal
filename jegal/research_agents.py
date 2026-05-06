import os
from anthropic import Anthropic

class GenericResearchAgent:
    """
    A generalized agent wrapper that can perform any financial research task
    based on the provided system prompt.
    """
    def __init__(self):
        # Credentials are retrieved at runtime from secure environment variables
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set in the environment.")
        self.client = Anthropic(api_key=self.api_key)

    async def execute_task(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Executes a task with a custom system and user prompt.
        """
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # Simplified parser logic: in production, use structured JSON output
        content = response.content[0].text
        print(f"Agent response: {content}")
        
        # Determine action from response (simple parsing logic)
        action = "HOLD"
        if "BUY" in content.upper(): action = "BUY"
        elif "SELL" in content.upper(): action = "SELL"
        
        return {"action": action, "symbol": "BTC-USD", "target": 75000.0}
