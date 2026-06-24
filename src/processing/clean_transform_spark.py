import json
import os
import re
from datetime import datetime
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    trim,
    lower,
    regexp_replace,
    to_timestamp,
    year,
    month,
    dayofweek,
    when,
    lit
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "processing"

HDFS_INPUT_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/silver/privacy_safe_orders.parquet"
HDFS_OUTPUT_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/silver/clean_orders.parquet"


SPECIAL_COLUMN_NAMES = {
    "order date (dateorders)": "order_date",
    "shipping date (dateorders)": "shipping_date",
    "days for shipping (real)": "days_for_shipping_real",
    "days for shipment (scheduled)": "days_for_shipment_scheduled",
    "late_delivery_risk": "late_delivery_risk"
}


NUMERIC_COLUMNS = [
    "days_for_shipping_real",
    "days_for_shipment_scheduled",
    "benefit_per_order",
    "sales_per_customer",
    "late_delivery_risk",
    "category_id",
    "customer_id",
    "department_id",
    "latitude",
    "longitude",
    "order_customer_id",
    "order_id",
    "order_item_cardprod_id",
    "order_item_discount",
    "order_item_discount_rate",
    "order_item_id",
    "order_item_product_price",
    "order_item_profit_ratio",
    "order_item_quantity",
    "sales",
    "order_item_total",
    "order_profit_per_order",
    "order_zipcode",
    "product_card_id",
    "product_category_id",
    "product_price",
    "product_status"
]


CATEGORICAL_COLUMNS = [
    "type",
    "delivery_status",
    "category_name",
    "customer_city",
    "customer_country",
    "customer_segment",
    "customer_state",
    "department_name",
    "market",
    "order_city",
    "order_country",
    "order_region",
    "order_state",
    "order_status",
    "product_name",
    "shipping_mode"
]


