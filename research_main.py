import asyncio
import jegal
import pandas as pd
import os
import json
from dotenv import load_dotenv
from jegal.research_agents import FinancialResearchAgent, EarningsReviewerAgent
from jegal.engine_bridge import write_target_weights

# Load environment variables from .env file
load_dotenv()

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

    # 2. Load Portfolio Universe from Config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    active_sectors = [s for s, active in config.get("sectors", {}).items() if active]
    
    # Flatten manual and dynamic watchlist
    portfolio_universe = []
    portfolio_universe.extend(config.get("manual_watchlist", []))
    portfolio_universe.extend(config.get("dynamic_watchlist", []))
    
    # Get current positions from Rust Broker
    print("Research Pipeline: Fetching current portfolio state from broker...")
    # Note: engine doesn't have a direct get_positions yet in the Python bridge, 
    # but we can simulate or add it. For now, we'll try to call it if it exists.
    try:
        current_portfolio = engine.get_positions() # This needs to be exposed in lib.rs
    except:
        current_portfolio = {}
    
    print(f"Research Pipeline: Starting deep analysis for {len(portfolio_universe)} tickers in {active_sectors}...")

    # 3. Parallel Research
    agent = FinancialResearchAgent()
    earnings_agent = EarningsReviewerAgent()
    
    # Perform general research and get weights
    journal, weights_json = await agent.perform_market_research(
        symbols=portfolio_universe, 
        active_sectors=active_sectors,
        current_portfolio=current_portfolio
    )
    
    # Supplement with earnings reviews for top tickers (simulated)
    for ticker in portfolio_universe[:3]:
        review = await earnings_agent.review_earnings(ticker)
        journal += f"\n\n### Earnings Review: {ticker}\n{review}"
    
    # 4. Save Research Output
    os.makedirs("logs", exist_ok=True)
    with open("logs/research_report.md", "w") as f:
        f.write(journal)
    print(f"Research Pipeline: Report saved to logs/research_report.md")

    # 5. Dispatch Target Weights via Arrow IPC
    df = pd.DataFrame(weights_json["weights"])
    if 'ticker' not in df.columns and 'symbol' in df.columns:
        df = df.rename(columns={'symbol': 'ticker'})
    
    ipc_path = "/tmp/jegal_target_weights.arrow"
    write_target_weights(df, ipc_path)
    
    # 6. Trigger Rust Rebalancing
    print("Research Pipeline: Triggering Rust Rebalancer...")
    engine.run_rebalancing(ipc_path, tolerance=0.05)
    
    print("Research Pipeline: Cycle complete.")

if __name__ == "__main__":
    asyncio.run(main())
