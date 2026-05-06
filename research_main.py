import asyncio
import jegal
from jegal.research_agents import FinancialResearchAgent
from jegal.engine_bridge import dispatch_agent_results

async def main():
    # 1. Init Rust Engine
    risk_manager = jegal.RiskManager(
        max_exposure_per_symbol=100000.0, 
        max_total_exposure=500000.0, 
        drawdown_limit=1000.0,
        max_orders_per_window=100,
        velocity_window_seconds=60
    )
    engine = jegal.ExecutionEngine(risk_manager)
    engine.set_broker("mock", {"balance": 100000.0})

    # 2. Run Anthropic Agent Research
    agent = FinancialResearchAgent()
    market_ideas = await agent.get_market_research(["BTC-USD", "ETH-USD"])
    
    # 3. Dispatch to Rust via zero-copy Arrow bridge
    dispatch_agent_results([market_ideas], engine)
    
    print("Strategy orchestration from Anthropic agents complete.")

if __name__ == "__main__":
    asyncio.run(main())
