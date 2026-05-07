import asyncio
import jegal
import pandas as pd
import os
from jegal.research_agents import FinancialResearchAgent
from jegal.engine_bridge import write_target_weights

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

    # 2. Run Financial Research Agent
    print("Starting AI Financial Research...")
    agent = FinancialResearchAgent()
    journal, weights_json = await agent.perform_market_research(["BTC-USD", "ETH-USD", "AAPL", "TSLA"])
    
    # 3. Save Markdown Report (Trade Journal)
    os.makedirs("logs", exist_ok=True)
    with open("logs/research_report.md", "w") as f:
        f.write(journal)
    print(f"Research report saved to logs/research_report.md")

    # 4. Prepare and Dispatch Target Weights via Arrow IPC
    df = pd.DataFrame(weights_json["weights"])
    # Rename columns to match expected schema if necessary
    if 'ticker' not in df.columns and 'symbol' in df.columns:
        df = df.rename(columns={'symbol': 'ticker'})
    if 'weight' not in df.columns:
        # Fallback/Error handling if JSON structure was different
        print("Warning: JSON weights missing 'weight' column.")
    
    ipc_path = "/tmp/jegal_target_weights.arrow"
    write_target_weights(df, ipc_path)
    
    # 5. Trigger Rust Rebalancing
    print("Triggering Rust Rebalancer...")
    engine.run_rebalancing(ipc_path, tolerance=0.05)
    
    print("AI Research and Rebalancing orchestration complete.")

if __name__ == "__main__":
    asyncio.run(main())
