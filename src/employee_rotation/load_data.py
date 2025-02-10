from pathlib import Path

import polars as pl


date_format_fr = "%d/%m/%Y"
date_format_en = "%m/%d/%Y"


def load_data(input_folder: Path):
    df = pl.scan_csv(input_folder, skip_rows=1).select(
        pl.col("Nom").alias("first_name"),
        pl.col("Prénom").alias("last_name"),
        pl.col("Date Recrutement").str.to_datetime(date_format_en).alias("start_date"),
        pl.col("Section").alias("current_department"),
        pl.when(pl.col("Durée Par section").str.head(1).cast(pl.Int32) == 1)
        .then(12)
        .otherwise(6)
        .alias("duration_months"),
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
        pl.col("start_date"),
        pl.col("current_department"),
    ).collect()

    return department, employees


if __name__ == "__main__":
    print(load_data("/home/salah/employee_rotation/data.csv"))
