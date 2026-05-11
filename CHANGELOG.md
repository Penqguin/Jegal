# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-05-09

### Added
- **Autonomous Watcher Loop**: `main.py` now implements a continuous watcher that triggers the research and execution pipeline at configurable intervals.
- **Centralized Configuration**: All system parameters (risk, budget, broker, LLM, and watcher) are now consolidated in `config.json`.
- **LangGraph Integration**: The research layer now uses a stateful graph to manage news discovery, deep research, and execution handoff.
- **Dynamic Watchlist Discovery**: `NewsScannerAgent` now scans live news via free sources (DuckDuckGo/YFinance) and updates the dynamic watchlist in real-time.
- **Improved LLM Support**: Added support for choosing LLM provider (Ollama, OpenAI, Anthropic, Gemini) and model directly in `config.json`.
- **ADR 2**: Documented the architectural shift toward an autonomous research and execution pipeline.

### Changed
- Refactored `main.py` from a simulation script to a production-ready entry point.
- Updated `FinancialResearchAgent` and `NewsScannerAgent` to prefer configuration from `config.json`.
- Enhanced `execution_node` to use live broker and risk settings from centralized config.

## [0.2.0] - 2026-05-05

### Added
- **Zero-Copy Arrow Bridge**: Native integration using Arrow C Data Interface for sub-microsecond latency between Python and Rust.
- **Advanced Risk Management**: Hardcoded exposure limits per symbol, global exposure limits, and a persistent drawdown-based "kill switch".
- **Broker Adapters**:
    - **IBKR**: Support for Interactive Brokers via local Gateway.
    - **Mock**: Simulated broker for safe local testing and CI/CD.

- **Integration Test Suite**: End-to-end verification of the research and execution pipeline.
- **Secrets Management**: Integration with the `secrecy` crate to protect credentials in memory.

### Changed
- Refactored `ExecutionEngine` to handle native Arrow `RecordBatch` structures.
- Moved risk logic to a dedicated `src/risk.rs` module.
- Updated `README.md` with usage instructions for the full integrated system.

