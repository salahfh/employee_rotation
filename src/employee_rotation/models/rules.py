from __future__ import annotations
from typing import TYPE_CHECKING, Literal, Self, Any
from functools import partial

if TYPE_CHECKING:
    from employee_rotation.models.employee import Employee, TrainingDepartment


class FilterRules:
    """
    Apply filter rules.

    Operation rules are conserned with delaying the action.
    Excelution rules are for permenat actions.
    """

    def __init__(
        self,
    ) -> None:
        self.exclusion_filters = list()
        self.operational_filters = list()

    def check(
        self,
        emp: Employee,
        dept: TrainingDepartment,
        *,
        filter_type: Literal["Exclusion", "Operation"],
    ) -> bool:
        filters = (
            self.exclusion_filters
            if filter_type == "Exclusion"
            else self.operational_filters
        )
        for fltr in filters:
            if fltr(emp, dept):
                return True
        return False

    def add_filters(
        self,
        filter_item: list[str] | list[tuple[str, dict[str, Any]]],
        *,
        filter_type: Literal["Exclusion", "Operation"],
    ) -> Self:
        filters = (
            self.exclusion_filters
            if filter_type == "Exclusion"
            else self.operational_filters
        )
        for item in filter_item:
            match item:
                case f_name, kwargs:
                    f_name = f_name
                    kwargs = kwargs
                case f_name:
                    f_name = f_name
                    kwargs = {}

            if f_name is None:
                raise ValueError(
                    f"{f_name} is not a valid filter. please change your configration"
                )

            filter_func = partial(getattr(self, f_name), **kwargs)
            filters.append(filter_func)

        return self

    @staticmethod
    def exclude_female_from_Immobilisations(
        emp: Employee,
        dept: TrainingDepartment,
    ) -> bool:
        if emp.sexe == "F" and dept.name == "Immobilisations":
            return True
        return False

    @staticmethod
    def cannot_move_more_than_limit(
        emp: Employee, dept: TrainingDepartment, limit: int
    ) -> bool:
        limit = min(limit, dept.max_capacity)
        if dept._rotation_movement.count("+") > limit - 1:
            return True
        return False
