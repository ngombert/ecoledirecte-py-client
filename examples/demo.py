import asyncio
import os
import sys

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


import json

QCM_FILE = "qcm.json"


def load_qcm():
    if os.path.exists(QCM_FILE):
        try:
            with open(QCM_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_qcm(question, answer):
    data = load_qcm()
    # If the question already has answers, we might want to append?
    # For now let's just store the last correct answer or a list.
    # User asked "to keep track of all the possible questions... and correct response".
    if question not in data:
        data[question] = []

    if answer not in data[question]:
        data[question].append(answer)

    with open(QCM_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def fetch_data(session):
    students = []
    if isinstance(session, Family):
        print(f"Family account detected. Found {len(session.students)} students.")
        students = session.students
    elif isinstance(session, Student):
        students = [session]

    for student in students:
        name_info = getattr(student, "name", f"Student {student.id}")
        print(f"\n--- Data for {name_info} ---")

        print("Fetching grades...")
        grades = await student.get_grades()
        print(f"Grades fetched: {len(grades)} items (listing first 5 if available)")
        if isinstance(grades, list):
            print(grades[:5])
        else:
            print(grades)

        print("\nFetching homework...")
        homework = await student.get_homework()
        # Homework response structure might vary, let's explore it
        print(
            f"Homework data received (keys): {list(homework.keys()) if isinstance(homework, dict) else 'Not a dict'}"
        )
        # If homework contains dates which contain work:
        if isinstance(homework, dict):
            # Try to show some detail
            pass


async def main():
    username = os.environ.get("ECOLEDIRECTE_USER")
    password = os.environ.get("ECOLEDIRECTE_PASSWORD")

    if not username or not password:
        print(
            "Please set ECOLEDIRECTE_USER and ECOLEDIRECTE_PASSWORD environment variables."
        )
        return

    # Load device tokens if available
    device_info = {}
    if os.path.exists("device.json"):
        try:
            with open("device.json", "r") as f:
                device_info = json.load(f)
        except Exception:
            pass

    cn = device_info.get("cn")
    cv = device_info.get("cv")

    client = Client()
    session = None
    try:
        print(f"Logging in as {username}...")
        if cn and cv:
            print("Using saved device tokens to bypass MFA...")

        session = await client.login(username, password, cn=cn, cv=cv)
        print(f"Login successful! Session type: {type(session).__name__}")

        # Save device tokens if they are new or updated
        if client.cn and client.cv and (client.cn != cn or client.cv != cv):
            print("Saving new device tokens...")
            with open("device.json", "w") as f:
                json.dump({"cn": client.cn, "cv": client.cv}, f, indent=2)

        await fetch_data(session)

    except MFARequiredError as e:
        print("\n--- MFA REQUIRED ---")
        print(f"Question: {e.question}")  # This line was already correct

        known_answers = load_qcm().get(e.question, [])
        answer = None

        if known_answers:
            print(f"Known acceptable answers: {known_answers}")
            # Pick the most recent one (last added)
            potential_answer = known_answers[-1]
            print(f"Auto-selecting known answer: {potential_answer}")

            # Try auto-submission
            try:
                session = await client.submit_mfa(potential_answer)
                print("MFA Verification Successful (Auto)!")

                # Save device tokens after successful MFA
                if client.cn and client.cv:
                    print("Saving device tokens for future use...")
                    with open("device.json", "w") as f:
                        json.dump({"cn": client.cn, "cv": client.cv}, f, indent=2)

                await fetch_data(session)
                return  # Exit main on success
            except Exception as e:
                print(f"Auto-submission with '{potential_answer}' failed: {e}")
                print("Falling back to interactive mode...")

        if e.propositions:
            print("Propositions:")
            for idx, p in enumerate(e.propositions):
                print(f"{idx}: {p}")

        print("\nTo proceed, we would need to submit the answer interactively.")

        # Interactive prompt
        while True:
            choice = input("Enter your choice (index number) or the full text answer: ")

            answer = choice
            if choice.isdigit() and int(choice) < len(e.propositions):
                answer = e.propositions[int(choice)]
                print(f"Selected: {answer}")

            print(f"Submitting answer: {answer}")
            try:
                session = await client.submit_mfa(answer)
                print("MFA Verification Successful!")

                # Save correct answer
                save_qcm(e.question, answer)
                print("Answer saved to qcm.json")

                # Save device tokens after successful MFA
                if client.cn and client.cv:
                    print("Saving device tokens for future use...")
                    with open("device.json", "w") as f:
                        json.dump({"cn": client.cn, "cv": client.cv}, f, indent=2)

                await fetch_data(session)
                break

            except Exception as mfa_err:
                print(f"MFA Failed: {mfa_err}")
                print("Please try again.")
                # The session might need reset or just loop again
                # Assuming client allows retrying submit_mfa if session is still alive or refreshed within submit_mfa flow

    except LoginError as e:
        print(f"Login failed: {e}")

    except ApiError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
