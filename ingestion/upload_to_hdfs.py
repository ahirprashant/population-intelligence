from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys

SOURCE_FILE = Path("data/raw/population.csv")

HDFS_RAW = "/government-data/raw"
HDFS_PROCESSED = "/government-data/processed"
HDFS_ARCHIVE = "/government-data/archive"

METADATA_DIR = Path("logs")
METADATA_FILE = METADATA_DIR / "ingestion_metadata.json"


def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"{result.stderr}"
        )

    return result.stdout


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {SOURCE_FILE}"
        )

    if SOURCE_FILE.stat().st_size == 0:
        raise ValueError("Dataset file is empty.")

    # Validate CSV structure and row count.
    import pandas as pd

    df = pd.read_csv(SOURCE_FILE)

    if df.empty:
        raise ValueError("CSV contains no data rows.")

    if "District" not in df.columns:
        raise ValueError("Required column 'District' is missing.")

    # Create HDFS directories.
    for directory in (
        HDFS_RAW,
        HDFS_PROCESSED,
        HDFS_ARCHIVE
    ):
        run_command([
            "hdfs", "dfs", "-mkdir", "-p", directory
        ])

    # Upload the raw file.
    destination = f"{HDFS_RAW}/population.csv"

    run_command([
        "hdfs", "dfs", "-put", "-f",
        str(SOURCE_FILE),
        destination
    ])

    # Verify uploaded file.
    listing = run_command([
        "hdfs", "dfs", "-ls", destination
    ])

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {
        "filename": SOURCE_FILE.name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "file_size_bytes": SOURCE_FILE.stat().st_size,
        "source_url": None,
        "source_verification": "Pending",
        "fetch_timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "hdfs_path": destination,
        "upload_status": "SUCCESS"
    }

    METADATA_FILE.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )

    print("HDFS upload successful.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"HDFS path: {destination}")
    print(f"Metadata: {METADATA_FILE}")
    print(listing)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
