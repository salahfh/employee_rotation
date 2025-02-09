from employee_rotation.models import (
    Employee,
    TrainingDepartment,
    DepartmentFullException,
    EmployeeNotAssignedtoDepartmentException,
    rotate_one_employee,
    rotate_employees,
)
from datetime import datetime as dt

import pytest


@pytest.fixture()
def departments():
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    achat_local = TrainingDepartment("Achats Local", duration=6, max_capacity=3)
    finance = TrainingDepartment("Finance", duration=12, max_capacity=4)
    imports = TrainingDepartment("Imports", duration=6, max_capacity=1)
    departments = [achat_local, achat_etrange, finance, imports]
    return departments


def test_assign_emp_to_depart():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)

    achat_etrange.assign_employee(chouaib)

    assert chouaib.current_department == achat_etrange
    assert chouaib in achat_etrange.employees


def test_assign_emp_to_depart_when_dept_is_full():
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    emp1 = Employee("EMP1", "BEGHOURA")
    emp2 = Employee("EMP2", "BEGHOURA")
    emp3 = Employee("EMP3", "BEGHOURA")
    for emp in [emp1, emp2, emp3]:
        achat_etrange.assign_employee(emp)

    chouaib = Employee("CHOUAIB", "BEGHOURA")

    with pytest.raises(DepartmentFullException):
        achat_etrange.assign_employee(chouaib)


def test_remove_emp_from_dept():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    achat_etrange.assign_employee(chouaib)

    achat_etrange.remove_employee(chouaib)

    assert chouaib.current_department is None
    assert chouaib not in achat_etrange.employees


def test_remove_emp_from_dept_where_not_added_in_first_place():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)

    with pytest.raises(ValueError):
        achat_etrange.remove_employee(chouaib)


def test_employee_previous_deparments():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    finance = TrainingDepartment("Finance", duration=12, max_capacity=4)

    achat_etrange.assign_employee(chouaib)

    assert chouaib.current_department == achat_etrange
    assert chouaib.previous_departments == []

    finance.assign_employee(chouaib)

    assert chouaib.current_department == finance
    assert chouaib.previous_departments == [achat_etrange]


def test_employee_time_spent_training():
    # Need mocking for the datetime module?
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    achat_etrange.assign_employee(chouaib)

    assert chouaib.month_spent_training == 0

    chouaib.start_date = dt(2025, 1, 1)
    assert chouaib.month_spent_training == 1.3


def test_employee_has_completed_training():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    achat_etrange.assign_employee(chouaib)

    chouaib.start_date = dt(2025, 1, 1)
    assert not chouaib.has_completed_training()

    chouaib.start_date = dt(2024, 1, 1)
    assert chouaib.has_completed_training()


def test_employee_has_completed_training_not_assigned_employee():
    chouaib = Employee("CHOUAIB", "BEGHOURA")

    with pytest.raises(EmployeeNotAssignedtoDepartmentException):
        assert chouaib.has_completed_training()


def test_employee_rotation_completed_training():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    imports = TrainingDepartment("Imports", duration=6, max_capacity=1)
    departments = [achat_etrange, imports]

    achat_etrange.assign_employee(chouaib)
    chouaib.start_date = dt(2024, 1, 1)
    assert chouaib.has_completed_training()

    chouaib = rotate_one_employee(chouaib, departments)

    assert chouaib.current_department is imports


def test_employee_rotation_not_completed_training():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    imports = TrainingDepartment("Imports", duration=6, max_capacity=1)
    departments = [achat_etrange, imports]

    achat_etrange.assign_employee(chouaib)
    assert not chouaib.has_completed_training()

    chouaib = rotate_one_employee(chouaib, departments)

    assert chouaib.current_department is achat_etrange


def test_employees_rotation_not_completed_training():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    siham = Employee("SIHAM", "BEGHOURA")
    hamid = Employee("HAMID", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    imports = TrainingDepartment("Imports", duration=6, max_capacity=1)
    departments = [achat_etrange, imports]
    emps = [chouaib, siham, hamid]

    achat_etrange.assign_employee(chouaib)
    achat_etrange.assign_employee(hamid)
    imports.assign_employee(siham)

    rotate_employees(emps, departments)

    assert chouaib.current_department is achat_etrange
    assert hamid.current_department is achat_etrange
    assert siham.current_department is imports


def test_employees_rotation_all_completed_training():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    siham = Employee("SIHAM", "BEGHOURA")
    hamid = Employee("HAMID", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    imports = TrainingDepartment("Imports", duration=6, max_capacity=3)
    departments = [achat_etrange, imports]
    emps = [chouaib, siham, hamid]

    achat_etrange.assign_employee(chouaib)
    achat_etrange.assign_employee(hamid)
    imports.assign_employee(siham)

    for emp in emps:
        emp.start_date = dt(2024, 1, 1)
        assert emp.has_completed_training()

    rotate_employees(emps, departments)

    assert chouaib.current_department is imports
    assert hamid.current_department is imports
    assert siham.current_department is achat_etrange


def test_employees_rotation_all_completed_training_with_limited_capacity_dept():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    siham = Employee("SIHAM", "BEGHOURA")
    hamid = Employee("HAMID", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    imports = TrainingDepartment("Imports", duration=6, max_capacity=1)
    departments = [achat_etrange, imports]
    emps = [chouaib, siham, hamid]

    achat_etrange.assign_employee(chouaib)
    achat_etrange.assign_employee(hamid)
    imports.assign_employee(siham)

    for emp in emps:
        emp.start_date = dt(2024, 1, 1)
        assert emp.has_completed_training()

    rotate_employees(emps, departments)

    assert siham.current_department is achat_etrange
    assert chouaib.current_department is imports
    assert hamid.current_department is None


def test_employees_rotation_employees_with_mixed_finish_status():
    chouaib = Employee("CHOUAIB", "BEGHOURA")
    siham = Employee("SIHAM", "BEGHOURA")
    hamid = Employee("HAMID", "BEGHOURA")
    achat_etrange = TrainingDepartment("Achat Etranger", duration=6, max_capacity=3)
    imports = TrainingDepartment("Imports", duration=36, max_capacity=1)
    departments = [achat_etrange, imports]
    emps = [chouaib, siham, hamid]

    achat_etrange.assign_employee(chouaib)
    achat_etrange.assign_employee(hamid)
    imports.assign_employee(siham)

    for emp in emps:
        emp.start_date = dt(2024, 1, 1)

    rotate_employees(emps, departments)

    assert siham.current_department is imports
    assert chouaib.current_department is None
    assert hamid.current_department is None