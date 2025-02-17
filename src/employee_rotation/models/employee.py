from __future__ import annotations
from random import choice
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass, field
from typing import Self, Optional
from itertools import product
import datetime as dt

from employee_rotation.models.exceptions import (
    DepartmentFullException,
    EmployeeNotAssignedtoDepartmentException,
)


@dataclass
class TimeSimulator:
    forwarded_months = 0

    @classmethod
    def forward_in_future(cls, months: float) -> None:
        cls.forwarded_months += months

    @classmethod
    def now(cls) -> dt.datetime:
        return dt.datetime.now() + dt.timedelta(days=30 * cls.forwarded_months)

    @classmethod
    def offset_month_randomly(cls, date: dt.datetime) -> dt.datetime:
        """Adds a month or deduct a month randomly from a date"""
        return date + relativedelta(months=choice([0, 1, 2]))


@dataclass
class Employee:
    first_name: str
    last_name: str
    _current_department: Optional[TrainingDepartment] = None
    start_date: Optional[dt.datetime] = None
    previous_departments: list[TrainingDepartment] = field(default_factory=list)
    time_simulator: TimeSimulator = dt.datetime  # type:ignore

    def __repr__(self) -> str:
        return f"{self.first_name} works in {self.current_department} since {self.days_spent_training:.0f} month(s)"

    def has_completed_training(self) -> bool:
        if self.current_department is None:
            raise EmployeeNotAssignedtoDepartmentException
        return self.current_department.duration - self.days_spent_training < 0

    def has_department(self):
        return self.current_department is not None

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}".title()

    @property
    def current_department(self) -> Optional[TrainingDepartment]:
        return self._current_department

    @current_department.setter
    def current_department(self, value: Optional[TrainingDepartment]):
        if self._current_department is not None:
            self.previous_departments.append(self._current_department)
        self._current_department = value

    @property
    def days_spent_training(self) -> int:
        if self.start_date is None:
            return 0
        now = self.time_simulator.now()
        return (now - self.start_date).days

    @property
    def hash(self):
        return self.__hash__()

    def __hash__(self):
        dept = (
            str(self.current_department.name)
            if self.current_department is not None
            else ""
        )
        return hash((self.full_name, dept))

    @staticmethod
    def new(row: tuple, departments: list[TrainingDepartment]) -> "Employee":
        emp = Employee(first_name=row[0], last_name=row[1], start_date=row[2])

        str_dept = row[3]
        for dept in departments:
            if dept.name == str_dept:
                dept.assign_employee(emp, start_date_overright=emp.start_date)
                break
        return emp


@dataclass
class TrainingDepartment:
    name: str
    duration_months: int
    max_capacity: int
    employees: list[Employee] = field(default_factory=list)
    time_simulator: TimeSimulator = dt.datetime  # type: ignore

    def __repr__(self):
        return f"{self.name} ({self.current_capacity}/{self.max_capacity} with {self.duration_months} months)"

    @property
    def duration(self):
        return self.duration_months * 30

    @property
    def current_capacity(self):
        return len(self.employees)

    @property
    def hash(self):
        return hash(tuple(self.employees))

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
        return self

    def remove_employee(self, emp: Employee) -> Self:
        if emp not in self.employees:
            raise ValueError("Employee is not currently in this department")
        for dept_emp in self.employees:
            if dept_emp is emp:
                self.employees.remove(emp)
                emp.current_department = None
                emp.start_date = None
        return self

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
) -> list[Employee]:
    for emp in emps:
        if not emp.has_department():
            continue
        if emp.has_completed_training():
            emp.current_department.remove_employee(emp)  # type: ignore

    for emp, dept in product(emps, departments):
        if not dept.has_capacity():
            continue
        elif dept in emp.previous_departments:
            continue
        elif not emp.has_department():
            dept.assign_employee(emp)
    return emps


if __name__ == "__main__":
    pass
