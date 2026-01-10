# Usage Guide

Advanced usage patterns and best practices for `ecoledirecte-py-client`.

## Table of Contents

- [Authentication Patterns](#authentication-patterns)
- [Working with Students](#working-with-students)
- [Working with Family Accounts](#working-with-family-accounts)
- [Error Handling](#error-handling)
- [Async Patterns](#async-patterns)
- [Production Deployment](#production-deployment)
- [Security Best Practices](#security-best-practices)
- [Real-World Examples](#real-world-examples)

---

## Authentication Patterns

### Basic Authentication

```python
import asyncio
from ecoledirecte_py_client import Client

async def authenticate():
    client = Client()
    try:
        session = await client.login("username", "password")
        return client, session
    except Exception as e:
        await client.close()
        raise

client, session = asyncio.run(authenticate())
```

### Environment-Based Authentication

```python
import os
from dotenv import load_dotenv
from ecoledirecte_py_client import Client

async def login_from_env():
    load_dotenv()
    
    username = os.getenv("ECOLEDIRECTE_USERNAME")
    password = os.getenv("ECOLEDIRECTE_PASSWORD")
    
    if not username or not password:
        raise ValueError("Missing credentials in environment")
    
    client = Client()
    session = await client.login(username, password)
    return client, session
```

### Context Manager Pattern (Recommended)

While the library doesn't currently implement context managers, you can create a wrapper:

```python
from contextlib import asynccontextmanager
from ecoledirecte_py_client import Client

@asynccontextmanager
async def ecoledirecte_session(username, password):
    """Context manager for automatic cleanup"""
    client = Client()
    try:
        session = await client.login(username, password)
        yield session
    finally:
        await client.close()

# Usage
async def main():
    async with ecoledirecte_session("user", "pass") as session:
        grades = await session.get_grades()
        # Client automatically closed after this block
```

---

## Working with Students

### Fetching Specific Quarter Grades

```python
async def get_quarter_summary(student, quarter):
    """Get summary of grades for a specific quarter"""
    grades = await student.get_grades(quarter=quarter)
    
    if not grades:
        return f"No data for quarter {quarter}"
    
    subjects = grades.get('ensembleMatieres', {}).get('disciplines', [])
    
    summary = []
    for subject in subjects:
        name = subject.get('discipline', 'Unknown')
        average = subject.get('moyenneEleve', 'N/A')
        summary.append(f"{name}: {average}")
    
    return "\n".join(summary)

# Usage
q1_summary = await get_quarter_summary(student, 1)
print(q1_summary)
```

### Working with Homework

```python
from datetime import datetime, timedelta

async def get_upcoming_homework(student, days=7):
    """Get homework due in the next N days"""
    homework_data = await student.get_homework()
    
    upcoming = []
    cutoff = datetime.now() + timedelta(days=days)
    
    # Parse homework structure (structure may vary)
    # This is an example - adjust based on actual API response
    for date_key, assignments in homework_data.items():
        try:
            assignment_date = datetime.strptime(date_key, "%Y-%m-%d")
            if assignment_date <= cutoff:
                upcoming.extend(assignments)
        except (ValueError, AttributeError):
            continue
    
    return upcoming
```

### Schedule Management

```python
from datetime import date, timedelta

async def get_this_week_schedule(student):
    """Get this week's schedule"""
    today = date.today()
    
    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())
    
    # Find Friday of current week
    friday = monday + timedelta(days=4)
    
    schedule = await student.get_schedule(
        monday.isoformat(),
        friday.isoformat()
    )
    
    return schedule

async def find_free_periods(student, date_str):
    """Find free periods in a day's schedule"""
    schedule = await student.get_schedule(date_str, date_str)
    
    # Sort by start time
    schedule.sort(key=lambda x: x.get('start_date', ''))
    
    free_periods = []
    for i in range(len(schedule) - 1):
        end_current = schedule[i].get('end_date')
        start_next = schedule[i + 1].get('start_date')
        
        if end_current and start_next and end_current < start_next:
            free_periods.append({
                'start': end_current,
                'end': start_next
            })
    
    return free_periods
```

---

## Working with Family Accounts

### Processing Multiple Students

```python
from ecoledirecte_py_client import Family, Student

async def process_all_students(session):
    """Process data for all students in a family account"""
    
    if not isinstance(session, Family):
        # Single student account
        return await process_single_student(session)
    
    results = {}
    for student in session.students:
        student_name = getattr(student, 'name', f'Student {student.id}')
        print(f"Processing {student_name}...")
        
        results[student_name] = await process_single_student(student)
    
    return results

async def process_single_student(student: Student):
    """Process a single student's data"""
    return {
        'grades': await student.get_grades(),
        'homework': await student.get_homework(),
        'messages': await student.get_messages()
    }
```

### Parallel Fetching for Performance

```python
import asyncio
from typing import List
from ecoledirecte_py_client import Student, Family

async def fetch_all_student_grades(family: Family) -> dict:
    """Fetch grades for all students in parallel"""
    
    async def fetch_student_grades(student: Student):
        student_name = getattr(student, 'name', f'Student {student.id}')
        grades = await student.get_grades()
        return student_name, grades
    
    # Fetch all grades concurrently
    results = await asyncio.gather(
        *[fetch_student_grades(s) for s in family.students],
        return_exceptions=True
    )
    
    # Build results dict, handling any errors
    grades_by_student = {}
    for result in results:
        if isinstance(result, Exception):
            print(f"Error fetching grades: {result}")
            continue
        
        name, grades = result
        grades_by_student[name] = grades
    
    return grades_by_student
```

### Comparing Student Performance

```python
async def compare_students(family: Family, quarter: int = None):
    """Compare grades across multiple students"""
    
    if len(family.students) < 2:
        return "Need at least 2 students to compare"
    
    comparison = {}
    
    for student in family.students:
        name = getattr(student, 'name', f'Student {student.id}')
        grades = await student.get_grades(quarter=quarter)
        
        # Extract average (structure depends on API response)
        avg = grades.get('moyenneGenerale', 'N/A')
        comparison[name] = avg
    
    return comparison
```

---

## Error Handling

### Comprehensive Error Handling

```python
from ecoledirecte_py_client import (
    Client,
    LoginError,
    ApiError,
    MFARequiredError,
    EcoleDirecteError
)
import logging

logger = logging.getLogger(__name__)

async def safe_login(username: str, password: str, max_retries: int = 3):
    """Login with retry logic and comprehensive error handling"""
    client = Client()
    
    for attempt in range(max_retries):
        try:
            session = await client.login(username, password)
            logger.info(f"Login successful on attempt {attempt + 1}")
            return client, session
        
        except MFARequiredError:
            # MFA requires special handling - don't retry
            raise
        
        except LoginError as e:
            logger.error(f"Login failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                await client.close()
                raise
            
            # Wait before retry
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        except ApiError as e:
            logger.error(f"API error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                await client.close()
                raise
            
            await asyncio.sleep(1)
        
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            await client.close()
            raise
    
    await client.close()
    raise LoginError("Max retries exceeded")
```

### Graceful Degradation

```python
async def fetch_student_data_safe(student):
    """Fetch student data with graceful degradation"""
    
    results = {
        'grades': None,
        'homework': None,
        'messages': None,
        'errors': []
    }
    
    # Try to fetch grades
    try:
        results['grades'] = await student.get_grades()
    except ApiError as e:
        results['errors'].append(f"Grades: {e}")
    
    # Try to fetch homework
    try:
        results['homework'] = await student.get_homework()
    except ApiError as e:
        results['errors'].append(f"Homework: {e}")
    
    # Try to fetch messages
    try:
        results['messages'] = await student.get_messages()
    except ApiError as e:
        results['errors'].append(f"Messages: {e}")
    
    return results
```

---

## Async Patterns

### Running Multiple Operations

```python
import asyncio

async def fetch_all_data(student):
    """Fetch all student data in parallel"""
    
    grades_task = student.get_grades()
    homework_task = student.get_homework()
    messages_task = student.get_messages()
    
    # Wait for all tasks to complete
    grades, homework, messages = await asyncio.gather(
        grades_task,
        homework_task,
        messages_task
    )
    
    return {
        'grades': grades,
        'homework': homework,
        'messages': messages
    }
```

### Timeout Handling

```python
import asyncio

async def fetch_with_timeout(student, timeout_seconds=30):
    """Fetch data with timeout"""
    
    try:
        grades = await asyncio.wait_for(
            student.get_grades(),
            timeout=timeout_seconds
        )
        return grades
    
    except asyncio.TimeoutError:
        print(f"Request timed out after {timeout_seconds} seconds")
        return None
```

### Background Tasks

```python
import asyncio

class StudentDataMonitor:
    """Monitor student data in the background"""
    
    def __init__( self, client, session):
        self.client = client
        self.session = session
        self.monitoring = False
        self.task = None
    
    async def monitor(self, interval_minutes=60):
        """Monitor student data at regular intervals"""
        self.monitoring = True
        
        while self.monitoring:
            try:
                print("Fetching latest data...")
                grades = await self.session.get_grades()
                messages = await self.session.get_messages()
                
                # Process data (e.g., check for new messages)
                self.process_data(grades, messages)
                
                # Wait before next check
                await asyncio.sleep(interval_minutes * 60)
            
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(60)  # Wait and retry
    
    def process_data(self, grades, messages):
        """Process fetched data"""
        # Implement your logic here
        pass
    
    def start(self, interval_minutes=60):
        """Start monitoring in background"""
        self.task = asyncio.create_task(self.monitor(interval_minutes))
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.task:
            self.task.cancel()
```

---

## Production Deployment

### Configuration Management

```python
from pydantic_settings import BaseSettings

class EcoleDirecteConfig(BaseSettings):
    """Configuration using pydantic-settings"""
    
    username: str
    password: str
    mfa_cache_file: str = "qcm.json"
    request_timeout: int = 30
    max_retries: int = 3
    
    class Config:
        env_prefix = "ECOLEDIRECTE_"
        env_file = ".env"

# Usage
config = EcoleDirecteConfig()
client = Client()
session = await client.login(config.username, config.password)
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ecoledirecte.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ecoledirecte_app')

async def main():
    logger.info("Starting application")
    
    try:
        client = Client()
        session = await client.login(username, password)
        logger.info(f"Logged in as {type(session).__name__}")
        
        # ... application logic
        
    except Exception as e:
        logger.exception("Application error")
        raise
    
    finally:
        await client.close()
        logger.info("Application stopped")
```

### Health Checks

```python
from datetime import datetime

async def health_check(client, session):
    """Check if the session is still valid"""
    
    try:
        # Try a simple API call
        await session.get_messages()
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
    
    except ApiError as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
```

---

## Security Best Practices

### Credential Management

```python
import os
from getpass import getpass

def get_credentials_safe():
    """Get credentials safely without hardcoding"""
    
    # Try environment variables first
    username = os.getenv('ECOLEDIRECTE_USERNAME')
    password = os.getenv('ECOLEDIRECTE_PASSWORD')
    
    # Fallback to interactive prompt
    if not username:
        username = input("Username: ")
    
    if not password:
        password = getpass("Password: ")  # Hidden input
    
    return username, password
```

### MFA Cache Security

```python
import json
import os
from pathlib import Path

def load_mfa_cache(filename="qcm.json"):
    """Load MFA cache with proper file permissions"""
    
    cache_path = Path(filename)
    
    # Create with restricted permissions if it doesn't exist
    if not cache_path.exists():
        cache_path.touch(mode=0o600)  # Read/write for owner only
        return {}
    
    # Check permissions
    stat_info = cache_path.stat()
    if stat_info.st_mode & 0o077:  # Check if group/others have access
        print("Warning: MFA cache has insecure permissions")
    
    with open(cache_path, 'r') as f:
        return json.load(f)

def save_mfa_cache(data, filename="qcm.json"):
    """Save MFA cache securely"""
    
    cache_path = Path(filename)
    
    # Write with restricted permissions
    with open(cache_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Ensure permissions are restrictive
    os.chmod(cache_path, 0o600)
```

---

## Real-World Examples

### Daily Grade Report

```python
import asyncio
from datetime import datetime
from ecoledirecte_py_client import Client

async def daily_grade_report(username, password):
    """Generate a daily summary of grades"""
    
    client = Client()
    
    try:
        session = await client.login(username, password)
        
        print(f"=== Daily Report - {datetime.now().strftime('%Y-%m-%d')} ===\n")
        
        if isinstance(session, Family):
            for student in session.students:
                await print_student_summary(student)
        else:
            await print_student_summary(session)
    
    finally:
        await client.close()

async def print_student_summary(student):
    name = getattr(student, 'name', f'Student {student.id}')
    print(f"--- {name} ---")
    
    grades = await student.get_grades()
    homework = await student.get_homework()
    
    print(f"Current Grades: {len(grades)} entries")
    print(f"Pending Homework: {len(homework)} items")
    print()

if __name__ == "__main__":
    asyncio.run(daily_grade_report("username", "password"))
```

### Homework Reminder Bot

```python
import asyncio
from datetime import datetime, timedelta

async def homework_reminder(client, session, notification_callback):
    """Check for homework due soon and send notifications"""
    
    if isinstance(session, Family):
        students = session.students
    else:
        students = [session]
    
    for student in students:
        name = getattr(student, 'name', f'Student {student.id}')
        homework = await student.get_homework()
        
        # Filter homework due in next 2 days
        upcoming = filter_upcoming_homework(homework, days=2)
        
        if upcoming:
            message = f"Reminder for {name}:\n"
            for hw in upcoming:
                message += f"- {hw['subject']}: {hw['description']}\n"
            
            notification_callback(message)

def filter_upcoming_homework(homework_data, days=2):
    """Filter homework due within specified days"""
    # Implementation depends on homework data structure
    return []  # Placeholder
```

### Export to CSV

```python
import csv
import asyncio

async def export_grades_to_csv(student, filename='grades.csv'):
    """Export grades to CSV file"""
    
    grades = await student.get_grades()
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Subject', 'Grade', 'Coefficient', 'Date'])
        
        # Write grades (structure depends on API response)
        for grade in grades:
            writer.writerow([
                grade.get('subject', ''),
                grade.get('value', ''),
                grade.get('coefficient', ''),
                grade.get('date', '')
            ])
    
    print(f"Grades exported to {filename}")
```

---

## Next Steps

- See [MFA Handling Guide](mfa.md) for advanced MFA strategies
- See [Troubleshooting](troubleshooting.md) for common issues
- See [API Reference](api.md) for complete method documentation
