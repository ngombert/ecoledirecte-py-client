# API Reference

Complete API documentation for `ecoledirecte-py-client`.

## Table of Contents

- [Client](#client)
- [Student](#student)
- [Family](#family)
- [Models](#models)
- [Exceptions](#exceptions)

---

## Client

The main entry point for interacting with the EcoleDirecte API.

### Class: `Client`

```python
from ecoledirecte_py_client import Client
```

#### Constructor

```python
client = Client()
```

Creates a new client instance. Initializes the HTTP client and sets up headers required by the EcoleDirecte API.

**Returns**: `Client` instance

#### Methods

##### `login(username: str, password: str)`

Authenticates with the EcoleDirecte API.

```python
session = await client.login("username", "password")
```

**Parameters**:
- `username` (str): EcoleDirecte username (usually an identifier or email)
- `password` (str): EcoleDirecte password

**Returns**:
- `Student`: For student accounts
- `Family`: For family/parent accounts

**Raises**:
- `LoginError`: If authentication fails (invalid credentials)
- `MFARequiredError`: If Multi-Factor Authentication is required
- `ApiError`: If the API returns an unexpected error

**Example**:
```python
from ecoledirecte_py_client import Client, MFARequiredError

client = Client()
try:
    session = await client.login("my_username", "my_password")
    print(f"Logged in as: {type(session).__name__}")
except MFARequiredError as e:
    print(f"MFA required: {e.question}")
    # Handle MFA (see submit_mfa)
```

---

##### `submit_mfa(answer: str)`

Submits an answer to an MFA challenge.

```python
session = await client.submit_mfa(answer)
```

**Parameters**:
- `answer` (str): The answer to the MFA question (plain text)

**Returns**:
- `Student` or `Family`: Authenticated session object

**Raises**:
- `LoginError`: If MFA verification fails (wrong answer)
- `ApiError`: If the API returns an unexpected error

**Example**:
```python
try:
    session = await client.login(username, password)
except MFARequiredError as e:
    print(f"Question: {e.question}")
    for idx, option in enumerate(e.propositions):
        print(f"{idx}: {option}")
    
    choice = int(input("Select: "))
    answer = e.propositions[choice]
    
    session = await client.submit_mfa(answer)
    print("MFA successful!")
```

---

##### `request(url: str, args: Dict[str, Any] = None)`

Makes an authenticated request to the EcoleDirecte API.

```python
response = await client.request(url, args={"key": "value"})
```

**Parameters**:
- `url` (str): The API endpoint URL
- `args` (Dict[str, Any], optional): Request payload data

**Returns**:
- `Dict[str, Any]`: Parsed JSON response from the API

**Raises**:
- `ApiError`: If the API returns an error code or invalid response

**Note**: This is a low-level method. Most users should use the higher-level `Student` or `Family` methods instead.

---

##### `close()`

Closes the HTTP client connection.

```python
await client.close()
```

**Example**:
```python
client = Client()
try:
    session = await client.login(username, password)
    # ... use session
finally:
    await client.close()
```

**Best Practice**: Always close the client when done, or use as an async context manager if implemented.

---

## Student

Represents a student account and provides methods to retrieve student data.

### Class: `Student`

```python
from ecoledirecte_py_client import Student
```

**Note**: You typically don't instantiate `Student` directly. It's returned by `Client.login()` or accessed via `Family.students`.

#### Attributes

- `id` (int): Student account ID
- `name` (str): Student's full name (when accessed via Family account)
- `session` (Client): Reference to the parent Client session

#### Methods

##### `get_grades(quarter: Optional[int] = None)`

Retrieves the student's grades.

```python
grades = await student.get_grades()
grades_q1 = await student.get_grades(quarter=1)
```

**Parameters**:
- `quarter` (int, optional): Specific quarter/period to retrieve (e.g., 1, 2, 3, 4). If not provided, returns all available grades.

**Returns**:
- `Dict[str, Any]`: Grade data structure
  - When `quarter` is specified: Returns data for that specific period
  - When `quarter` is None: Returns all grades organized by period

**Example**:
```python
# Get all grades
all_grades = await student.get_grades()

# Get grades for quarter 1
q1_grades = await student.get_grades(quarter=1)
print(f"Q1 Period ID: {q1_grades.get('idPeriode')}")
print(f"Subjects: {q1_grades.get('ensembleMatieres')}")
```

---

##### `get_homework()`

Retrieves homework assignments from the student's cahier de texte (assignment notebook).

```python
homework = await student.get_homework()
```

**Returns**:
- `Dict[str, Any]`: Homework data structure containing assignments organized by date

**Example**:
```python
homework = await student.get_homework()

# Homework is typically organized by date
if 'matieres' in homework:
    for matiere in homework['matieres']:
        print(f"Subject: {matiere.get('matiere')}")
        print(f"Assignment: {matiere.get('aFaire')}")
```

---

##### `get_schedule(start_date: str, end_date: str)`

Retrieves the student's schedule (emploi du temps) for a date range.

```python
schedule = await student.get_schedule("2024-01-01", "2024-01-31")
```

**Parameters**:
- `start_date` (str): Start date in format "YYYY-MM-DD"
- `end_date` (str): End date in format "YYYY-MM-DD"

**Returns**:
- `List[Dict[str, Any]]`: List of scheduled classes/events

**Example**:
```python
from datetime import date, timedelta

# Get schedule for next week
today = date.today()
next_week = today + timedelta(days=7)

schedule = await student.get_schedule(
    today.isoformat(),
    next_week.isoformat()
)

for event in schedule:
    print(f"{event.get('matiere')} - {event.get('start_date')} to {event.get('end_date')}")
```

---

##### `get_messages()`

Retrieves the student's messages (received).

```python
messages = await student.get_messages()
```

**Returns**:
- `Dict[str, Any]`: Message data containing received messages

**Example**:
```python
messages = await student.get_messages()

if 'messages' in messages:
    for msg in messages['messages']:
        print(f"From: {msg.get('from')}")
        print(f"Subject: {msg.get('subject')}")
        print(f"Date: {msg.get('date')}")
```

---

## Family

Represents a family/parent account with access to multiple students.

### Class: `Family`

```python
from ecoledirecte_py_client import Family
```

**Note**: You don't instantiate `Family` directly. It's returned by `Client.login()` when logging in with parent credentials.

#### Attributes

- `session` (Client): Reference to the parent Client session
- `data` (Dict[str, Any]): Raw account data from login
- `students` (List[Student]): List of associated `Student` objects

#### Properties

##### `check_students`

Returns the list of associated students.

```python
students = family.check_students
```

**Returns**:
- `List[Student]`: List of Student objects

**Example**:
```python
client = Client()
family = await client.login("parent_username", "parent_password")

if isinstance(family, Family):
    students = family.check_students
    print(f"Found {len(students)} students")
    
    for student in students:
        print(f"Student: {student.name} (ID: {student.id})")
```

#### Methods

##### `fetch(token: str)`

Placeholder for specific family fetch logic.

```python
await family.fetch(token)
```

**Note**: Currently a placeholder method. Most family account functionality is accessed through the `students` list.

---

## Models

Pydantic models for type-safe data handling.

### `Account`

Represents an EcoleDirecte account.

```python
from ecoledirecte_py_client.models import Account
```

**Fields**:
- `id` (int): Account ID
- `type_compte` (str): Account type (e.g., "E" for student, "1"/"Famille" for family)
- `nom` (str, optional): Last name
- `prenom` (str, optional): First name
- `civilite` (str, optional): Title (M./Mme.)
- `data` (Dict[str, Any]): Additional account data

---

### `LoginResponseData`

Contains the data returned from a successful login.

**Fields**:
- `token` (str): Authentication token
- `accounts` (List[Account]): List of associated accounts

---

### `LoginResponse`

Complete login response structure.

**Fields**:
- `code` (int): Response code (200 for success)
- `token` (str): Authentication token
- `message` (str): Response message
- `data` (LoginResponseData): Login data containing accounts

---

### `ApiResponse`

Generic API response structure.

**Fields**:
- `code` (int): Response code
- `token` (str, optional): Token (if applicable)
- `message` (str, optional): Response message
- `data` (Any, optional): Response data payload

---

## Exceptions

Custom exception hierarchy for error handling.

### `EcoleDirecteError`

Base exception for all library errors.

```python
from ecoledirecte_py_client import EcoleDirecteError
```

All other exceptions inherit from this base class.

---

### `LoginError`

Raised when authentication fails.

```python
from ecoledirecte_py_client import LoginError
```

**Common causes**:
- Invalid username or password
- Account locked or suspended
- Network connectivity issues

**Example**:
```python
try:
    session = await client.login(username, password)
except LoginError as e:
    print(f"Login failed: {e}")
    # Check credentials and try again
```

---

### `ApiError`

Raised when the API returns an error or unexpected response.

```python
from ecoledirecte_py_client import ApiError
```

**Common causes**:
- Invalid API request
- Server error
- Rate limiting
- Malformed response

**Example**:
```python
try:
    grades = await student.get_grades()
except ApiError as e:
    print(f"API error: {e}")
    # Log error and retry or handle gracefully
```

---

### `MFARequiredError`

Raised when Multi-Factor Authentication is required during login.

```python
from ecoledirecte_py_client import MFARequiredError
```

**Attributes**:
- `question` (str): The MFA question text
- `propositions` (List[str]): List of possible answers

**Example**:
```python
try:
    session = await client.login(username, password)
except MFARequiredError as e:
    print(f"MFA Question: {e.question}")
    print("Options:")
    for idx, option in enumerate(e.propositions):
        print(f"  {idx}: {option}")
    
    # Get user input and submit answer
    choice = int(input("Select: "))
    session = await client.submit_mfa(e.propositions[choice])
```

---

## Type Hints

The library is fully typed. You can use type hints for better IDE support:

```python
from ecoledirecte_py_client import Client, Student, Family
from typing import Union

async def get_student_data(username: str, password: str) -> Union[Student, Family]:
    client = Client()
    session = await client.login(username, password)
    return session
```

---

## Complete Example

Here's a complete example demonstrating the API:

```python
import asyncio
from ecoledirecte_py_client import (
    Client,
    Student,
    Family,
    MFARequiredError,
    LoginError,
    ApiError
)

async def main():
    client = Client()
    
    try:
        # Login
        session = await client.login("username", "password")
        
        # Handle different account types
        if isinstance(session, Family):
            print(f"Family account with {len(session.students)} students")
            for student in session.students:
                await process_student(student)
        
        elif isinstance(session, Student):
            await process_student(session)
    
    except MFARequiredError as e:
        print(f"MFA Required: {e.question}")
        # Handle MFA...
    
    except LoginError as e:
        print(f"Login failed: {e}")
    
    except ApiError as e:
        print(f"API error: {e}")
    
    finally:
        await client.close()

async def process_student(student: Student):
    print(f"\nProcessing: {student.name if hasattr(student, 'name') else student.id}")
    
    # Fetch all data
    grades = await student.get_grades()
    homework = await student.get_homework()
    messages = await student.get_messages()
    
    print(f"  Grades: {len(grades)}")
    print(f"  Homework: {len(homework)}")

if __name__ == "__main__":
    asyncio.run(main())
```
