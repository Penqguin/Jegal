# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-05-07

### Added
- **Target Portfolio Weight Architecture**: Implemented a new rebalancing model where the research layer dictates percentage-based target allocations.
- **Hybrid Threshold-Based Rebalancing**: Added a Rust rebalancer module that executes trades only when asset weights deviate from targets by a configurable threshold (e.g., 5%).
- **AI Research Layer (The Brains)**:
    - Added `FinancialResearchAgent` with support for Model Context Protocol (MCP) data connectors (Morningstar, SEC filings, News).
    - Implemented **Dual-Output Requirement**: Agent generates a human-readable Markdown 'trade journal' and a machine-readable JSON target weight object.
- **Arrow IPC Handoff**: Dedicated Arrow IPC stream bus for zero-copy transfer of portfolio targets from Python to Rust.
- **Enhanced Broker Trait**: Added support for position and balance fetching across all broker adapters.

### Changed
- Updated `research_main.py` to orchestrate the new AI-driven rebalancing workflow.
- Integrated `RiskManager` checks directly into the rebalancing execution loop.

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

