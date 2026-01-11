#!/usr/bin/env python3
"""
EcoleDirecte Python Client - Complete Demo
===========================================

This demo showcases ALL features of the ecoledirecte-py-client library,
demonstrating how an external developer would use this SDK in their application.

Features demonstrated:
- Client initialization and authentication
- MFA handling (auto-submission and interactive fallback)
- Device persistence (cn/cv tokens)
- Both Student and Family account types
- All managers: Grades, Homework, Schedule, Messages
- Working with typed Pydantic models
- Error handling and best practices
"""

import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Optional

# Ensure src is in python path for local testing without install
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ecoledirecte_py_client import (
    Client,
    LoginError,
    ApiError,
    MFARequiredError,
    Family,
    Student,
)

# Import Pydantic models to demonstrate type-safe data handling
from ecoledirecte_py_client.models.grades import Grade
from ecoledirecte_py_client.models.homework import HomeworkAssignment
from ecoledirecte_py_client.models.schedule import ScheduleEvent
from ecoledirecte_py_client.models.messages import Message

# Configuration files
QCM_FILE = "qcm.json"
DEVICE_FILE = "device.json"


# =============================================================================
# Helper Functions for MFA and Device Management
# =============================================================================


def load_qcm() -> dict:
    """Load saved MFA answers from qcm.json."""
    if os.path.exists(QCM_FILE):
        try:
            with open(QCM_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_qcm(question: str, answer: str):
    """Save a successful MFA answer to qcm.json."""
    data = load_qcm()
    if question not in data:
        data[question] = []

    if answer not in data[question]:
        data[question].append(answer)

    with open(QCM_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_device_tokens() -> tuple[Optional[str], Optional[str]]:
    """Load device tokens (cn, cv) from device.json."""
    if os.path.exists(DEVICE_FILE):
        try:
            with open(DEVICE_FILE, "r") as f:
                data = json.load(f)
                return data.get("cn"), data.get("cv")
        except Exception:
            pass
    return None, None


def save_device_tokens(cn: str, cv: str):
    """Save device tokens to device.json for future use."""
    with open(DEVICE_FILE, "w") as f:
        json.dump({"cn": cn, "cv": cv}, f, indent=2)


# =============================================================================
# Demo Functions - Grades Manager
# =============================================================================


async def demo_grades(client: Client, student_id: int):
    """
    Demonstrates the GradesManager with typed Pydantic models.

    Shows:
    - Fetching all grades
    - Filtering by period
    - Sorting by date
    - Working with Grade model properties
    - Calculating statistics
    """
    print("\n" + "=" * 80)
    print("📊 GRADES MANAGER DEMO")
    print("=" * 80)

    # Example 1: Get all grades for the student
    print("\n📚 Fetching all grades...")
    all_grades: List[Grade] = await client.grades.list(student_id)
    print(f"✓ Retrieved {len(all_grades)} grades total")

    if all_grades:
        # Show first few grades with Pydantic model properties
        print("\n📝 Sample grades (first 3):")
        for i, grade in enumerate(all_grades[:3], 1):
            print(f"\n  Grade {i}:")
            print(f"    Subject: {grade.libelle_matiere}")
            print(f"    Value: {grade.valeur}/{grade.note_sur}")
            print(
                f"    Normalized: {grade.normalized_value:.2f}/20"
                if grade.normalized_value
                else "    N/A"
            )
            print(f"    Coefficient: {grade.coef}")
            print(f"    Date: {grade.date.strftime('%Y-%m-%d')}")
            print(f"    Period: {grade.code_periode}")
            print(f"    Type: {grade.type_devoir}")

        # Example 2: Filter by period
        print("\n📅 Fetching grades for first period only (A001)...")
        period_grades: List[Grade] = await client.grades.list(
            student_id=student_id, period_id="A001"
        )
        print(f"✓ Retrieved {len(period_grades)} grades for period A001")

        # Example 3: Get grades sorted by date
        print("\n🗓️  Fetching grades sorted by date...")
        sorted_grades: List[Grade] = await client.grades.list(
            student_id=student_id, sort_by_date=True
        )
        if sorted_grades:
            oldest = sorted_grades[0]
            newest = sorted_grades[-1]
            print(
                f"✓ Oldest grade: {oldest.libelle_matiere} on {oldest.date.strftime('%Y-%m-%d')}"
            )
            print(
                f"✓ Newest grade: {newest.libelle_matiere} on {newest.date.strftime('%Y-%m-%d')}"
            )

        # Example 4: Calculate statistics using Pydantic model properties
        print("\n📈 Calculating statistics...")
        numeric_grades = [g for g in all_grades if g.normalized_value is not None]
        if numeric_grades:
            avg = sum(g.normalized_value for g in numeric_grades) / len(numeric_grades)
            max_grade = max(numeric_grades, key=lambda g: g.normalized_value)
            min_grade = min(numeric_grades, key=lambda g: g.normalized_value)

            print(f"  Average: {avg:.2f}/20")
            print(
                f"  Best: {max_grade.normalized_value:.2f} ({max_grade.libelle_matiere})"
            )
            print(
                f"  Lowest: {min_grade.normalized_value:.2f} ({min_grade.libelle_matiere})"
            )

            # Group by subject
            subjects = {}
            for grade in numeric_grades:
                if grade.libelle_matiere not in subjects:
                    subjects[grade.libelle_matiere] = []
                subjects[grade.libelle_matiere].append(grade.normalized_value)

            print("\n  📚 Averages by subject:")
            for subject, values in sorted(subjects.items())[:5]:  # Show top 5
                subject_avg = sum(values) / len(values)
                print(f"    {subject}: {subject_avg:.2f}/20 ({len(values)} grades)")


# =============================================================================
# Demo Functions - Homework Manager
# =============================================================================


async def demo_homework(client: Client, student_id: int):
    """
    Demonstrates the HomeworkManager with typed Pydantic models.

    Shows:
    - Fetching all homework
    - Filtering pending assignments
    - Sorting by due date
    - Working with HomeworkAssignment model
    """
    print("\n" + "=" * 80)
    print("📝 HOMEWORK MANAGER DEMO")
    print("=" * 80)

    # Example 1: Get all homework
    print("\n📚 Fetching all homework assignments...")
    all_homework: List[HomeworkAssignment] = await client.homework.list(student_id)
    print(f"✓ Retrieved {len(all_homework)} homework assignments")

    if all_homework:
        # Show sample homework with Pydantic model properties
        print("\n📋 Sample homework (first 2):")
        for i, hw in enumerate(all_homework[:2], 1):
            print(f"\n  Assignment {i}:")
            print(f"    Subject: {hw.matiere}")
            print(f"    Given on: {hw.donne_le.strftime('%Y-%m-%d')}")
            print(f"    Due on: {hw.pour_le.strftime('%Y-%m-%d')}")
            print(f"    Completed: {'✓' if hw.effectue else '✗'}")
            print(f"    Is test: {'✓' if hw.interrogation else '✗'}")
            print(f"    Online submission: {'✓' if hw.rendre_en_ligne else '✗'}")

        # Example 2: Get only pending homework, sorted by due date
        print("\n⏰ Fetching pending homework sorted by due date...")
        pending: List[HomeworkAssignment] = await client.homework.list(
            student_id=student_id, pending_only=True, sort_by_due_date=True
        )
        print(f"✓ Found {len(pending)} pending assignments")

        if pending:
            print("\n  📌 Next 3 assignments due:")
            for hw in pending[:3]:
                days_until = (hw.pour_le - datetime.now().date()).days
                urgency = (
                    "🔴 URGENT"
                    if days_until <= 1
                    else "🟡"
                    if days_until <= 3
                    else "🟢"
                )
                print(
                    f"    {urgency} {hw.matiere}: Due in {days_until} day(s) ({hw.pour_le.strftime('%Y-%m-%d')})"
                )

        # Example 3: Statistics
        completed_count = len([hw for hw in all_homework if hw.effectue])
        completion_rate = (
            (completed_count / len(all_homework)) * 100 if all_homework else 0
        )
        print(
            f"\n  📊 Completion rate: {completion_rate:.1f}% ({completed_count}/{len(all_homework)})"
        )


# =============================================================================
# Demo Functions - Schedule Manager
# =============================================================================


async def demo_schedule(client: Client, student_id: int):
    """
    Demonstrates the ScheduleManager with typed Pydantic models.

    Shows:
    - Fetching schedule for date range
    - Working with ScheduleEvent model
    - Sorting by date
    """
    print("\n" + "=" * 80)
    print("📅 SCHEDULE MANAGER DEMO")
    print("=" * 80)

    # Get current week's schedule
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=4)  # Mon-Fri

    start_date = start_of_week.strftime("%Y-%m-%d")
    end_date = end_of_week.strftime("%Y-%m-%d")

    print(f"\n📆 Fetching schedule from {start_date} to {end_date}...")
    events: List[ScheduleEvent] = await client.schedule.list(
        student_id=student_id,
        start_date=start_date,
        end_date=end_date,
        sort_by_date=True,
    )
    print(f"✓ Retrieved {len(events)} schedule events")

    if events:
        # Show a few events with Pydantic model properties
        print("\n🗓️  Sample schedule events (first 3):")
        for i, event in enumerate(events[:3], 1):
            print(f"\n  Event {i}:")
            print(f"    Subject: {event.matiere}")
            print(f"    Teacher: {event.prof or 'N/A'}")
            print(f"    Start: {event.start_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"    End: {event.end_date.strftime('%H:%M')}")
            print(f"    Room: {event.salle or 'N/A'}")
            print(f"    Cancelled: {'✓' if event.is_annule else '✗'}")

        # Group by day
        days = {}
        for event in events:
            day = event.start_date.date()
            if day not in days:
                days[day] = []
            days[day].append(event)

        print("\n  📊 Events by day:")
        for day, day_events in sorted(days.items()):
            print(f"    {day.strftime('%A, %Y-%m-%d')}: {len(day_events)} events")


# =============================================================================
# Demo Functions - Messages Manager
# =============================================================================


async def demo_messages(client: Client, student_id: int):
    """
    Demonstrates the MessagesManager with typed Pydantic models.

    Shows:
    - Fetching received messages
    - Fetching sent messages
    - Filtering unread messages
    - Working with Message model
    """
    print("\n" + "=" * 80)
    print("📬 MESSAGES MANAGER DEMO")
    print("=" * 80)

    # Example 1: Get all received messages
    print("\n📥 Fetching received messages...")
    received: List[Message] = await client.messages.list(
        student_id=student_id, message_type="received"
    )
    print(f"✓ Retrieved {len(received)} received messages")

    if received:
        # Show sample messages
        print("\n✉️  Sample received messages (first 2):")
        for i, msg in enumerate(received[:2], 1):
            read_status = "✓ Read" if msg.read else "✗ Unread"
            print(f"\n  Message {i}: [{read_status}]")
            print(f"    From: {msg.sender_name}")
            print(f"    Subject: {msg.subject}")
            print(f"    Date: {msg.date.strftime('%Y-%m-%d %H:%M')}")
            print(
                f"    Preview: {msg.content[:60]}..."
                if len(msg.content) > 60
                else f"    Content: {msg.content}"
            )

    # Example 2: Get unread messages only
    print("\n📬 Fetching unread messages...")
    unread: List[Message] = await client.messages.list(
        student_id=student_id, message_type="received", unread_only=True
    )
    print(f"✓ Found {len(unread)} unread messages")

    # Example 3: Get sent messages
    print("\n📤 Fetching sent messages...")
    sent: List[Message] = await client.messages.list(
        student_id=student_id, message_type="sent"
    )
    print(f"✓ Retrieved {len(sent)} sent messages")

    # Statistics
    if received:
        unread_count = len([m for m in received if not m.read])
        print("\n  📊 Message statistics:")
        print(f"    Total received: {len(received)}")
        print(f"    Unread: {unread_count}")
        print(f"    Sent: {len(sent)}")


# =============================================================================
# Main Student Data Function
# =============================================================================


async def fetch_student_data(client: Client, student_id: int, student_name: str):
    """
    Fetch and display all data for a student using all managers.

    This demonstrates the complete workflow a developer would use
    to access all student information through the SDK.
    """
    print("\n" + "=" * 80)
    print(f"👤 STUDENT: {student_name} (ID: {student_id})")
    print("=" * 80)

    try:
        # Demonstrate all managers in sequence
        await demo_grades(client, student_id)
        await demo_homework(client, student_id)
        await demo_schedule(client, student_id)
        await demo_messages(client, student_id)

    except ApiError as e:
        print(f"❌ API Error while fetching data: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


# =============================================================================
# Authentication and Main Flow
# =============================================================================


async def handle_mfa(client: Client, error: MFARequiredError):
    """
    Handle MFA challenge with auto-submission and interactive fallback.

    This demonstrates best practices for MFA handling in a production application.
    """
    print("\n" + "=" * 80)
    print("🔐 MFA CHALLENGE DETECTED")
    print("=" * 80)
    print(f"\nQuestion: {error.question}")

    # Try auto-submission with known answer
    known_answers = load_qcm().get(error.question, [])
    if known_answers:
        print(f"\n💡 Found {len(known_answers)} known answer(s) in qcm.json")
        answer = known_answers[-1]  # Use most recent
        print(f"🤖 Auto-submitting: {answer}")

        try:
            session = await client.submit_mfa(answer)
            print("✓ MFA verification successful (automatic)!")

            # Save device tokens
            if client.cn and client.cv:
                save_device_tokens(client.cn, client.cv)
                print("✓ Device tokens saved for future logins")

            return session

        except Exception as e:
            print(f"❌ Auto-submission failed: {e}")
            print("⚠️  Falling back to interactive mode...")

    # Interactive MFA handling
    print("\n📋 Available options:")
    for idx, option in enumerate(error.propositions):
        print(f"  {idx}: {option}")

    while True:
        choice = input("\n👉 Enter your choice (index or full text): ").strip()

        # Parse choice
        answer = choice
        if choice.isdigit() and int(choice) < len(error.propositions):
            answer = error.propositions[int(choice)]
            print(f"✓ Selected: {answer}")

        try:
            session = await client.submit_mfa(answer)
            print("✓ MFA verification successful!")

            # Save the correct answer
            save_qcm(error.question, answer)
            print("✓ Answer saved to qcm.json")

            # Save device tokens
            if client.cn and client.cv:
                save_device_tokens(client.cn, client.cv)
                print("✓ Device tokens saved for future logins")

            return session

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            print("Please try again...")


async def main():
    """
    Main entry point - Complete SDK usage example.

    Demonstrates:
    - Environment-based configuration
    - Device token persistence
    - Login with MFA handling
    - Working with both Student and Family accounts
    - Using all four managers (Grades, Homework, Schedule, Messages)
    - Type-safe data access with Pydantic models
    - Proper resource cleanup
    """
    print("\n" + "=" * 80)
    print("🎓 EcoleDirecte Python Client - Complete Demo")
    print("=" * 80)

    # Load credentials from environment
    username = os.environ.get("ECOLEDIRECTE_USER")
    password = os.environ.get("ECOLEDIRECTE_PASSWORD")

    if not username or not password:
        print("\n❌ Error: Missing credentials!")
        print(
            "Please set ECOLEDIRECTE_USER and ECOLEDIRECTE_PASSWORD environment variables."
        )
        print("\nExample:")
        print("  export ECOLEDIRECTE_USER='your_username'")
        print("  export ECOLEDIRECTE_PASSWORD='your_password'")
        print("\nOr use a .env file:")
        print("  uv run --env-file .env examples/demo_complete.py")
        return

    # Initialize client
    client = Client()
    session = None

    try:
        # Attempt login with device tokens (if available)
        cn, cv = load_device_tokens()
        if cn and cv:
            print("\n🔑 Using saved device tokens to bypass MFA...")
        else:
            print("\n🔑 Logging in (first time, MFA may be required)...")

        print(f"👤 Username: {username}")

        try:
            session = await client.login(username, password, cn=cn, cv=cv)
            print(f"✓ Login successful! Account type: {type(session).__name__}")

            # Save new device tokens if updated
            if client.cn and client.cv and (client.cn != cn or client.cv != cv):
                save_device_tokens(client.cn, client.cv)
                print("✓ Device tokens saved")

        except MFARequiredError as mfa_error:
            session = await handle_mfa(client, mfa_error)

        # Process the session
        if isinstance(session, Family):
            print(
                f"\n👨‍👩‍👧‍👦 Family account detected: {len(session.students)} student(s)"
            )

            # Demonstrate accessing multiple students
            for idx, student in enumerate(session.students, 1):
                student_name = getattr(student, "name", f"Student {student.id}")
                print(f"\n{'=' * 80}")
                print(f"Processing student {idx}/{len(session.students)}")
                await fetch_student_data(client, student.id, student_name)

        elif isinstance(session, Student):
            student_name = getattr(session, "name", f"Student {session.id}")
            await fetch_student_data(client, session.id, student_name)

        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\n📚 This demo showcased:")
        print("  ✓ Client authentication with MFA handling")
        print("  ✓ Device token persistence (cn/cv)")
        print("  ✓ GradesManager with typed Grade models")
        print("  ✓ HomeworkManager with typed HomeworkAssignment models")
        print("  ✓ ScheduleManager with typed ScheduleEvent models")
        print("  ✓ MessagesManager with typed Message models")
        print("  ✓ Support for both Student and Family accounts")
        print("  ✓ Type-safe data access with Pydantic models")
        print("\n💡 Check the source code to see how each feature is used!")

    except LoginError as e:
        print(f"\n❌ Login failed: {e}")
    except ApiError as e:
        print(f"\n❌ API Error: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Always clean up resources
        await client.close()
        print("\n👋 Client closed. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
