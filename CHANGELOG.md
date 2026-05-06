# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-05

### Added
- **Zero-Copy Arrow Bridge**: Native integration using Arrow C Data Interface for sub-microsecond latency between Python and Rust.
- **Advanced Risk Management**: Hardcoded exposure limits per symbol, global exposure limits, and a persistent drawdown-based "kill switch".
- **Broker Adapters**:
    - **IBKR**: Support for Interactive Brokers via local Gateway.
    - **Questrade**: OAuth-based adapter with token management.
    - **Mock**: Simulated broker for safe local testing and CI/CD.
- **Integration Test Suite**: End-to-end verification of the research and execution pipeline.
- **Secrets Management**: Integration with the `secrecy` crate to protect credentials in memory.

### Changed
- Refactored `ExecutionEngine` to handle native Arrow `RecordBatch` structures.
- Moved risk logic to a dedicated `src/risk.rs` module.
- Updated `README.md` with usage instructions for the full integrated system.

