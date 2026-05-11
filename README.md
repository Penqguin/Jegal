# Jegal

A high-performance personal open-source auto trader built with a Python/Rust hybrid architecture. Jegal combines autonomous LLM-driven research with a low-latency Rust execution engine.

## Features

- **Autonomous Research:** LangGraph-powered pipeline featuring News Scanners, Financial Researchers, and Earnings Reviewers.
- **Hybrid Architecture:** Python for research and orchestration; Rust for execution and risk management.
- **Zero-Copy Data Handoff:** Uses Apache Arrow for ultra-fast communication between Python and Rust.
- **Config-Driven:** Control risk, budget, broker settings, and LLM preferences through a single `config.json`.
- **Multi-LLM Support:** Integrated with Ollama (local), OpenAI, Anthropic, and Gemini.

## Prerequisites

- [Rust](https://www.rust-lang.org/tools/install) (latest stable)
- [Python 3.10+](https://www.python.org/downloads/)
- [Maturin](https://github.com/PyO3/maturin) (`pip install maturin`)
- [Ollama](https://ollama.com/) (optional, for local LLM support)

## Installation & Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/jegal.git
    cd jegal
    ```

2. **Configure environment variables:**

    Create a `.env` file for API keys if using cloud providers:

    ```bash
    # API keys (only required for cloud providers)
    # ANTHROPIC_API_KEY=sk-ant-xxx
    # OPENAI_API_KEY=sk-xxx
    # GEMINI_API_KEY=xxx
    ```

3. **Configure the system:**

    Edit `config.json` to set your risk limits, budget, and broker details:

    ```json
    {
      "risk": {
        "max_exposure_per_symbol": 50000.0,
        "max_total_exposure": 200000.0,
        "drawdown_limit": 5000.0
      },
      "broker": {
        "type": "ibkr",
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 1
      },
      "llm": {
        "provider": "ollama",
        "model": "llama3"
      }
    }
    ```

4. **Compile the Rust bindings:**

    ```bash
    maturin develop --release
    ```

5. **Install Python dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To start the autonomous trading system (the "Watcher"):

```bash
python main.py
```

This will run the research and execution pipeline at intervals defined in `config.json`.

## Documentation

- **Architecture:** See [ADR 1: Hybrid Architecture](docs/adr/0001-hybrid-architecture-with-arrow.md) and [ADR 2: Autonomous Pipeline](docs/adr/0002-autonomous-research-and-execution-pipeline.md).
- **Research Logs:** Trade journals and research reports are saved to `logs/research_report.md`.

## Security

- API keys and secrets should be stored in a local `.env` file.
- Risk limits are enforced in Rust at the execution level and cannot be bypassed by the Python research layer.

## Testing

- **Rust tests:** `cargo test`
- **Python tests:** `pytest`
