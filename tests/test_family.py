from ecoledirecte_py_client.family import Family
from ecoledirecte_py_client.student import Student


def test_family_initialization(client, mock_family_login_response):
    family = Family(client, mock_family_login_response["data"])
    assert len(family.students) == 2
    assert all(isinstance(s, Student) for s in family.students)
    assert family.students[0].id == 12345
    assert family.students[0].name == "John Smith"
    assert family.students[1].id == 12346
    assert family.students[1].name == "Alice Smith"


def test_family_check_students(client, mock_family_login_response):
    family = Family(client, mock_family_login_response["data"])
    students = family.check_students
    assert len(students) == 2
    assert students[0].id == 12345
