# Troubleshooting Guide

Solutions to common issues when using `ecoledirecte-py-client`.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Authentication Problems](#authentication-problems)
- [MFA Issues](#mfa-issues)
- [API Errors](#api-errors)
- [Network Issues](#network-issues)
- [Async/Await Problems](#asyncawait-problems)
- [Data Retrieval Issues](#data-retrieval-issues)
- [Debugging Tips](#debugging-tips)

---

## Installation Issues

### pip install fails

**Problem**: `pip install ecoledirecte-py-client` fails

**Solutions**:

1. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```

2. **Check Python version** (requires 3.9+):
   ```bash
   python --version
   ```

3. **Use virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install ecoledirecte-py-client
   ```

### Module not found after installation

**Problem**: `ModuleNotFoundError: No module named 'ecoledirecte_py_client'`

**Solutions**:

1. **Verify installation**:
   ```bash
   pip list | grep ecoledirecte
   ```

2. **Check multiple Python installations**:
   ```bash
   which python
   which pip
   ```

3. **Reinstall**:
   ```bash
   pip uninstall ecoledirecte-py-client
   pip install ecoledirecte-py-client
   ```

---

## Authentication Problems

### Login fails with correct credentials

**Problem**: `LoginError` despite correct username/password

**Possible causes & solutions**:

1. **Account locked** - Try logging in via web browser to verify
2. **Special characters in password**:
   ```python
   import urllib.parse
   password = urllib.parse.quote(password)  # Encode special chars
   ```

3. **Captcha required** - EcoleDirecte may require browser login first
4. **Account type mismatch** - Verify you're using the correct account type

**Debugging**:
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('httpx')

# This will show HTTP requests/responses
```

### Token expiration

**Problem**: Session works initially but fails after some time

**Solution**:
```python
from ecoledirecte_py_client import ApiError

async def fetch_with_reauth(client, session, username, password):
    """Fetch data with automatic re-authentication"""
    
    try:
        return await session.get_grades()
    
    except ApiError as e:
        if "token" in str(e).lower() or "401" in str(e):
            print("Token expired, re-authenticating...")
            session = await client.login(username, password)
            return await session.get_grades()
        raise
```

---

## MFA Issues

### MFA always required

**Problem**: MFA challenge appears on every login

**Causes**:
- EcoleDirecte security policy for your account
- Different IP addresses
- Not caching answers properly

**Solutions**:

1. **Verify cache file exists**:
   ```bash
   ls -la qcm.json
   ```

2. **Check cache file permissions**:
   ```bash
   chmod 600 qcm.json
   ```

3. **Validate cache format**:
   ```python
   import json
   
   with open('qcm.json') as f:
       data = json.load(f)
       print(json.dumps(data, indent=2))
   ```

### Cached answer not working

**Problem**: Cache exists but MFA still requires user input

**Common issues**:

1. **Question text mismatch** (case-sensitive):
   ```python
   # Wrong
   "Quelle est votre ville de residence ?"  # Missing accent
   
   # Correct
   "Quelle est votre ville de résidence ?"  # With accent
   ```

2. **Answer format mismatch**:
   ```python
   # Check what's cached
   import json
   with open('qcm.json') as f:
       cache = json.load(f)
   
   question = "Your question here"
   print(f"Cached answers: {cache.get(question, 'Not found')}")
   ```

3. **Empty answers array**:
   ```json
   {
     "Question": []  // ❌ Empty array
   }
   ```

**Fix**:
```python
def debug_mfa_cache(mfa_error, qcm_file='qcm.json'):
    """Debug MFA cache issues"""
    import json
    
    with open(qcm_file, 'r') as f:
        cache = json.load(f)
    
    print(f"Looking for: '{mfa_error.question}'")
    print(f"Cache keys: {list(cache.keys())}")
    
    # Check for similar questions
    for question in cache.keys():
        if question.lower() == mfa_error.question.lower():
            print(f"Found case mismatch: '{question}'")
    
    # Show cached answer
    if mfa_error.question in cache:
        print(f"Cached answer: {cache[mfa_error.question]}")
    else:
        print("Not in cache")
```

### MFA submission fails

**Problem**: `submit_mfa()` raises an error

**Solutions**:

1. **Verify answer is in propositions**:
   ```python
   answer = "PARIS"
   if answer not in mfa_error.propositions:
       print(f"Answer not in options: {mfa_error.propositions}")
   ```

2. **Check for encoding issues**:
   ```python
   answer = answer.strip()  # Remove whitespace
   answer = answer.upper()  # Try uppercase if needed
   ```

---

## API Errors

### HTTP 500 - Server Error

**Problem**: `ApiError: HTTP 500`

**Causes**:
- EcoleDirecte server issues
- Invalid request format
- Account-specific problems

**Solutions**:

1. **Retry with backoff**:
   ```python
   import asyncio
   
   async def fetch_with_retry(func, max_retries=3):
       for i in range(max_retries):
           try:
               return await func()
           except ApiError as e:
               if i == max_retries - 1:
                   raise
               wait_time = 2 ** i
               print(f"Retry {i+1} after {wait_time}s...")
               await asyncio.sleep(wait_time)
   ```

2. **Check EcoleDirecte status** - Try web interface

### HTTP 200 but unexpected data

**Problem**: API returns 200 OK but data is unexpected or empty

**Debug**:
```python
async def debug_response(student):
    """Print raw API response"""
    import json
    
    grades = await student.get_grades()
    print("Raw response:")
    print(json.dumps(grades, indent=2, ensure_ascii=False))
```

### Rate limiting

**Problem**: Too many requests error

**Solution**:
```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, requests_per_minute=30):
        self.rpm = requests_per_minute
        self.requests = []
    
    async def acquire(self):
        now = datetime.now()
        
        # Remove old requests
        self.requests = [
            r for r in self.requests 
            if now - r < timedelta(minutes=1)
        ]
        
        # Wait if at limit
        if len(self.requests) >= self.rpm:
            sleep_time = 60 - (now - self.requests[0]).seconds
            await asyncio.sleep(sleep_time)
            self.requests = []
        
        self.requests.append(now)

# Usage
limiter = RateLimiter(requests_per_minute=20)

async def fetch_with_limit(student):
    await limiter.acquire()
    return await student.get_grades()
```

---

## Network Issues

### Connection timeout

**Problem**: Requests timeout

**Solution**:
```python
import httpx
from ecoledirecte_py_client import Client

class ClientWithTimeout(Client):
    """Client with custom timeout"""
    
    def __init__(self, timeout=60.0):
        super().__init__()
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=5)
        )

# Usage
client = ClientWithTimeout(timeout=120.0)
```

### SSL certificate errors

**Problem**: `SSLError` or certificate verification failed

**Solutions**:

1. **Update certifi**:
   ```bash
   pip install --upgrade certifi
   ```

2. **Check system time** - Incorrect time causes SSL errors

3. **Temporary bypass** (not recommended for production):
   ```python
   import httpx
   
   # Override client with SSL verification disabled
   client.http_client = httpx.AsyncClient(verify=False)
   ```

### Proxy configuration

**Problem**: Need to use corporate proxy

**Solution**:
```python
import httpx
import os

# Configure proxy
proxies = {
    "http://": os.getenv("HTTP_PROXY"),
    "https://": os.getenv("HTTPS_PROXY"),
}

client.http_client = httpx.AsyncClient(proxies=proxies)
```

---

## Async/Await Problems

### "RuntimeError: This event loop is already running"

**Problem**: Running async code in Jupyter/IPython

**Solution**:
```python
# In Jupyter notebooks
import nest_asyncio
nest_asyncio.apply()

# Now you can use await directly
session = await client.login(username, password)
```

### "coroutine was never awaited"

**Problem**: Forgot to use `await`

**Wrong**:
```python
session = client.login(username, password)  # ❌ Missing await
```

**Correct**:
```python
session = await client.login(username, password)  # ✓
```

### Running multiple async functions

**Problem**: Need to run multiple operations

**Solution**:
```python
import asyncio

async def main():
    client = Client()
    session = await client.login(username, password)
    
    # Run concurrently
    grades, homework, messages = await asyncio.gather(
        session.get_grades(),
        session.get_homework(),
        session.get_messages()
    )
    
    await client.close()

# Run
asyncio.run(main())
```

---

## Data Retrieval Issues

### Empty grades/homework

**Problem**: Methods return empty data

**Possible causes**:

1. **No data available for  period**:
   ```python
   # Try different quarters
   for q in range(1, 5):
       grades = await student.get_grades(quarter=q)
       if grades:
           print(f"Found data for quarter {q}")
   ```

2. **Account permissions** - Student account may have restrictions

3. **School year not started** - No data available yet

### Date format issues

**Problem**: `get_schedule()` returns errors

**Solution**:
```python
from datetime import date

# Use ISO format: YYYY-MM-DD
start = date.today().isoformat()  # "2024-01-15"
end = date(2024, 1, 31).isoformat()

schedule = await student.get_schedule(start, end)
```

### Parsing response data

**Problem**: Unsure how to parse API responses

**Solution**:
```python
import json

async def explore_response(student):
    """Explore response structure"""
    
    grades = await student.get_grades()
    
    print("Response type:", type(grades))
    print("\nKeys:" if isinstance(grades, dict) else "\nLength:")
    
    if isinstance(grades, dict):
        for key in grades.keys():
            print(f"  - {key}: {type(grades[key])}")
    else:
        print(f"  {len(grades)} items")
    
    print("\nFull response:")
    print(json.dumps(grades, indent=2, ensure_ascii=False))
```

---

## Debugging Tips

### Enable detailed logging

```python
import logging

# Enable DEBUG logging for the library
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable httpx logging to see HTTP requests
logging.getLogger('httpx').setLevel(logging.DEBUG)
```

### Inspect HTTP traffic

```python
import httpx

# Create client with event hooks
async def log_request(request):
    print(f"Request: {request.method} {request.url}")
    print(f"Headers: {request.headers}")

async def log_response(response):
    print(f"Response: {response.status_code}")
    print(f"Body: {response.text[:500]}")  # First 500 chars

client.http_client = httpx.AsyncClient(
    event_hooks={
        'request': [log_request],
        'response': [log_response]
    }
)
```

### Save raw responses

```python
import json
from datetime import datetime

async def save_response(response_data, name):
    """Save API response for debugging"""
    
    filename = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved to {filename}")

# Usage
grades = await student.get_grades()
await save_response(grades, "grades")
```

### Version compatibility

```python
import sys
import ecoledirecte_py_client

print(f"Python version: {sys.version}")
print(f"Library version: {ecoledirecte_py_client.__version__ if hasattr(ecoledirecte_py_client, '__version__') else 'unknown'}")

# Check dependencies
import httpx
import pydantic

print(f"httpx version: {httpx.__version__}")
print(f"pydantic version: {pydantic.__version__}")
```

---

## Common Error Messages

### "KeyError: 'data'"

**Cause**: API response doesn't contain expected 'data' field

**Debug**:
```python
try:
    session = await client.login(username, password)
except Exception as e:
    # Check the actual response
    print(f"Error: {e}")
    # May need to inspect client internals
```

### "pydantic validation error"

**Cause**: API response doesn't match expected model structure

**Solution**: API may have changed, check response structure:
```python
# Bypass model validation temporarily to see raw data
response = await client.request(url, args)
print(response)  # See actual structure
```

---

## Getting Help

If you're still experiencing issues:

1. **Check GitHub Issues**: [ecoledirecte-py-client/issues](https://github.com/ngombert/ecoledirecte-py-client/issues)

2. **Create a minimal reproducible example**:
   ```python
   import asyncio
   from ecoledirecte_py_client import Client
   
   async def minimal_example():
       client = Client()
       try:
           session = await client.login("username", "password")
           print("Success!")
       except Exception as e:
           print(f"Error: {type(e).__name__}: {e}")
       finally:
           await client.close()
   
   asyncio.run(minimal_example())
   ```

3. **Include system info**:
   - Python version
   - Library version
   - Operating system
   - Error message and stack trace

4. **Sanitize credentials** - Never include real usernames/passwords in issues!

---

## Next Steps

- See [Usage Guide](usage.md) for best practices
- See [MFA Guide](mfa.md) for MFA-specific issues
- See [API Reference](api.md) for method documentation
