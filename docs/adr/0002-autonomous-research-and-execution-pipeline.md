# ADR 2: Autonomous Research and Execution Pipeline

## Status
Accepted

## Context
The system needs to move beyond static signal generation to an autonomous, configuration-driven model that can discover catalysts, perform deep research, and execute trades without manual intervention. It also needs a centralized configuration for risk, budget, and connectivity.

## Decision
We will implement an autonomous pipeline using LangGraph:
- **Watcher (main.py)**: A continuous loop that triggers the pipeline at configurable intervals.
- **News Scanner (NewsScannerAgent)**: Uses free sources (DuckDuckGo/YFinance) to discover market catalysts and potential tickers.
- **Financial Researcher (FinancialResearchAgent)**: Performs deep analysis using LLMs (Ollama, OpenAI, Anthropic, or Gemini) to generate target portfolio weights and a trade journal.
- **Execution Node**: Handsoff the research output to the Rust engine via Arrow IPC for risk-checked rebalancing.
- **Centralized Config (config.json)**: All user-configurable parameters (risk limits, budget, broker settings, LLM provider, watcher interval) are consolidated in a single file.

## Consequences
- **Pros**: Fully autonomous operation, easier user configuration, modular agent design, and robust handoff to low-latency Rust execution.
- **Cons**: Dependency on LLM availability/latency, potential for hallucination in research (mitigated by trade journals and human review logs).
