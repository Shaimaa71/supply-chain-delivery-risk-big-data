import json
import os
from datetime import datetime
from pathlib import Path

from pyspark.sql import SparkSession


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "processing"

HDFS_RAW_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/raw/dataco_supply_chain.csv"
HDFS_OUTPUT_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/silver/privacy_safe_orders.parquet"

PRIVACY_COLUMNS = [
    "Customer Email",
    "Customer Password",
    "Customer Fname",
    "Customer Lname",
    "Customer Street",
    "Customer Zipcode",
    "Product Image",
    "Product Description"
]


def create_spark_session():
    os.environ["HADOOP_USER_NAME"] = "root"

    spark = (
    SparkSession.builder
    .appName("SupplyChainPrivacyCleaning")
    .master("local[*]")
    .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000")
    .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark


def write_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"privacy_cleaning_log_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4, ensure_ascii=False)

    return log_file


def main():
    start_time = datetime.now()
    spark = create_spark_session()

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .option("encoding", "ISO-8859-1")
        .csv(HDFS_RAW_PATH)
    )

    rows_before = df.count()
    columns_before = df.columns
    column_count_before = len(columns_before)

    existing_privacy_columns = [column for column in PRIVACY_COLUMNS if column in columns_before]
    missing_privacy_columns = [column for column in PRIVACY_COLUMNS if column not in columns_before]

    privacy_safe_df = df.drop(*existing_privacy_columns)

    rows_after = privacy_safe_df.count()
    columns_after = privacy_safe_df.columns
    column_count_after = len(columns_after)

    privacy_safe_df.write.mode("overwrite").parquet(HDFS_OUTPUT_PATH)

    end_time = datetime.now()

    log_data = {
        "status": "success",
        "input_path": HDFS_RAW_PATH,
        "output_path": HDFS_OUTPUT_PATH,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "column_count_before": column_count_before,
        "column_count_after": column_count_after,
        "dropped_columns": existing_privacy_columns,
        "missing_privacy_columns": missing_privacy_columns,
        "remaining_columns": columns_after,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2)
    }

    log_file = write_log(log_data)

    print("Privacy cleaning completed successfully.")
    print(f"Input path: {HDFS_RAW_PATH}")
    print(f"Output path: {HDFS_OUTPUT_PATH}")
    print(f"Rows before: {rows_before}")
    print(f"Rows after: {rows_after}")
    print(f"Columns before: {column_count_before}")
    print(f"Columns after: {column_count_after}")
    print("Dropped privacy columns:")
    for column in existing_privacy_columns:
        print(f"- {column}")
    print(f"Log file: {log_file}")

    spark.stop()


if __name__ == "__main__":
    main()