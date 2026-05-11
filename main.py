import asyncio
import json
import time
from jegal.jegal_graph import run_jegal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def watcher_loop():
    """
    The main Watcher loop that periodically triggers the Jegal research and execution pipeline.
    """
    while True:
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading config.json: {e}")
            await asyncio.sleep(60)
            continue

        watcher_cfg = config.get("watcher", {})
        if not watcher_cfg.get("enabled", True):
            print("Watcher is disabled in config.json. Exiting.")
            break

        print(f"\n{'='*50}")
        print(f"Watcher: Triggering Jegal Pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        try:
            await run_jegal()
        except Exception as e:
            print(f"Error during Jegal run: {e}")

        interval = watcher_cfg.get("interval_minutes", 60)
        print(f"\nWatcher: Sleeping for {interval} minutes...")
        await asyncio.sleep(interval * 60)

async def main():
    print("Starting Jegal System...")
    
    # Run the watcher loop
    await watcher_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nJegal System stopped by user.")
