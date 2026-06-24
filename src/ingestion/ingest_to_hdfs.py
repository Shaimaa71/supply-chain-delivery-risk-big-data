
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_INPUT_DIR = PROJECT_ROOT / "data" / "local_input"
LOG_DIR = PROJECT_ROOT / "logs" / "ingestion"
CONTAINER_NAME = "namenode"
DEFAULT_HDFS_DIR = "/user/bigdata/supply_chain/raw"
DEFAULT_HDFS_FILENAME = "dataco_supply_chain.csv"


def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def find_csv_file():
    csv_files = list(LOCAL_INPUT_DIR.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in {LOCAL_INPUT_DIR}")
    if len(csv_files) > 1:
        names = "\n".join(str(file) for file in csv_files)
        raise RuntimeError(f"More than one CSV file found. Please pass --file.\n{names}")
    return csv_files[0]


def detect_encoding(file_path):
    encodings = ["utf-8", "utf-8-sig", "latin1", "ISO-8859-1", "windows-1252"]
    for encoding in encodings:
        try:
            pd.read_csv(file_path, nrows=5, encoding=encoding)
            return encoding
        except Exception:
            continue
    raise RuntimeError("Could not detect a suitable encoding for the CSV file.")


def inspect_csv(file_path, encoding):
    row_count = 0
    column_count = 0
    columns = []

    chunks = pd.read_csv(file_path, encoding=encoding, chunksize=50000, low_memory=False)
    for index, chunk in enumerate(chunks):
        row_count += len(chunk)
        if index == 0:
            column_count = len(chunk.columns)
            columns = list(chunk.columns)

    return row_count, column_count, columns


def ensure_hdfs_directory(hdfs_dir):
    run_command([
        "docker", "exec", CONTAINER_NAME,
        "hdfs", "dfs", "-mkdir", "-p", hdfs_dir
    ])


def upload_to_hdfs(local_file, hdfs_dir, hdfs_filename):
    temp_container_path = f"/tmp/{hdfs_filename}"
    hdfs_target_path = f"{hdfs_dir}/{hdfs_filename}"

    run_command([
        "docker", "cp",
        str(local_file),
        f"{CONTAINER_NAME}:{temp_container_path}"
    ])

    run_command([
        "docker", "exec", CONTAINER_NAME,
        "hdfs", "dfs", "-put", "-f",
        temp_container_path,
        hdfs_target_path
    ])

    run_command([
        "docker", "exec", CONTAINER_NAME,
        "rm", "-f", temp_container_path
    ])

    return hdfs_target_path


def verify_hdfs_file(hdfs_path):
    output = run_command([
        "docker", "exec", CONTAINER_NAME,
        "hdfs", "dfs", "-ls", hdfs_path
    ])
    return output


def write_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"ingestion_log_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4, ensure_ascii=False)

    return log_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--hdfs-dir", type=str, default=DEFAULT_HDFS_DIR)
    parser.add_argument("--hdfs-name", type=str, default=DEFAULT_HDFS_FILENAME)
    args = parser.parse_args()

    start_time = datetime.now()

    if args.file:
        local_file = Path(args.file).resolve()
    else:
        local_file = find_csv_file()

    if not local_file.exists():
        raise FileNotFoundError(f"File not found: {local_file}")

    encoding = detect_encoding(local_file)
    row_count, column_count, columns = inspect_csv(local_file, encoding)

    ensure_hdfs_directory(args.hdfs_dir)
    hdfs_path = upload_to_hdfs(local_file, args.hdfs_dir, args.hdfs_name)
    hdfs_check_output = verify_hdfs_file(hdfs_path)

    end_time = datetime.now()

    log_data = {
        "status": "success",
        "source_file": str(local_file),
        "hdfs_path": hdfs_path,
        "file_size_mb": round(local_file.stat().st_size / (1024 * 1024), 2),
        "encoding": encoding,
        "row_count": row_count,
        "column_count": column_count,
        "columns": columns,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2),
        "hdfs_check_output": hdfs_check_output
    }

    log_file = write_log(log_data)

    print("Data ingestion completed successfully.")
    print(f"Source file: {local_file}")
    print(f"HDFS path: {hdfs_path}")
    print(f"Rows: {row_count}")
    print(f"Columns: {column_count}")
    print(f"Encoding: {encoding}")
    print(f"Log file: {log_file}")
    print("HDFS verification:")
    print(hdfs_check_output)


if __name__ == "__main__":
    main()