def create_spark_session():
    os.environ["HADOOP_USER_NAME"] = "root"

    spark = (
        SparkSession.builder
        .appName("SupplyChainCleanTransform")
        .master("local[*]")
        .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark


def clean_column_name(name):
    original = name.strip()
    key = original.lower()

    if key in SPECIAL_COLUMN_NAMES:
        return SPECIAL_COLUMN_NAMES[key]

    cleaned = original.lower()
    cleaned = cleaned.replace("(", "")
    cleaned = cleaned.replace(")", "")
    cleaned = cleaned.replace("/", "_")
    cleaned = cleaned.replace("-", "_")
    cleaned = cleaned.replace(".", "")
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    cleaned = cleaned.strip("_")

    return cleaned


def make_unique_columns(columns):
    seen = {}
    unique_columns = []

    for column in columns:
        if column not in seen:
            seen[column] = 0
            unique_columns.append(column)
        else:
            seen[column] += 1
            unique_columns.append(f"{column}_{seen[column]}")

    return unique_columns


def rename_columns(df):
    original_columns = df.columns
    cleaned_columns = [clean_column_name(column) for column in original_columns]
    unique_columns = make_unique_columns(cleaned_columns)

    renamed_df = df
    for old_name, new_name in zip(original_columns, unique_columns):
        renamed_df = renamed_df.withColumnRenamed(old_name, new_name)

    column_mapping = {
        old_name: new_name
        for old_name, new_name in zip(original_columns, unique_columns)
    }

    return renamed_df, column_mapping


def clean_numeric_column(column_name):
    return (
        regexp_replace(
            trim(col(column_name).cast("string")),
            r"[^0-9\.\-]",
            ""
        ).cast("double")
    )


def write_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"clean_transform_log_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4, ensure_ascii=False)

    return log_file


def main():
    start_time = datetime.now()
    spark = create_spark_session()

    df = spark.read.parquet(HDFS_INPUT_PATH)

    rows_before = df.count()
    columns_before = df.columns
    column_count_before = len(columns_before)

    df, column_mapping = rename_columns(df)

    for column_name in CATEGORICAL_COLUMNS:
        if column_name in df.columns:
            df = df.withColumn(
                column_name,
                when(
                    trim(col(column_name).cast("string")).isNull() |
                    (trim(col(column_name).cast("string")) == ""),
                    lit("Unknown")
                ).otherwise(trim(col(column_name).cast("string")))
            )

    for column_name in NUMERIC_COLUMNS:
        if column_name in df.columns:
            df = df.withColumn(column_name, clean_numeric_column(column_name))

    if "order_date" in df.columns:
        df = df.withColumn(
            "order_date",
            to_timestamp(col("order_date").cast("string"), "M/d/yyyy H:mm")
        )

    if "shipping_date" in df.columns:
        df = df.withColumn(
            "shipping_date",
            to_timestamp(col("shipping_date").cast("string"), "M/d/yyyy H:mm")
        )

    rows_before_duplicates = df.count()
    df = df.dropDuplicates()
    rows_after_duplicates = df.count()
    duplicates_removed = rows_before_duplicates - rows_after_duplicates

    if "days_for_shipping_real" in df.columns and "days_for_shipment_scheduled" in df.columns:
        df = df.withColumn(
            "shipping_delay_days",
            col("days_for_shipping_real") - col("days_for_shipment_scheduled")
        )

    if "order_profit_per_order" in df.columns and "sales" in df.columns:
        df = df.withColumn(
            "profit_margin",
            when(col("sales") != 0, col("order_profit_per_order") / col("sales"))
            .otherwise(lit(None))
        )

    if "order_profit_per_order" in df.columns:
        df = df.withColumn(
            "is_loss_order",
            when(col("order_profit_per_order") < 0, lit(1)).otherwise(lit(0))
        )

    if "order_item_discount_rate" in df.columns:
        df = df.withColumn(
            "discount_level",
            when(col("order_item_discount_rate").isNull(), lit("Unknown"))
            .when(col("order_item_discount_rate") == 0, lit("No Discount"))
            .when(col("order_item_discount_rate") <= 0.05, lit("Low"))
            .when(col("order_item_discount_rate") <= 0.15, lit("Medium"))
            .otherwise(lit("High"))
        )

    if "sales" in df.columns:
        quantiles = df.approxQuantile("sales", [0.33, 0.66], 0.01)
        low_sales_threshold = quantiles[0]
        high_sales_threshold = quantiles[1]

        df = df.withColumn(
            "sales_level",
            when(col("sales").isNull(), lit("Unknown"))
            .when(col("sales") <= low_sales_threshold, lit("Low"))
            .when(col("sales") <= high_sales_threshold, lit("Medium"))
            .otherwise(lit("High"))
        )
    else:
        low_sales_threshold = None
        high_sales_threshold = None

    if "order_date" in df.columns:
        df = df.withColumn("order_year", year(col("order_date")))
        df = df.withColumn("order_month", month(col("order_date")))
        df = df.withColumn("order_day_of_week", dayofweek(col("order_date")))

    rows_after = df.count()
    column_count_after = len(df.columns)

    selected_null_columns = [
        column_name for column_name in [
            "order_date",
            "shipping_date",
            "sales",
            "order_profit_per_order",
            "late_delivery_risk",
            "shipping_mode",
            "market",
            "order_region",
            "category_name"
        ] if column_name in df.columns
    ]

    null_summary = {}
    for column_name in selected_null_columns:
        null_count = df.filter(col(column_name).isNull()).count()
        null_summary[column_name] = null_count

    df.coalesce(4).write.mode("overwrite").parquet(HDFS_OUTPUT_PATH)

    end_time = datetime.now()

    created_features = [
        feature for feature in [
            "shipping_delay_days",
            "profit_margin",
            "is_loss_order",
            "discount_level",
            "sales_level",
            "order_year",
            "order_month",
            "order_day_of_week"
        ] if feature in df.columns
    ]

    log_data = {
        "status": "success",
        "input_path": HDFS_INPUT_PATH,
        "output_path": HDFS_OUTPUT_PATH,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "columns_before": column_count_before,
        "columns_after": column_count_after,
        "duplicates_removed": duplicates_removed,
        "created_features": created_features,
        "sales_level_thresholds": {
            "low_sales_threshold": low_sales_threshold,
            "high_sales_threshold": high_sales_threshold
        },
        "null_summary": null_summary,
        "column_mapping": column_mapping,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2)
    }

    log_file = write_log(log_data)

    print("Spark cleaning and feature engineering completed successfully.")
    print(f"Input path: {HDFS_INPUT_PATH}")
    print(f"Output path: {HDFS_OUTPUT_PATH}")
    print(f"Rows before: {rows_before}")
    print(f"Rows after: {rows_after}")
    print(f"Columns before: {column_count_before}")
    print(f"Columns after: {column_count_after}")
    print(f"Duplicates removed: {duplicates_removed}")
    print("Created features:")
    for feature in created_features:
        print(f"- {feature}")
    print("Selected null summary:")
    for column_name, null_count in null_summary.items():
        print(f"- {column_name}: {null_count}")
    print(f"Log file: {log_file}")

    spark.stop()


if __name__ == "__main__":
    main()