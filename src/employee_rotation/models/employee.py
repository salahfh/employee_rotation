from __future__ import annotations
from dataclasses import dataclass, field
from typing import Self, Optional, Literal
from itertools import product, repeat, chain
from enum import Enum, auto
import datetime as dt

from employee_rotation.models.exceptions import (
    DepartmentFullException,
    EmployeeNotAssignedtoDepartmentException,
)
from employee_rotation.models.rules import Rules


class Status(Enum):
    ASSIGNED = auto()
    WAITING_REASSIGNMENT = auto()
    FINISHED = auto()


@dataclass
class TimeSimulator:
    forwarded_months = 0

    @classmethod
    def forward_in_future(cls, months: float) -> None:
        cls.forwarded_months += months

    @classmethod
    def now(cls) -> dt.datetime:
        return dt.datetime.now() + dt.timedelta(days=30 * cls.forwarded_months)


@dataclass
class Employee:
    first_name: str
    last_name: str
    sexe: Literal["M", "F"] = "M"
    _current_department: Optional[TrainingDepartment] = None
    start_date: Optional[dt.datetime] = None
    previous_departments: list[tuple[TrainingDepartment, dt.datetime, dt.datetime]] = (
        field(default_factory=list)
    )
    excluded_departments: list[TrainingDepartment] = field(default_factory=list)
    time_simulator: TimeSimulator = dt.datetime  # type:ignore
    _status: Status = Status.ASSIGNED
    _changed: bool = False

    def __repr__(self) -> str:
        return f"{self.first_name} works in {self.current_department} since {self.days_spent_training:.0f} month(s)"

    def has_completed_training(self) -> bool:
        if self.current_department is None:
            raise EmployeeNotAssignedtoDepartmentException
        return self.current_department.duration - self.days_spent_training < 0

    def has_department(self):
        return self.status == Status.ASSIGNED

    def reset_mouvement_counter(self):
        self._changed = False

    @property
    def status(self) -> Status:
        return self._status

    @status.setter
    def status(self, value: Status):
        self._status = value
        self._changed = True

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}".title()

    @property
    def current_department(self) -> Optional[TrainingDepartment]:
        return self._current_department

    @current_department.setter
    def current_department(self, value: Optional[TrainingDepartment]):
        if self._current_department is not None:
            self.previous_departments.append(
                (self._current_department, self.start_date, self.time_simulator.now())  # type: ignore
            )
        self._current_department = value

    @property
    def days_spent_training(self) -> int:
        if self.start_date is None:
            return 0
        now = self.time_simulator.now()
        return (now - self.start_date).days

    @staticmethod
    def new(row: tuple, departments: list[TrainingDepartment]) -> "Employee":
        emp = Employee(
            first_name=row[0], last_name=row[1], sexe=row[2], start_date=row[3]
        )

        str_dept = row[4]
        for dept in departments:
            if dept.name == str_dept:
                dept.assign_employee(emp, start_date_overright=emp.start_date)
                break
        return emp

    def __hash__(self):
        return hash(f"{self.full_name} {self.sexe}")


@dataclass
class TrainingDepartment:
    name: str
    duration_months: int
    max_capacity: int
    employees: list[Employee] = field(default_factory=list)
    non_training_employees: set[Employee] = field(default_factory=set)
    time_simulator: TimeSimulator = dt.datetime  # type: ignore
    _rotation_movement: str = ""

    def __repr__(self):
        return f"{self.name} ({self.current_capacity}/{self.max_capacity} with {self.duration_months} months)"

    @property
    def duration(self):
        return self.duration_months * 30

    @property
    def current_capacity(self) -> int:
        return len(self.employees)

    @property
    def waiting_reassignment(self) -> list[Employee]:
        return [
            emp
            for emp in self.non_training_employees
            if emp.status is Status.WAITING_REASSIGNMENT
        ]

    @property
    def finished(self) -> list[Employee]:
        return [
            emp for emp in self.non_training_employees if emp.status is Status.FINISHED
        ]

    def reset_mouvement_counter(self):
        self._rotation_movement = ""

    def has_capacity(self) -> bool:
        return self.current_capacity < self.max_capacity

    def assign_employee(
        self, emp: Employee, start_date_overright: Optional[dt.datetime] = None
    ) -> Self:
        if not self.has_capacity():
            raise DepartmentFullException
        self.employees.append(emp)
        emp.current_department = self
        emp.start_date = self.time_simulator.now()
        if start_date_overright:
            emp.start_date = start_date_overright
        self._rotation_movement += "+"
        emp.status = Status.ASSIGNED
        return self

    def exclude_employee(self, emp: Employee) -> Self:
        if self.name not in [dp.name for dp in emp.excluded_departments]:
            emp.excluded_departments.append(self)
        return self

    def remove_employee(self, emp: Employee) -> Self:
        if emp not in self.employees:
            raise ValueError("Employee is not currently in this department")
        for dept_emp in self.employees:
            if dept_emp is emp:
                self.employees.remove(emp)
                emp.current_department = None
                emp.start_date = None
                break
        self._rotation_movement += "-"
        emp.status = Status.WAITING_REASSIGNMENT
        return self

    @staticmethod
    def mark_finished(emp: Employee, departments: list[TrainingDepartment]):
        if (
            sum([len(emp.previous_departments), len(emp.excluded_departments)])
            == len(departments)
            and emp.status is not Status.FINISHED
        ):
            emp.status = Status.FINISHED

    @staticmethod
    def readd_non_training(emp: Employee, departments: list[TrainingDepartment]):
        if emp.status is not Status.ASSIGNED:
            previous_dept = emp.previous_departments[-1][0]
            for dept in departments:
                if dept.name == previous_dept.name:
                    dept.non_training_employees.add(emp)

        # Clear out assigned one
        for dept in departments:
            non_training = set()
            for emp in dept.non_training_employees:
                if emp.status is not Status.ASSIGNED:
                    non_training.add(emp)
            dept.non_training_employees = non_training

    @staticmethod
    def new(row: tuple) -> "TrainingDepartment":
        return TrainingDepartment(
            name=row[0], duration_months=row[1], max_capacity=row[2]
        )


def rotate_one_employee(
    emp: Employee, departments: list[TrainingDepartment]
) -> Employee:
    return rotate_employees([emp], departments).pop()


def rotate_employees(
    emps: list[Employee],
    departments: list[TrainingDepartment],
    rules: Rules = Rules(),
) -> list[Employee]:
    for dept in departments:
        dept.reset_mouvement_counter()

    for emp in emps:
        emp.reset_mouvement_counter()

    for emp in emps:
        if not emp.has_department():
            continue
        if rules.check(
            emp,
            emp.current_department,  # type: ignore
            category="Operation",
            position="Pre",
        ):
            continue
        if emp.has_completed_training():
            emp.current_department.remove_employee(emp)  # type: ignore

    for emp, dept in product(emps, chain(*repeat(departments, 2))):
        if not dept.has_capacity():
            continue
        elif rules.check(emp, dept, category="Exclusion", position="Post"):
            dept.exclude_employee(emp)
        elif rules.check(emp, dept, category="Operation", position="Post"):
            continue
        elif not emp.has_department():
            dept.assign_employee(emp)

    for emp in emps:
        TrainingDepartment.mark_finished(emp, departments)
        TrainingDepartment.readd_non_training(emp, departments)
    return emps


if __name__ == "__main__":
    pass
