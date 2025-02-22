from pathlib import Path
from dataclasses import dataclass


@dataclass
class Config:
    INPUT_FOLDER = Path().home() / "employee_rotation"
    OUTPUT_FOLDER = Path().home() / "employee_rotation"
    rotations = 500
    delay_start_by_months = 2
    rotation_length_in_months = 1.01

    def __post_init__(self):
        for folder in [self.INPUT_FOLDER, self.OUTPUT_FOLDER]:
            folder.mkdir(exist_ok=True, parents=True)
