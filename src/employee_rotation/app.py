from employee_rotation.config import Config
from employee_rotation.models import (
    TrainingDepartment,
    Employee,
    TimeSimulator,
    rotate_employees,
)
from employee_rotation.load_data import load_data


def main():
    config = Config()
    t_simulator = TimeSimulator()

    departments_df, employees_df = load_data(config.INPUT_FOLDER / "data.csv")

    departements: list[TrainingDepartment] = []
    employees: list[Employee] = []

    for row in departments_df.iter_rows():
        dept = TrainingDepartment(*row)
        dept.time_simulator = t_simulator
        departements.append(dept)

    for row in employees_df.iter_rows():
        emp = Employee.new(row, departments=departements)
        emp.time_simulator = t_simulator
        employees.append(emp)

    for index in range(config.rotations):
        t_simulator.forward_in_future(config.rotation_length_in_months)
        employees = rotate_employees(employees, departements)

        for dept in departements:
            print(
                f"{t_simulator.now().strftime('%Y-%m')} "
                f"{dept.name.rjust(15)} "
                f"({dept.current_capacity}/{dept.max_capacity}): "
                f"{[emp.full_name for emp in dept.employees]} "
            )
        print()


if __name__ == "__main__":
    pass
