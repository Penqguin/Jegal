# Contributing to Jegal

We welcome contributions! This project uses a Python/Rust hybrid structure managed by Maturin.

## Development Workflow

1. **Fork the repository** and create your branch from `main`.
2. **Set up the environment:**
    - Install Rust and Python dependencies.
    - Use `maturin develop` to build the Rust module during development.
3. **Code Standards:**
    - Rust: Follow standard `rustfmt` guidelines.
    - Python: Follow PEP 8 and use type hints where possible.
4. **Testing:**
    - Ensure all tests pass before submitting a PR.
    - Add new tests for any new features or bug fixes.
5. **Documentation:**
    - Update the `CHANGELOG.md` with your changes.
    - Document significant architectural changes in a new ADR (Architecture Decision Record) in the `docs/adr` directory.

## Local API Keys

For local testing, create a `.env` file in the root directory. This file is ignored by git.
