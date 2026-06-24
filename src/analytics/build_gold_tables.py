import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    countDistinct,
    lit,
    sum as spark_sum,
    when
)
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "analytics"

HDFS_INPUT_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/silver/clean_orders.parquet"
HDFS_GOLD_BASE_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/gold"


def create_spark_session():
    os.environ["HADOOP_USER_NAME"] = "root"

    spark = (
        SparkSession.builder
        .appName("SupplyChainGoldAnalyticsTables")
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


def write_to_hdfs(df, table_name):
    output_path = f"{HDFS_GOLD_BASE_PATH}/{table_name}.parquet"
    df.coalesce(1).write.mode("overwrite").parquet(output_path)
    return output_path


def truncate_postgres_table(engine, schema, table_name):
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE TABLE {schema}.{table_name} RESTART IDENTITY;"))


def write_to_postgres(df, engine, schema, table_name):
    pandas_df = df.toPandas()
    truncate_postgres_table(engine, schema, table_name)
    pandas_df.to_sql(
        table_name,
        engine,
        schema=schema,
        if_exists="append",
        index=False,
        method="multi"
    )
    return len(pandas_df)


def build_executive_kpis(df):
    result = df.agg(
        countDistinct("order_id").alias("total_orders"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit"),
        countDistinct(when(col("late_delivery_risk") == 1, col("order_id"))).alias("late_orders"),
        avg("days_for_shipping_real").alias("average_shipping_days"),
        avg("profit_margin").alias("average_profit_margin")
    )

    result = result.withColumn(
        "late_delivery_rate",
        safe_divide_percentage(col("late_orders"), col("total_orders"))
    )

    result = result.withColumn(
        "average_profit_margin",
        col("average_profit_margin") * 100
    )

    return result.select(
        "total_orders",
        "total_sales",
        "total_profit",
        "late_delivery_rate",
        "average_shipping_days",
        "average_profit_margin"
    )


def build_late_by_group(df, group_column, table_columns):
    result = df.groupBy(group_column).agg(
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

    return result.select(*table_columns).orderBy(col("late_delivery_rate").desc())


def build_profit_impact(df):
    result = df.groupBy("delivery_status").agg(
        countDistinct("order_id").alias("total_orders"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit"),
        avg("order_profit_per_order").alias("average_profit_per_order"),
        avg("profit_margin").alias("average_profit_margin"),
        countDistinct(when(col("is_loss_order") == 1, col("order_id"))).alias("loss_orders")
    )

    result = result.withColumn(
        "average_profit_margin",
        col("average_profit_margin") * 100
    )

    result = result.withColumn(
        "loss_rate",
        safe_divide_percentage(col("loss_orders"), col("total_orders"))
    )

    return result.select(
        "delivery_status",
        "total_orders",
        "total_sales",
        "total_profit",
        "average_profit_per_order",
        "average_profit_margin",
        "loss_orders",
        "loss_rate"
    ).orderBy(col("loss_rate").desc())


def build_risky_products(df):
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

    result = result.filter(col("total_orders") >= 20)

    return result.select(
        "product_name",
        "category_name",
        "total_orders",
        "total_sales",
        "total_profit",
        "late_orders",
        "late_delivery_rate"
    ).orderBy(col("late_delivery_rate").desc(), col("total_sales").desc()).limit(25)


def build_discount_profit_summary(df):
    result = df.groupBy("discount_level").agg(
        countDistinct("order_id").alias("total_orders"),
        avg("order_item_discount_rate").alias("average_discount_rate"),
        spark_sum("sales").alias("total_sales"),
        spark_sum("order_profit_per_order").alias("total_profit"),
        avg("profit_margin").alias("average_profit_margin"),
        countDistinct(when(col("is_loss_order") == 1, col("order_id"))).alias("loss_orders")
    )

    result = result.withColumn(
        "average_discount_rate",
        col("average_discount_rate") * 100
    )

    result = result.withColumn(
        "average_profit_margin",
        col("average_profit_margin") * 100
    )

    result = result.withColumn(
        "loss_rate",
        safe_divide_percentage(col("loss_orders"), col("total_orders"))
    )

    return result.select(
        "discount_level",
        "total_orders",
        "average_discount_rate",
        "total_sales",
        "total_profit",
        "average_profit_margin",
        "loss_orders",
        "loss_rate"
    ).orderBy(col("loss_rate").desc())


def write_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"gold_tables_log_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4, ensure_ascii=False)

    return log_file


def main():
    start_time = datetime.now()

    spark = create_spark_session()
    db_config = load_database_config()
    engine = create_engine_from_config(db_config)
    schema = db_config["schema"]

    clean_df = spark.read.parquet(HDFS_INPUT_PATH)

    total_input_rows = clean_df.count()

    tables = {
        "executive_kpis": build_executive_kpis(clean_df),
        "late_by_shipping_mode": build_late_by_group(
            clean_df,
            "shipping_mode",
            [
                "shipping_mode",
                "total_orders",
                "late_orders",
                "late_delivery_rate",
                "average_shipping_days",
                "total_sales",
                "total_profit"
            ]
        ),
        "late_by_market": build_late_by_group(
            clean_df,
            "market",
            [
                "market",
                "total_orders",
                "late_orders",
                "late_delivery_rate",
                "average_shipping_days",
                "total_sales",
                "total_profit"
            ]
        ),
        "late_by_region": build_late_by_group(
            clean_df,
            "order_region",
            [
                "order_region",
                "total_orders",
                "late_orders",
                "late_delivery_rate",
                "average_shipping_days",
                "total_sales",
                "total_profit"
            ]
        ),
        "late_by_category": build_late_by_group(
            clean_df,
            "category_name",
            [
                "category_name",
                "total_orders",
                "late_orders",
                "late_delivery_rate",
                "average_shipping_days",
                "total_sales",
                "total_profit"
            ]
        ),
        "profit_impact": build_profit_impact(clean_df),
        "risky_products": build_risky_products(clean_df),
        "discount_profit_summary": build_discount_profit_summary(clean_df)
    }

    table_results = {}

    for table_name, table_df in tables.items():
        hdfs_output_path = write_to_hdfs(table_df, table_name)
        postgres_rows = write_to_postgres(table_df, engine, schema, table_name)

        table_results[table_name] = {
            "hdfs_output_path": hdfs_output_path,
            "postgres_rows": postgres_rows
        }

    end_time = datetime.now()

    log_data = {
        "status": "success",
        "input_path": HDFS_INPUT_PATH,
        "gold_base_path": HDFS_GOLD_BASE_PATH,
        "postgres_database": db_config["name"],
        "postgres_schema": schema,
        "input_rows": total_input_rows,
        "created_tables": table_results,
        "table_count": len(tables),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2)
    }

    log_file = write_log(log_data)

    print("Gold analytics tables built successfully.")
    print(f"Input path: {HDFS_INPUT_PATH}")
    print(f"Input rows: {total_input_rows}")
    print(f"HDFS gold base path: {HDFS_GOLD_BASE_PATH}")
    print(f"PostgreSQL schema: {schema}")
    print(f"Tables created: {len(tables)}")

    for table_name, result in table_results.items():
        print(f"- {table_name}")
        print(f"  HDFS: {result['hdfs_output_path']}")
        print(f"  PostgreSQL rows: {result['postgres_rows']}")

    print(f"Log file: {log_file}")

    spark.stop()


if __name__ == "__main__":
    main()
    