# FureverMatch

A Python package for matching pets with forever homes.

## Installation

```bash
pip install -e .
```

## Usage

```python
from furever_match.main import App

app = App()
app.run()
```

Or use the command-line entry point:

```bash
furever-match
```

## Development

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run tests:
   ```bash
   pytest
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Project Structure

```
furever_match/
├── furever_match/          # Main package
│   ├── __init__.py
│   ├── main.py            # Main application module
│   ├── config.py          # Configuration management
│   └── utils.py           # Utility functions
├── tests/                  # Test directory
│   ├── __init__.py
│   └── test_main.py
├── setup.py               # Setup configuration
├── pyproject.toml         # Modern Python project config
└── .env                   # Environment variables
```

## License

MIT
