from employee_rotation.config import Config
from employee_rotation.models import (
    TrainingDepartment,
    Employee,
    Rules,
    TimeSimulator,
    rotate_employees,
    Status,
)
from employee_rotation.data import load_data, write_data


def main():
    config = Config()
    t_simulator = TimeSimulator()
    rules = Rules().add_rules(config.rules)

    departments_df, employees_df = load_data(config.INPUT_FOLDER / "data.csv")

    departements: list[TrainingDepartment] = []
    employees: list[Employee] = []
    lines = []

    # initilize objects
    for row in departments_df.iter_rows():
        dept = TrainingDepartment(*row)
        dept.time_simulator = t_simulator
        departements.append(dept)

    for row in employees_df.iter_rows():
        emp = Employee.new(row, departments=departements)
        emp.time_simulator = t_simulator
        employees.append(emp)

    # Before ratation
    produce_rotation_output(departements, employees, lines)

    # start delayed by month
    t_simulator.forward_in_future(config.delay_start_by_months)

    # rotate employees
    for _ in range(config.rotations):
        t_simulator.forward_in_future(config.rotation_length_in_months)
        employees = rotate_employees(employees, departements, rules)

        produce_rotation_output(departements, employees, lines)

    write_data(config.OUTPUT_FOLDER / "plan.txt", lines)


def produce_rotation_output(
    departements: list[TrainingDepartment],
    employees: list[Employee],
    lines: list[str],
):
    departements_formating = format_depatements_output(departements)
    lines.extend(departements_formating)
    lines.extend(format_employees_output(employees))

    if len(departements_formating):
        lines.extend(format_employees_summary_output(employees))
        lines.extend(format_departments_summary_output(departements))

        lines.append("\n")
        lines.append("-----" * 20)


def format_employees_output(
    employees: list[Employee],
) -> list[str]:
    """
    Helper function for output formatting for employees
    """
    lines = []
    for emp in employees:
        if not emp._changed:
            continue

        match emp.status:
            case Status.WAITING_REASSIGNMENT:
                action = "Waiting Reassignment"
                dept = emp.previous_departments[-1][1].name
                indicator = "<-"
            
            case Status.ASSIGNED:
                action = "Waiting Reassignment"
                action = "Assigned"
                dept = emp.current_department.name  # type: ignore
                indicator = "->"

            case Status.FINISHED:
                action = "Training Completed"
                dept = "Finished"
                indicator = "**"

            case _:
                raise NotImplementedError("Status case not implemented")

        message = (
            f"{action.rjust(30)}: {emp.full_name.ljust(30, '.')} {indicator} {dept}"
        )

        lines.append(message)

    return lines


def format_depatements_output(departements: list[TrainingDepartment]) -> list[str]:
    """
    Helper function for output formatting for departements
    """

    lines = []
    for dept in sorted(departements, key=lambda dept: dept.max_capacity):
        if not dept._rotation_movement:
            continue

        lines.append(
            f"{dept.time_simulator.now().strftime('%Y-%m')} "
            f"{dept.name.rjust(16)} "
            f"({dept.current_capacity}/{dept.max_capacity}): "
            f"{sorted([emp.full_name for emp in dept.employees])} "
            f"({dept._rotation_movement.count('-')}-/"
            f"{dept._rotation_movement.count('+')}+)"
        )
    return lines


def format_departments_summary_output(
    departements: list[TrainingDepartment],
) -> list[str]:
    lines = []
    max_capacity = sum(dept.max_capacity for dept in departements)
    occupied_capacity = sum(dept.current_capacity for dept in departements)
    empty_sport = max_capacity - occupied_capacity
    summary = (
        "\n"
        f"{'Departments summary'.rjust(30)}:"
        f" {occupied_capacity} Occupied /"
        f" {empty_sport} Empty /"
        f" {max_capacity} Max Capacity "
    )
    lines.append(summary)
    return lines


def format_employees_summary_output(
    employees: list[Employee],
) -> list[str]:
    lines = []

    finished = sum(1 for emp in employees if emp.status is Status.FINISHED)
    waiting = sum(1 for emp in employees if emp.status is Status.WAITING_REASSIGNMENT)
    assigned = sum(1 for emp in employees if emp.status is Status.ASSIGNED)
    summary = (
        "\n"
        f"{'Employees summary'.rjust(30)}: {waiting} Waiting /  {assigned} Assigned / {finished} Finished"
    )
    lines.append(summary)

    return lines


if __name__ == "__main__":
    main()
