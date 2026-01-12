"""
MFA (Multi-Factor Authentication) utilities for EcoleDirecte.

This module provides helper functions for handling MFA challenges,
including built-in callbacks for common use cases.
"""

from typing import List


def default_console_callback(question: str, propositions: List[str]) -> str:
    """
    Built-in console-based MFA callback handler.

    Prompts user to select from available options by index or text.
    Validates input and retries on invalid selection.

    Args:
        question: The MFA question to display
        propositions: List of available answer options

    Returns:
        The selected answer

    Example:
        >>> from ecoledirecte_py_client import Client, default_console_callback
        >>> client = Client(mfa_callback=default_console_callback)
        >>> session = await client.login(username, password)
    """
    print(f"\n🔐 MFA Required: {question}")
    print("\n📋 Available options:")
    for idx, option in enumerate(propositions):
        print(f"  {idx}: {option}")

    while True:
        choice = input("\n👉 Enter your choice (index or text): ").strip()

        # Try to parse as index
        if choice.isdigit() and int(choice) < len(propositions):
            return propositions[int(choice)]

        # Try exact text match
        if choice in propositions:
            return choice

        print("❌ Invalid choice, please try again")
