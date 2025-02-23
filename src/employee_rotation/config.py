from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    INPUT_FOLDER = Path().home() / "employee_rotation"
    OUTPUT_FOLDER = Path().home() / "employee_rotation"
    years_of_plan = 25
    rotations = years_of_plan * 12
    delay_start_by_months = 2
    rotation_length_in_months = 1.01
    exclution_filters = ["exclude_female_from_Immobilisations"]
    operation_filters = [
        # ("cannot_move_more_than_limit", {"limit": 1})
        ]

    def __post_init__(self):
        for folder in [self.INPUT_FOLDER, self.OUTPUT_FOLDER]:
            folder.mkdir(exist_ok=True, parents=True)
