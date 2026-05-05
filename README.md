# Jegal

A high-performance personal open-source auto trader built with a Python/Rust hybrid architecture.

## Architecture

- **Rust (Execution Engine):** Handles live execution, order management, and real-time risk checks (the "kill switch") to ensure low latency and zero garbage collection pauses.
- **Python (Research Layer):** Used for strategy orchestration, backtesting, and data analysis leveraging the NumPy/Pandas/PyArrow ecosystem.
- **Data Transfer:** Uses Apache Arrow for zero-copy memory sharing between Python and Rust.

## Prerequisites

- [Rust](https://www.rust-lang.org/tools/install) (latest stable)
- [Python 3.8+](https://www.python.org/downloads/)
- [Maturin](https://github.com/PyO3/maturin) (`pip install maturin`)

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/jegal.git
    cd jegal
    ```

2.  **Compile the Rust bindings:**
    ```bash
    maturin develop --release
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -e .
    ```

## Usage

To run the example strategy:
```bash
python jegal/strategy.py
```

## Security

- API keys and secrets should be stored in a local `.env` file or passed via environment variables.
- **NEVER** commit secrets to version control. The `.gitignore` is configured to protect these.

## Testing

- **Rust tests:** `cargo test`
- **Python tests:** `pytest`
