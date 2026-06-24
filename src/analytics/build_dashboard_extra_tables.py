import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, countDistinct, lit, sum as spark_sum, when
from sqlalchemy import create_engine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "analytics"

HDFS_INPUT_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/silver/clean_orders.parquet"
HDFS_GOLD_BASE_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/gold"


def create_spark_session():
    os.environ["HADOOP_USER_NAME"] = "root"

    spark = (
        SparkSession.builder
        .appName("SupplyChainDashboardExtraTables")
        .master("local[*]")
        .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark


def load_database_config():
    load_dotenv(PROJECT_ROOT / ".env")

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "name": os.getenv("DB_NAME", "supply_chain_db"),
        "user": os.getenv("DB_USER", "supply_chain_user"),
        "password": os.getenv("DB_PASSWORD", "supply_chain_pass"),
        "schema": os.getenv("DB_SCHEMA", "dashboard"),
    }


def create_engine_from_config(config):
    url = (
        f"postgresql+psycopg2://{config['user']}:{config['password']}"
        f"@{config['host']}:{config['port']}/{config['name']}"
    )
    return create_engine(url)


def safe_divide_percentage(numerator_col, denominator_col):
    return when(
        denominator_col > 0,
        (numerator_col / denominator_col) * 100
    ).otherwise(lit(0.0))


def build_late_by_country(df):
    result = df.groupBy("order_country").agg(
        countDistinct("order_id").alias("total_orders"),
        countDistinct(when(col("late_delivery_risk") == 1, col("order_id"))).alias("late_orders"),
        avg("days_for_shipping_real").alias("average_shipping_days"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit")
    )

    result = result.withColumn(
        "late_delivery_rate",
        safe_divide_percentage(col("late_orders"), col("total_orders"))
    )

    return result.select(
        "order_country",
        "total_orders",
        "late_orders",
        "late_delivery_rate",
        "average_shipping_days",
        "total_sales",
        "total_profit"
    ).orderBy(col("late_delivery_rate").desc()).limit(20)


def build_top_products_by_sales(df):
    result = df.groupBy("product_name", "category_name").agg(
        countDistinct("order_id").alias("total_orders"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit"),
        countDistinct(when(col("late_delivery_risk") == 1, col("order_id"))).alias("late_orders")
    )

    result = result.withColumn(
        "late_delivery_rate",
        safe_divide_percentage(col("late_orders"), col("total_orders"))
    )

    return result.select(
        "product_name",
        "category_name",
        "total_orders",
        "total_sales",
        "total_profit",
        "late_orders",
        "late_delivery_rate"
    ).orderBy(col("total_sales").desc()).limit(25)


def build_loss_by_market(df):
    result = df.groupBy("market").agg(
        countDistinct("order_id").alias("total_orders"),
        countDistinct(when(col("is_loss_order") == 1, col("order_id"))).alias("loss_orders"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit")
    )

    result = result.withColumn(
        "loss_rate",
        safe_divide_percentage(col("loss_orders"), col("total_orders"))
    )

    return result.select(
        "market",
        "total_orders",
        "loss_orders",
        "loss_rate",
        "total_sales",
        "total_profit"
    ).orderBy(col("loss_rate").desc())


def build_profit_margin_by_category(df):
    result = df.groupBy("category_name").agg(
        countDistinct("order_id").alias("total_orders"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit"),
        avg("profit_margin").alias("average_profit_margin")
    )

    result = result.withColumn(
        "average_profit_margin",
        col("average_profit_margin") * 100
    )

    return result.select(
        "category_name",
        "total_orders",
        "total_sales",
        "total_profit",
        "average_profit_margin"
    ).orderBy(col("average_profit_margin").desc()).limit(20)


def write_table(df, table_name, engine, schema):
    hdfs_path = f"{HDFS_GOLD_BASE_PATH}/{table_name}.parquet"
    df.coalesce(1).write.mode("overwrite").parquet(hdfs_path)

    pandas_df = df.toPandas()
    pandas_df.to_sql(
        table_name,
        engine,
        schema=schema,
        if_exists="replace",
        index=False,
        method="multi"
    )

    return hdfs_path, len(pandas_df)


def write_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"dashboard_extra_tables_log_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4, ensure_ascii=False)

    return log_file


def main():
    start_time = datetime.now()

    spark = create_spark_session()
    config = load_database_config()
    engine = create_engine_from_config(config)
    schema = config["schema"]

    df = spark.read.parquet(HDFS_INPUT_PATH)

    tables = {
        "late_by_country": build_late_by_country(df),
        "top_products_by_sales": build_top_products_by_sales(df),
        "loss_by_market": build_loss_by_market(df),
        "profit_margin_by_category": build_profit_margin_by_category(df)
    }

    results = {}

    for table_name, table_df in tables.items():
        hdfs_path, rows = write_table(table_df, table_name, engine, schema)
        results[table_name] = {
            "hdfs_path": hdfs_path,
            "postgres_rows": rows
        }

    end_time = datetime.now()

    log_data = {
        "status": "success",
        "created_tables": results,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2)
    }

    log_file = write_log(log_data)

    print("Dashboard extra analytics tables built successfully.")
    for table_name, result in results.items():
        print(f"- {table_name}")
        print(f"  HDFS: {result['hdfs_path']}")
        print(f"  PostgreSQL rows: {result['postgres_rows']}")
    print(f"Log file: {log_file}")

    spark.stop()


if __name__ == "__main__":
    main()