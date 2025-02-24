from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Self, Any, Callable
from functools import partial, wraps

if TYPE_CHECKING:
    from employee_rotation.models.employee import Employee, TrainingDepartment


class Rules:
    """
    Apply filter rules.

    Category:
    * Operation rules are business general.
    * Excelution rules are for permenat actions.

    Position: Depending on the location the check function is called.
    * Pre: applied during removal of department
    * Post: applied during assignment of department
    """

    def __init__(
        self,
    ) -> None:
        self.rules = list()

    def check(
        self,
        emp: Employee,
        dept: TrainingDepartment,
        *,
        category: Literal["Exclusion", "Operation"],
        position: Literal["Pre", "Post", "All"] = "All",
    ) -> bool:
        for fltr in self.rules:
            if fltr(emp, dept, position=position, category=category):
                return True
        return False

    def add_rules(
        self,
        rules: list[str] | list[tuple[str, dict[str, Any]]],
    ) -> Self:
        for item in rules:
            match item:
                case f_name, kwargs:
                    f_name = f_name
                    kwargs = kwargs
                case f_name:
                    f_name = f_name
                    kwargs = {}
            if not hasattr(self, f_name):
                raise ValueError(
                    f"{f_name} is not a valid rule. please change your configration"
                )
            rule_func = partial(getattr(self, f_name), **kwargs)
            self.rules.append(rule_func)
        return self

    @staticmethod
    def meta(
        *,
        position: Literal["All", "Pre", "Post"],
        category: Literal["Operation", "Exclusion"],
    ):
        def decorated(f: Callable):
            @wraps(f)
            def wrapper(*args, **kwargs):
                position_match = position == kwargs.pop("position")
                category_match = category == kwargs.pop("category")
                if category_match and position_match:
                    return f(*args, **kwargs)
                return False

            return wrapper

        return decorated

    @staticmethod
    @meta(position="Post", category="Exclusion")
    def exclude_female_from_Immobilisations(
        emp: Employee,
        dept: TrainingDepartment,
    ) -> bool:
        if emp.sexe == "F" and dept.name == "Immobilisations":
            return True
        return False

    @staticmethod
    @meta(position="Pre", category="Operation")
    def cannot_move_more_than_limit(
        emp: Employee, dept: TrainingDepartment, limit: int
    ) -> bool:
        limit = min(limit, dept.max_capacity)
        if dept._rotation_movement.count("-") >= limit:
            return True
        return False

    @staticmethod
    @meta(position="Post", category="Operation")
    def train_once_in_each_dept(emp: Employee, dept: TrainingDepartment) -> bool:
        if dept in (d[0] for d in emp.previous_departments):
            return True
        return False
