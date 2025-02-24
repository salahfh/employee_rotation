from pathlib import Path

import polars as pl


date_format_fr = "%d/%m/%Y"
date_format_en = "%m/%d/%Y"


def load_data(input_file: Path):
    df = pl.scan_csv(input_file).select(
        pl.col("Nom").alias("first_name"),
        pl.col("Prénom").alias("last_name"),
        pl.col("Sexe").alias("gender"),
        pl.col("Date Recrutement").str.to_datetime(date_format_en).alias("start_date"),
        pl.col("Section").alias("current_department"),
        pl.col("Durée Par section").alias("duration_months"),
        pl.col("Durée Par section").count().over("Section").alias("max_capacity"),
    )

    department = (
        df.group_by(pl.col("current_department"))
        .agg(pl.col("duration_months").max(), pl.col("max_capacity").max())
        .collect()
    )

    employees = df.select(
        pl.col("first_name"),
        pl.col("last_name"),
        pl.col("gender"),
        pl.col("start_date"),
        pl.col("current_department"),
    ).collect()

    return department, employees


def write_data(file: Path, data: list[str], clean=False):
    if not clean:
        data = clean_up_output(data)
    with open(file, "w") as f:
        for line in data:
            f.write(line)
            f.write("\n")


def clean_up_output(lines):
    """
    Remove the extra white line and add one when necessary
    """
    prev_line = lines[0]
    new_lines = [prev_line]
    for line in lines[1:]:
        if line == "\n" and prev_line == "\n":
            continue
        if not prev_line.startswith("  ") and line.startswith("  "):
            new_lines.append("\n")
        prev_line = line
        new_lines.append(line)
    return new_lines


if __name__ == "__main__":
    path = Path().home() / 'employee_rotation' / 'data.csv'
    dept, emp = load_data(path)
    print(dept)
    print(emp)
