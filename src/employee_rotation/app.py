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

    plan_per_emp = employees_training_plan(employees)

    write_data(config.OUTPUT_FOLDER / "plan.txt", lines)
    write_data(config.OUTPUT_FOLDER / "plan_per_emp.txt", plan_per_emp, clean=True)


def produce_rotation_output(
    departements: list[TrainingDepartment],
    employees: list[Employee],
    lines: list[str],
):
    departements_formating = format_depatements_output(departements)
    lines.extend(departements_formating)
    lines.extend(format_employees_output(employees))

    if len(departements_formating):
        # lines.extend(format_employees_summary_output(employees))
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
                try:
                    dept = emp.previous_departments[-1][0].name
                except IndexError:
                    dept = emp.current_department.name  # type: ignore
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
            f"{action.rjust(32)}: {emp.full_name.ljust(30, '.')} {indicator} {dept}"
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

        # actual_capacity = len(dept.non_training_employees) + len(dept.employees)
        wait_reassignment = len(dept.waiting_reassignment)

        lines.append(
            f"{dept.time_simulator.now().strftime('%Y-%m')} "
            f"{dept.name.rjust(16)} "
            f"({dept.current_capacity}/{dept.max_capacity}/{wait_reassignment}): "
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
    training = sum(dept.current_capacity for dept in departements)
    wait_reassignment = sum(len(dept.waiting_reassignment) for dept in departements)
    finished = sum(len(dept.finished) for dept in departements)
    summary = (
        "\n"
        f"{'Departments summary'.rjust(32)}:"
        f" {training} Training /"
        f" {wait_reassignment} Waiting Reassignment /"
        f" {finished} Finished /"
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
        f"{'Employees summary'.rjust(32)}: {waiting} Waiting /  {assigned} Assigned / {finished} Finished"
    )
    lines.append(summary)

    return lines


def employees_training_plan(
    employees: list[Employee],
) -> list[str]:
    plan = []
    for i, emp in enumerate(employees):
        plan.extend(
            [
                ",".join(
                    (
                        str(i + 1),
                        emp.full_name,
                        entry[0].name,
                        entry[1].strftime("%Y-%m"),
                        entry[2].strftime("%Y-%m"),
                    )
                )
                for entry in emp.previous_departments
            ]
        )

    return plan


if __name__ == "__main__":
    main()
