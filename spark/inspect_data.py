from pathlib import Path
import pandas as pd

FILE_PATH = Path("data/raw/population.csv")


def main():
    if not FILE_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {FILE_PATH}\n"
            "Copy your dataset into data/raw/population.csv"
        )

    df = pd.read_csv(FILE_PATH)

    if df.empty:
        raise ValueError("Dataset is empty.")

    print("\n========== DATASET OVERVIEW ==========")
    print(f"File: {FILE_PATH}")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Duplicate complete rows: {df.duplicated().sum()}")

    print("\n========== COLUMN NAMES ==========")
    for column in df.columns:
        print(column)

    print("\n========== MISSING VALUES ==========")
    missing = df.isnull().sum()
    report = pd.DataFrame({
        "Missing_Count": missing,
        "Missing_Percentage": (
            missing / len(df) * 100
        ).round(2)
    })
    print(report[report["Missing_Count"] > 0].to_string())

    print("\n========== DISTRICT NAMES ==========")
    if "District" in df.columns:
        print(df["District"].to_string(index=False))
        print(
            "Unique districts:",
            df["District"].nunique()
        )
    else:
        print("WARNING: District column not found.")

    print("\n========== DATA TYPES ==========")
    print(df.dtypes.to_string())

    print("\n========== FIRST 5 RECORDS ==========")
    print(df.head().to_string(index=False))

    print("\nInspection completed.")


if __name__ == "__main__":
    main()
