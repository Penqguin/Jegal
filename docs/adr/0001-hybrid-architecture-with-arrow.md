# ADR 1: Python/Rust Hybrid Architecture with Apache Arrow

## Status
Proposed

## Context
We need a system that combines the rapid prototyping and rich data science ecosystem of Python with the low-latency, garbage-collection-free execution of Rust. Traditional serialization (JSON/MsgPack) between these layers introduces significant overhead.

## Decision
We will use a Python/Rust hybrid architecture:
- **Python** for strategy research, signal generation, and high-level orchestration.
- **Rust** for the live execution engine and real-time risk management (the "kill switch").
- **Apache Arrow** as the data exchange format to enable zero-copy memory sharing across the language boundary via the Arrow C Data Interface.

## Consequences
- **Pros**: Sub-microsecond risk checks, full access to Python's ML/Quant libraries, minimal memory overhead during data transfer.
- **Cons**: Increased build complexity (requires Rust toolchain and `maturin`), developer must manage memory safety across the FFI boundary.
