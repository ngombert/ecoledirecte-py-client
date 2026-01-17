# EcoleDirecte Test Suite

## Overview

This test suite provides comprehensive coverage of the refactored EcoleDirecte Python client library. The tests are organized by component and use pytest with pytest-async and pytest-httpx for mocking HTTP requests.

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── test_helpers.py                # Helper functions for creating mock data
├── test_models_auth.py            # Tests for authentication models
├── test_models_grades.py          # Tests for grades models
├── test_models_homework.py        # Tests for homework models  
├── test_models_schedule.py        # Tests for schedule models
├── test_models_messages.py        # Tests for messages models
├── test_models_common.py          # Tests for common models
├── test_managers_grades.py        # Tests for GradesManager
├── test_managers_homework.py      # Tests for HomeworkManager
├── test_managers_schedule.py      # Tests for ScheduleManager
├── test_managers_messages.py      # Tests for MessagesManager
├── test_client_auth.py            # Tests for client authentication
├── test_client_mfa.py             # Tests for MFA handling
├── test_client_persistence.py     # Tests for device/QCM persistence
├── test_client_errors.py          # Tests for error handling
├── test_student.py                # Tests for Student class
├── test_family.py                 # Tests for Family class
└── test_integration.py            # Integration/E2E tests
```

## Running Tests

### Run all tests:
```bash
uv run pytest tests/
```

### Run tests with verbose output:
```bash
uv run pytest tests/ -v
```

### Run tests for a specific module:
```bash
uv run pytest tests/test_client_auth.py -v
```

### Run a specific test:
```bash
uv run pytest tests/test_client_auth.py::TestClientAuthentication::test_login_success_student -v
```

### Run with coverage:
```bash
uv run pytest --cov=src/ecoledirecte_py_client --cov-report=html tests/
```

## Test Categories

### Model Tests
Test Pydantic model validation, parsing, field aliases, and computed properties.

**Note**: Some model tests may fail initially as they need to be adjusted to match the exact field names and aliases in the actual models. The models use Pydantic's `Field(alias="...")` for many fields (e.g., `valeur` instead of `value`).

### Manager Tests
Test the business logic in manager classes for grades, homework, schedule, and messages. These tests mock the HTTP client to avoid making real API calls.

### Client Tests
Comprehensive tests for:
- Authentication flow (GTK, login, token management)
- MFA handling (auto-submit from cache, callback invocation)
- Device token and QCM cache persistence
- Error handling for various HTTP and API errors

### Integration Tests
End-to-end tests that simulate complete workflows like:
- Student login and data fetching
- Family login with multiple students
- MFA flow with callbacks

## Current Status

✅ **Passing**: 
- Authentication model tests
- Common model tests  
- Student/Family class tests
- Client persistence tests

⚠️ **Needs Adjustment**:
- Some grades model tests (field name mismatches - `valeur` vs `value`)
- Some homework/schedule/messages model tests (need to check actual model structure)
- Client HTTP mocking tests (URL patterns may need adjusting)

## Known Issues

1. **Field Names**: The Grade model uses `valeur` (with French field names) rather than `value`. Tests referencing `grade.value` need to use `grade.valeur` instead.

2. **Required Fields**: Models have many required fields. The `create_mock_grade()` helper  has been updated to include all required fields, but some tests may still need adjustment.

3. **HTTP Mocking**: Some tests using `pytest-httpx` may need the exact URL patterns adjusted to match how the client constructs requests.

## Fixtures

### Shared Fixtures (from conftest.py)
- `api_responses`: Dict of all API responses from `api_responses/` directory
- `mock_login_response_student`: Mock student login response
- `mock_login_response_family`: Mock family login response  
- `mock_mfa_qcm_response`: Mock MFA question response
- `mock_mfa_success_response`: Mock successful MFA verification
- `temp_files`: Temporary file paths for device and QCM caching
- `mock_client`: Pre-configured Client instance for testing

### Helper Functions (from test_helpers.py)
- `build_api_response()`: Create standard API response structure
- `build_error_response()`: Create error response
- `create_mock_grade()`: Create mock grade data
- `create_mock_homework()`: Create mock homework data
- `create_mock_schedule_event()`: Create mock schedule event
- Various assertion helpers

## Contributing to Tests

When adding new tests:
1. Use appropriate fixtures from `conftest.py`
2. Use helper functions from `test_helpers.py` to create mock data
3. Mark async tests with `@pytest.mark.asyncio`
4. Group related tests in classes
5. Use descriptive test names and docstrings
6. Mock HTTP requests using `pytest-httpx` 's `HTTPXMock`

## Next Steps

1. ✅ Fix field name issues in model tests (use actual field names like `valeur`)
2. ⏳ Verify all required fields are present in mock data helpers
3. ⏳ Adjust HTTP URL patterns in client tests if needed
4. ⏳ Run full test suite and achieve >85% coverage
5. ⏳ Add any missing edge case tests
