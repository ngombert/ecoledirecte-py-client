# ecoledirecte-py-client

[![PyPI version](https://badge.fury.io/py/ecoledirecte-py-client.svg)](https://pypi.org/project/ecoledirecte-py-client/)
[![Python Support](https://img.shields.io/pypi/pyversions/ecoledirecte-py-client.svg)](https://pypi.org/project/ecoledirecte-py-client/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A comprehensive Python client library for the EcoleDirecte API, providing easy access to student data, grades, homework, schedules, and more. Built with async/await support and robust Multi-Factor Authentication (MFA) handling.

## Features

- **🔐 Dual Account Support**: Seamlessly handles both Student and Family (Parent) accounts
- **🛡️ MFA/CNED Support**: Integrated handling of Multi-Factor Authentication challenges
- **🤖 Smart MFA**: Automatically caches and reuses known MFA answers for frictionless future logins
- **⚡ Async/Await**: Built on modern async Python with `httpx` for efficient API calls
- **🔒 Secure by Default**: Credential management via environment variables
- **📦 Zero Configuration**: Works out of the box with minimal setup
- **🎯 Type Hints**: Full type annotations for better IDE support and code quality
- **✅ Well Tested**: Comprehensive test suite with pytest

## Installation

Install from PyPI using pip:

```bash
pip install ecoledirecte-py-client
```

Or using uv (recommended):

```bash
uv add ecoledirecte-py-client
```

## Quick Start

### Basic Usage (Student Account)

```python
import asyncio
from ecoledirecte_py_client import Client

async def main():
    # Create client and login
    client = Client()
    session = await client.login("username", "password")
    
    # Fetch student data
    grades = await session.get_grades()
    homework = await session.get_homework()
    messages = await session.get_messages()
    
    print(f"Retrieved {len(grades)} grades")
    
    # Always close the client
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Family Account with Multiple Students

```python
from ecoledirecte_py_client import Client, Family

async def main():
    client = Client()
    session = await client.login("parent_username", "parent_password")
    
    # Check if it's a family account
    if isinstance(session, Family):
        print(f"Found {len(session.students)} students")
        
        # Access each student
        for student in session.students:
            print(f"\n--- Data for {student.name} ---")
            grades = await student.get_grades()
            homework = await student.get_homework()
            print(f"Grades: {len(grades)}")
    
    await client.close()

asyncio.run(main())
```

### Handling MFA Challenges

```python
from ecoledirecte_py_client import Client, MFARequiredError

async def main():
    client = Client()
    
    try:
        session = await client.login("username", "password")
        print("Login successful!")
        
    except MFARequiredError as e:
        print(f"MFA Required: {e.question}")
        print("Options:")
        for idx, option in enumerate(e.propositions):
            print(f"  {idx}: {option}")
        
        # Get user input
        choice = int(input("Select option: "))
        answer = e.propositions[choice]
        
        # Submit MFA answer
        session = await client.submit_mfa(answer)
        print("MFA verification successful!")
    
    await client.close()

asyncio.run(main())
```

## Documentation

- **[API Reference](docs/api.md)** - Complete API documentation for all classes and methods
- **[Usage Guide](docs/usage.md)** - Advanced usage patterns and best practices
- **[MFA Handling](docs/mfa.md)** - Detailed guide on handling Multi-Factor Authentication
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Contributing](docs/contributing.md)** - Guide for contributors

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
ECOLEDIRECTE_USERNAME=your_username
ECOLEDIRECTE_PASSWORD=your_password
```

Then load it in your application:

```python
from dotenv import load_dotenv
import os

load_dotenv()

username = os.getenv("ECOLEDIRECTE_USERNAME")
password = os.getenv("ECOLEDIRECTE_PASSWORD")
```

### MFA Configuration

The library automatically manages MFA answers in a `qcm.json` file. When you successfully answer an MFA challenge, it's cached for future logins:

```json
{
  "Quelle est votre ville de résidence ?": ["PARIS"],
  "Quel est le niveau scolaire de <prénom> ?": ["QUATRIEMES"]
}
```

See [docs/mfa.md](docs/mfa.md) for detailed MFA handling strategies.

## Available Methods

### Student Class

```python
# Retrieve grades (all or by quarter)
grades = await student.get_grades()
grades_q1 = await student.get_grades(quarter=1)

# Get homework assignments
homework = await student.get_homework()

# Fetch schedule for date range
schedule = await student.get_schedule("2024-01-01", "2024-01-31")

# Access messages
messages = await student.get_messages()
```

### Family Class

```python
# Access list of students
for student in family.students:
    print(student.name, student.id)
    
# Each student has the same methods as Student class
grades = await family.students[0].get_grades()
```

## Examples

Check the `examples/` directory for complete, runnable examples:

```bash
# Run the demo with your credentials
uv run --env-file .env examples/demo.py
```

## Project Structure

```
ecoledirecte-py-client/
├── src/ecoledirecte_py_client/  # Core library code
│   ├── client.py                # Main Client class
│   ├── student.py               # Student account methods
│   ├── family.py                # Family account methods
│   ├── models.py                # Pydantic models
│   └── exceptions.py            # Custom exceptions
├── examples/                    # Usage examples
│   └── demo.py                  # Complete demo script
├── tests/                       # Test suite
├── docs/                        # Documentation
└── qcm.json.example            # Example MFA cache file
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ngombert/ecoledirecte-py-client.git
cd ecoledirecte-py-client

# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/ecoledirecte_py_client
```

See [docs/contributing.md](docs/contributing.md) for detailed contribution guidelines.

## Important Notes

- **Rate Limiting**: Be respectful of the EcoleDirecte API. Avoid excessive requests.
- **Credentials Security**: Never commit `.env` files or `qcm.json` with real data to version control.
- **MFA Answers**: The `qcm.json` file contains answers specific to your account. Keep it private.
- **Unofficial API**: This library uses an unofficial API that may change without notice.

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later). See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](docs/contributing.md) for details on our code of conduct and the process for submitting pull requests.

## Support

- **Issues**: [GitHub Issues](https://github.com/ngombert/ecoledirecte-py-client/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ngombert/ecoledirecte-py-client/discussions)

## Acknowledgments

This library is inspired by and references other EcoleDirecte API implementations. Special thanks to the EcoleDirecte community for reverse-engineering efforts.

---

**Disclaimer**: This is an unofficial client library and is not affiliated with or endorsed by EcoleDirecte. Use at your own risk.
