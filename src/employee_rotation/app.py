from employee_rotation.config import Config
from employee_rotation.models import (
    TrainingDepartment,
    Employee,
    TimeSimulator,
    rotate_employees,
)
from employee_rotation.data import load_data, write_data


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
                message = f"  Removed  {emp.full_name.ljust(30, '.')} from {employees_track[emp.full_name][1].name}"
            else:
                message = f"  Assigned {emp.full_name.ljust(30, '.')} to {emp.current_department.name}"

            if len(emp.previous_departments) == len(departements):
                message = f"  ** Training Completed for {emp.full_name} **"

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
        else:
            departements_track[dept.name] = dept.hash

            lines.append(
                f"{dept.time_simulator.now().strftime('%Y-%m')} "
                f"{dept.name.rjust(15)} "
                f"({dept.current_capacity}/{dept.max_capacity}): "
                f"{sorted([emp.full_name for emp in dept.employees])} "
            )
    return lines


def main():
    config = Config()
    t_simulator = TimeSimulator()

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
        emp.start_date = t_simulator.offset_month_randomly(emp.start_date)  # type: ignore
        employees.append(emp)
    employees_track = {
        emp.full_name: (emp.hash, emp.current_department) for emp in employees
    }

    # rotate employees
    for _ in range(config.rotations):
        t_simulator.forward_in_future(config.rotation_length_in_months)
        employees = rotate_employees(employees, departements)

        departements_formating = format_depatements_output(
            departements, departements_track
        )
        lines.extend(departements_formating)
        lines.extend(format_employees_output(employees, employees_track, departements))

        if len(departements_formating):
            lines.append("\n")
            lines.append("-----" * 20)

    prev_line = lines[0]
    new_lines = []
    for line in lines[1:]:
        if line == "\n" and prev_line == "\n":
            continue
        if not prev_line.startswith("  ") and line.startswith("  "):
            new_lines.append("\n")
        prev_line = line
        new_lines.append(line)

    write_data(config.OUTPUT_FOLDER / "plan.txt", new_lines)


if __name__ == "__main__":
    pass
