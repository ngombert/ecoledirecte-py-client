# Contributing Guide

Thank you for your interest in contributing to `ecoledirecte-py-client`!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Project Structure](#project-structure)

---

## Code of Conduct

By participating in this project, you agree to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Finding Issues to Work On

1. Check [GitHub Issues](https://github.com/ngombert/ecoledirecte-py-client/issues)
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to indicate you're working on it

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/ecoledirecte-py-client.git
cd ecoledirecte-py-client

# Add upstream remote
git remote add upstream https://github.com/ngombert/ecoledirecte-py-client.git
```

### 2. Install Dependencies

**Using uv (recommended)**:
```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Using pip**:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e ".[dev]"
```

### 3. Configure Environment

```bash
# Copy example environment files
cp .env_student.example .env_student
cp .env_family.example .env_family

# Edit with your test credentials (optional, for manual testing)
# Note: Never commit real credentials!
```

### 4. Verify Setup

```bash
# Run tests
uv run pytest

# Or if using pip
pytest

# Check code formatting
uv run ruff check .
```

---

## Development Workflow

### 1. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Write code following the [code style guidelines](#code-style)
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_client.py

# Run with coverage
uv run pytest --cov=src/ecoledirecte_py_client --cov-report=html

# View coverage report
open htmlcov/index.html  # Or firefox/chrome htmlcov/index.html
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of changes"

# Push to your fork
git push origin feature/your-feature-name
```

### 5. Open Pull Request

1. Go to your fork on GitHub
2. Click "Compare & pull request"
3. Fill in the PR template
4. Link related issues
5. Wait for review

---

## Code Style

### General Guidelines

- Follow [PEP 8](https://pep8.org/)
- Use meaningful variable and function names
- Add type hints to all functions
- Write docstrings for public methods
- Keep functions focused and small

### Python Style

```python
from typing import Optional, Dict, Any

async def get_student_data(
    student_id: int,
    include_grades: bool = True
) -> Dict[str, Any]:
    """
    Fetch student data from the API.
    
    Args:
        student_id: The student's ID
        include_grades: Whether to include grade data
    
    Returns:
        Dictionary containing student data
    
    Raises:
        ApiError: If the API request fails
    """
    # Implementation here
    pass
```

### Formatting

We use `ruff` for linting and formatting:

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Import Organization

```python
# Standard library imports
import asyncio
import json
from typing import Optional, Dict

# Third-party imports
import httpx
from pydantic import BaseModel

# Local imports
from .models import Student
from .exceptions import ApiError
```

---

## Testing

### Test Structure

Tests are located in `tests/` directory:

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_client.py       # Client tests
├── test_student.py      # Student tests
└── test_family.py       # Family tests
```

### Writing Tests

```python
import pytest
from ecoledirecte_py_client import Client, LoginError

@pytest.mark.asyncio
async def test_login_success(mock_httpx):
    """Test successful login"""
    # Setup
    client = Client()
    
    # Mock API response
    mock_httpx.post("https://api.ecoledirecte.com/v3/login.awp").respond(
        json={
            "code": 200,
            "token": "test_token",
            "data": {
                "accounts": [{
                    "id": 123,
                    "typeCompte": "E"
                }]
            }
        }
    )
    
    # Execute
    session = await client.login("test_user", "test_pass")
    
    # Assert
    assert session is not None
    assert client.token == "test_token"

@pytest.mark.asyncio
async def test_login_failure(mock_httpx):
    """Test login with invalid credentials"""
    client = Client()
    
    mock_httpx.post("https://api.ecoledirecte.com/v3/login.awp").respond(
        json={"code": 505, "message": "Invalid credentials"}
    )
    
    with pytest.raises(LoginError):
        await client.login("wrong", "credentials")
```

### Running Tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/test_client.py

# Specific test
uv run pytest tests/test_client.py::test_login_success

# With coverage
uv run pytest --cov=src/ecoledirecte_py_client

# Verbose output
uv run pytest -v

# Show print statements
uv run pytest -s
```

### Test Fixtures

Use fixtures in `conftest.py` for shared test setup:

```python
# tests/conftest.py
import pytest
from ecoledirecte_py_client import Client

@pytest.fixture
def client():
    """Provide a client instance"""
    return Client()

@pytest.fixture
async def authenticated_session(client, mock_httpx):
    """Provide an authenticated session"""
    # Setup mock and login
    # ...
    return session
```

---

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Short description of function.
    
    Longer description if needed. Can span multiple lines and
    include details about the function's behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is empty
        ApiError: When API request fails
    
    Example:
        ```python
        result = example_function("test", 42)
        print(result)  # True
        ```
    """
    pass
```

### Updating Documentation

When adding new features:

1. Update relevant `.md` files in `docs/`
2. Add examples to README.md if applicable
3. Update API Reference (docs/api.md)
4. Add entry to CHANGELOG (if exists)

---

## Submitting Changes

### Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No debugging code or print statements
- [ ] No real credentials in code/tests

### PR Title Format

```
<type>: <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- test: Test changes
- refactor: Code refactoring
- chore: Maintenance tasks

Examples:
feat: Add support for fetching absence data
fix: Resolve MFA caching issue (#123)
docs: Update installation instructions
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issues
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing Done
- [ ] Added new tests
- [ ] All tests pass
- [ ] Manually tested with real API

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

---

## Project Structure

```
ecoledirecte-py-client/
├── src/ecoledirecte_py_client/  # Main package
│   ├── __init__.py              # Package exports
│   ├── client.py                # Main Client class
│   ├── student.py               # Student class
│   ├── family.py                # Family class
│   ├── models.py                # Pydantic models
│   └── exceptions.py            # Custom exceptions
├── tests/                       # Test suite
│   ├── conftest.py             # Test fixtures
│   ├── test_client.py          # Client tests
│   ├── test_student.py         # Student tests
│   └── test_family.py          # Family tests
├── docs/                        # Documentation
│   ├── api.md                  # API reference
│   ├── usage.md                # Usage guide
│   ├── mfa.md                  # MFA guide
│   ├── troubleshooting.md      # Troubleshooting
│   └── contributing.md         # This file
├── examples/                    # Example scripts
│   └── demo.py                 # Complete demo
├── .github/                     # GitHub configs
│   └── workflows/              # CI/CD workflows
├── pyproject.toml              # Project metadata
├── README.md                   # Main README
└── LICENSE                     # License file
```

### Key Components

- **Client**: Main entry point, handles authentication and HTTP requests
- **Student**: Methods for student data (grades, homework, schedule, messages)
- **Family**: Manages multiple students for parent accounts
- **Models**: Pydantic models for type-safe data handling
- **Exceptions**: Custom exception hierarchy

---

## Development Tips

### Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints (remove before committing!)
print(f"Debug: {variable}")
```

### Testing with Real API

```python
# Create a test script (don't commit!)
import asyncio
from ecoledirecte_py_client import Client

async def manual_test():
    client = Client()
    session = await client.login("test_user", "test_pass")
    grades = await session.get_grades()
    print(grades)
    await client.close()

asyncio.run(manual_test())
```

### Performance Profiling

```python
import cProfile

def profile_function():
    # Your code here
    pass

cProfile.run('profile_function()')
```

---

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG (if exists)
3. Create git tag: `git tag v0.2.1`
4. Push tag: `git push --tags`
5. GitHub Actions will build and publish to PyPI

---

## Questions?

- Open a [GitHub Discussion](https://github.com/ngombert/ecoledirecte-py-client/discussions)
- Comment on relevant issues
- Check existing documentation

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (GPL-3.0-or-later).

---

Thank you for contributing! 🎉
