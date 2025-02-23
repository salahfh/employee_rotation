from employee_rotation.config import Config
from employee_rotation.models import (
    TrainingDepartment,
    Employee,
    FilterRules,
    TimeSimulator,
    rotate_employees,
)
from employee_rotation.data import load_data, write_data


def main():
    config = Config()
    t_simulator = TimeSimulator()
    filters = (
        FilterRules()
        .add_filters(config.exclution_filters, filter_type="Exclusion")
        .add_filters(config.operation_filters, filter_type="Operation")
    )

    departments_df, employees_df = load_data(config.INPUT_FOLDER / "data.csv")

    departements: list[TrainingDepartment] = []
    employees: list[Employee] = []
    lines = []

    # initilize objects
    for row in departments_df.iter_rows():
        dept = TrainingDepartment(*row)
        dept.time_simulator = t_simulator
        departements.append(dept)
    departements_track = {dept.name: dept.hash for dept in departements}

    for row in employees_df.iter_rows():
        emp = Employee.new(row, departments=departements)
        emp.time_simulator = t_simulator
        employees.append(emp)
    employees_track = {
        emp.full_name: (emp.hash, emp.current_department) for emp in employees
    }

    # Before ratation
    produce_rotation_output(
        departements, employees, lines, departements_track, employees_track
    )

    # start delayed by month
    t_simulator.forward_in_future(config.delay_start_by_months)

    # rotate employees
    for _ in range(config.rotations):
        t_simulator.forward_in_future(config.rotation_length_in_months)
        employees = rotate_employees(employees, departements, filters)

        produce_rotation_output(
            departements, employees, lines, departements_track, employees_track
        )

    write_data(config.OUTPUT_FOLDER / "plan.txt", lines)


def produce_rotation_output(
    departements: list[TrainingDepartment],
    employees: list[Employee],
    lines: list[str],
    departements_track: dict,
    employees_track: dict,
):
    departements_formating = format_depatements_output(departements, departements_track)
    lines.extend(departements_formating)
    lines.extend(format_employees_output(employees, employees_track, departements))

    if len(departements_formating):
        lines.extend(format_employees_summary_output(employees, departements))

        lines.append("\n")
        lines.append("-----" * 20)


def format_employees_output(
    employees: list[Employee],
    employees_track: dict,
    departements: list[TrainingDepartment],
) -> list[str]:
    """
    Helper function for output formatting for employees
    """
    lines = []
    for emp in employees:
        if employees_track[emp.full_name][0] == emp.hash:
            continue
        else:
            if emp.current_department is None:
                action = "Waiting Reassignment"
                dept = employees_track[emp.full_name][1].name
                indicator = "<-"

            else:
                action = "Assigned"
                dept = emp.current_department.name
                indicator = "->"

            if len(emp.previous_departments) + len(emp.excluded_departments) == len(
                departements
            ):
                action = "Training Completed"
                dept = "Finished"
                indicator = "**"

            message = (
                f"{action.rjust(30)}: {emp.full_name.ljust(30, '.')} {indicator} {dept}"
            )

            lines.append(message)
            employees_track[emp.full_name] = (emp.hash, emp.current_department)

    return lines


def format_depatements_output(
    departements: list[TrainingDepartment], departements_track: dict
) -> list[str]:
    """
    Helper function for output formatting for departements
    """

    lines = []
    for dept in sorted(departements, key=lambda dept: dept.max_capacity):
        if departements_track[dept.name] == dept.hash:
            continue

        lines.append(
            f"{dept.time_simulator.now().strftime('%Y-%m')} "
            f"{dept.name.rjust(16)} "
            f"({dept.current_capacity}/{dept.max_capacity}): "
            f"{sorted([emp.full_name for emp in dept.employees])} "
            f"({dept._rotation_movement.count('-')}-/"
            f"{dept._rotation_movement.count('+')}+)"
        )
        departements_track[dept.name] = dept.hash
    return lines


def format_employees_summary_output(
    employees: list[Employee],
    departements: list[TrainingDepartment],
) -> list[str]:
    lines = []

    finished = sum(
        (
            1
            for emp in employees
            if len(emp.previous_departments) + len(emp.excluded_departments)
            == len(departements)
        )
    )
    waiting = abs(
        sum((1 for emp in employees if emp.current_department is None)) - finished
    )
    assigned = sum(1 for emp in employees if emp.current_department is not None)
    summary = (
        "\n"
        f"{'Employees summary'.rjust(30)}: {waiting} Waiting /  {assigned} Assigned / {finished} Finished"
    )
    lines.append(summary)

    return lines


if __name__ == "__main__":
    main()
