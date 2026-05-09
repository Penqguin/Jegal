import asyncio
import json
from dotenv import load_dotenv
from jegal.research_agents import NewsScannerAgent

# Load environment variables
load_dotenv()

async def watch_news():
    print("News Watcher Agent: Starting live market monitoring...")
    scanner = NewsScannerAgent()
    
    while True:
        try:
            print("News Watcher Agent: Scanning for catalysts...")
            # Load existing config
            with open("config.json", "r") as f:
                config = json.load(f)
            
            active_sectors = [s for s, active in config.get("sectors", {}).items() if active]
            
            catalysts = await scanner.scan_for_catalysts(active_sectors)
            
            if catalysts:
                updated = False
                for item in catalysts:
                    ticker = item["ticker"]
                    sector = item["sector"]
                    
                    # Only add if sector is active or it's a "special" ticker
                    is_active_sector = config.get("sectors", {}).get(sector, False)
                    
                    if is_active_sector and ticker not in config["manual_watchlist"] and ticker not in config["dynamic_watchlist"]:
                        print(f"News Watcher Agent: NEW CATALYST DETECTED for {ticker} in active sector {sector}. Adding to dynamic watchlist.")
                        config["dynamic_watchlist"].append(ticker)
                        updated = True
                
                if updated:
                    with open("config.json", "w") as f:
                        json.dump(config, f, indent=2)
                    print("News Watcher Agent: config.json updated.")
            else:
                print("News Watcher Agent: No significant catalysts found in this scan.")
                
        except Exception as e:
            print(f"News Watcher Agent Error: {e}")
            
        # Poll every 60 seconds (simulated)
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(watch_news())
