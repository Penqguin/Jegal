# Project: Personal Open-Source Auto Trader (Python/Rust Hybrid)

Core Directives for AI Agents

This document provides project-specific operational guidance and constraints that you, the AI coding agent, must follow when writing or modifying code in this repository.

1. Architectural Roles & Monorepo Structure

    Python: Use for strategy backtesting, data analysis (NumPy/Pandas), and high-level orchestration.

    Rust: Use strictly for the live execution engine to eliminate garbage collection pauses and ensure predictable latency.

    Project Layout: This is a mixed Python/Rust monorepo managed with maturin. Rust execution code resides in the src/ directory, while Python research scripts sit alongside it. Use the PyO3 library to compile the Rust engine into a module that Python can import.

2. Zero-Copy Data Transfer

    Never serialize large datasets (e.g., via JSON or standard RPC) between the Python and Rust components.

    Always use Apache Arrow to enable zero-copy memory sharing and high-performance data transfer across the language boundary.

3. Strict Security & API Key Management

    Local API Key Control: Never hardcode API keys in the source code, and do not design the system to rely on cloud-based secret vaults.

    Ensure all credentials are kept securely on the local device or Virtual Private Server (VPS), loaded strictly at runtime, and never committed to version control.

    All external API connections must enforce strict SSL encryption.

4. Risk Management & Kill Switch

    Ensure strict position and exposure limits are hardcoded directly at the trading agent level.

    All execution logic must include an automated "kill switch" that triggers based on daily loss thresholds, maximum drawdowns, margin utilization spikes, or abnormal order velocities.  

5. Open-Source Documentation Standards

    ADRs: When making significant architectural changes, document the reasoning in the project's Architecture Decision Records (ADRs) so future contributors understand the design.

    Keep the README.md, CONTRIBUTING.md, and CHANGELOG.md files up to date with clear setup instructions, feature additions, and testing rules.

6. Build & Setup Commands

    Compile Rust/Python bindings: maturin develop --release

    Run Python tests: pytest

    Run Rust tests: cargo test
