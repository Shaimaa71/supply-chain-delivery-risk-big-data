import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "storage"


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


def write_log(log_data):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"processed_storage_setup_log_{timestamp}.json"

    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4, ensure_ascii=False)

    return log_file


def create_tables(engine, schema):
    statements = [
        f"CREATE SCHEMA IF NOT EXISTS {schema};",

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.executive_kpis (
            id SERIAL PRIMARY KEY,
            total_orders BIGINT,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION,
            late_delivery_rate DOUBLE PRECISION,
            average_shipping_days DOUBLE PRECISION,
            average_profit_margin DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.late_by_shipping_mode (
            shipping_mode TEXT PRIMARY KEY,
            total_orders BIGINT,
            late_orders BIGINT,
            late_delivery_rate DOUBLE PRECISION,
            average_shipping_days DOUBLE PRECISION,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.late_by_market (
            market TEXT PRIMARY KEY,
            total_orders BIGINT,
            late_orders BIGINT,
            late_delivery_rate DOUBLE PRECISION,
            average_shipping_days DOUBLE PRECISION,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.late_by_region (
            order_region TEXT PRIMARY KEY,
            total_orders BIGINT,
            late_orders BIGINT,
            late_delivery_rate DOUBLE PRECISION,
            average_shipping_days DOUBLE PRECISION,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.late_by_category (
            category_name TEXT PRIMARY KEY,
            total_orders BIGINT,
            late_orders BIGINT,
            late_delivery_rate DOUBLE PRECISION,
            average_shipping_days DOUBLE PRECISION,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.profit_impact (
            delivery_status TEXT PRIMARY KEY,
            total_orders BIGINT,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION,
            average_profit_per_order DOUBLE PRECISION,
            average_profit_margin DOUBLE PRECISION,
            loss_orders BIGINT,
            loss_rate DOUBLE PRECISION
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.risky_products (
            product_name TEXT,
            category_name TEXT,
            total_orders BIGINT,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION,
            late_orders BIGINT,
            late_delivery_rate DOUBLE PRECISION,
            PRIMARY KEY (product_name, category_name)
        );
        """,

        f"""
        CREATE TABLE IF NOT EXISTS {schema}.discount_profit_summary (
            discount_level TEXT PRIMARY KEY,
            total_orders BIGINT,
            average_discount_rate DOUBLE PRECISION,
            total_sales DOUBLE PRECISION,
            total_profit DOUBLE PRECISION,
            average_profit_margin DOUBLE PRECISION,
            loss_orders BIGINT,
            loss_rate DOUBLE PRECISION
        );
        """
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def list_created_tables(engine, schema):
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema
        ORDER BY table_name;
    """)

    with engine.connect() as connection:
        result = connection.execute(query, {"schema": schema})
        return [row[0] for row in result]


def test_connection(engine):
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1;"))
        return result.scalar() == 1


def main():
    start_time = datetime.now()

    config = load_database_config()
    engine = create_engine_from_config(config)

    connection_ok = test_connection(engine)
    create_tables(engine, config["schema"])
    tables = list_created_tables(engine, config["schema"])

    end_time = datetime.now()

    log_data = {
        "status": "success",
        "database": config["name"],
        "schema": config["schema"],
        "connection_ok": connection_ok,
        "created_tables": tables,
        "table_count": len(tables),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2)
    }

    log_file = write_log(log_data)

    print("Processed storage setup completed successfully.")
    print(f"Database: {config['name']}")
    print(f"Schema: {config['schema']}")
    print(f"Connection OK: {connection_ok}")
    print(f"Tables created: {len(tables)}")
    for table in tables:
        print(f"- {config['schema']}.{table}")
    print(f"Log file: {log_file}")


if __name__ == "__main__":
    main()