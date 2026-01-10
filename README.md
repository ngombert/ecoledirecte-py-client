# ecoledirecte-py-client

[![PyPI version](https://badge.fury.io/py/ecoledirecte-py-client.svg)](https://pypi.org/project/ecoledirecte-py-client/)
[![Python Support](https://img.shields.io/pypi/pyversions/ecoledirecte-py-client.svg)](https://pypi.org/project/ecoledirecte-py-client/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A Python client for the EcoleDirecte API, supporting both Student and Family accounts with Multi-Factor Authentication (MFA) handling.

## Features

- **Dual Account Support**: Seamlessly handles both Student and Family (Parent) accounts.
- **MFA Support**: Integrated handling of CNED/MFA challenges.
- **Interactive & Automated MFA**: 
  - Prompts for MFA codes interactively if needed.
  - Caches known MFA answers in `qcm.json` for automated future logins.
- **Secure**: Sensitive data is managed via environment variables.

## Installation

Install from PyPI using pip:

```bash
pip install ecoledirecte-py-client
```

Or using uv:

```bash
uv add ecoledirecte-py-client
```

## Configuration

1. **Environment Variables**:
   Create a `.env` file (or `.env_student` / `.env_family` for specific testing) with your credentials:

   ```env
   ECOLEDIRECTE_USERNAME=your_username
   ECOLEDIRECTE_PASSWORD=your_password
   # Optional: set to 'true' to skip actual login requests during dev
   ECOLEDIRECTE_DEMO_MODE=false 
   ```

2. **MFA Configuration**:
   The `qcm.json` file stores the mapping of MFA questions to answers. It is automatically updated when you solve a new challenge.
   
   *Note: Do not commit `qcm.json` if it contains personal answers, though the answers are specific to your account challenges.*

## Usage

```python
from ecoledirecte_py_client import Client
import asyncio

async def main():
    client = Client()
    await client.login("username", "password")
    # ...
```

Check the `examples/` directory for full usage scripts.

```bash
uv run --env-file .env examples/demo.py
```

## Project Structure

- `src/ecoledirecte_py_client/`: Core library code.
- `examples/`: Demo scripts.
- `qcm.json`: Local database of MFA Q&A.

## License

[GPLv3](LICENSE)
