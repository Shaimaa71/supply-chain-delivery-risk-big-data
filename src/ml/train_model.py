import json
import os
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pyspark.sql import SparkSession

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs" / "ml"
MODEL_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

HDFS_INPUT_PATH = "hdfs://localhost:9000/user/bigdata/supply_chain/silver/clean_orders.parquet"

TARGET_COLUMN = "late_delivery_risk"

CATEGORICAL_FEATURES = [
    "type",
    "category_name",
    "customer_segment",
    "department_name",
    "market",
    "order_region",
    "order_country",
    "order_state",
    "shipping_mode"
]

NUMERIC_FEATURES = [
    "days_for_shipment_scheduled",
    "order_item_quantity",
    "order_item_discount",
    "order_item_discount_rate",
    "order_item_product_price",
    "product_price",
    "sales"
]

LEAKAGE_COLUMNS = [
    "days_for_shipping_real",
    "delivery_status",
    "shipping_date",
    "shipping_delay_days"
]

ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def create_spark_session():
    os.environ["HADOOP_USER_NAME"] = "root"

    spark = (
        SparkSession.builder
        .appName("LateDeliveryRiskModelTraining")
        .master("local[*]")
        .config("spark.hadoop.fs.defaultFS", "hdfs://localhost:9000")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")
    return spark


def create_one_hot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=True)


def create_preprocessor():
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("encoder", create_one_hot_encoder())
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES)
        ]
    )

    return preprocessor


def evaluate_model(model, x_test, y_test):
    y_pred = model.predict(x_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0)
    }

    if hasattr(model, "predict_proba"):
        y_probability = model.predict_proba(x_test)[:, 1]
        metrics["roc_auc"] = roc_auc_score(y_test, y_probability)
    else:
        metrics["roc_auc"] = None

    report = classification_report(y_test, y_pred, zero_division=0)
    matrix = confusion_matrix(y_test, y_pred)

    return metrics, report, matrix


def save_confusion_matrix_plot(matrix, output_path):
    plt.figure(figsize=(6, 5))
    plt.imshow(matrix)
    plt.title("Confusion Matrix - Best Model")
    plt.xlabel("Predicted Label")
    plt.ylabel("Actual Label")
    plt.xticks([0, 1], ["No Risk", "Late Risk"])
    plt.yticks([0, 1], ["No Risk", "Late Risk"])

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            plt.text(j, i, str(matrix[i, j]), ha="center", va="center")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def save_model_comparison_plot(metrics_by_model, output_path):
    model_names = list(metrics_by_model.keys())
    metric_names = ["accuracy", "precision", "recall", "f1_score"]

    x = np.arange(len(metric_names))
    width = 0.35

    plt.figure(figsize=(9, 5))

    for index, model_name in enumerate(model_names):
        values = [metrics_by_model[model_name][metric] for metric in metric_names]
        plt.bar(x + (index * width), values, width, label=model_name)

    plt.xticks(x + width / 2, ["Accuracy", "Precision", "Recall", "F1-score"])
    plt.ylim(0, 1)
    plt.title("Model Performance Comparison")
    plt.ylabel("Score")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def save_roc_curve_plot(models, x_test, y_test, output_path):
    plt.figure(figsize=(7, 5))

    for model_name, model in models.items():
        if hasattr(model, "predict_proba"):
            y_probability = model.predict_proba(x_test)[:, 1]
            fpr, tpr, _ = roc_curve(y_test, y_probability)
            auc_score = roc_auc_score(y_test, y_probability)
            plt.plot(fpr, tpr, label=f"{model_name} AUC={auc_score:.3f}")

    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.title("ROC Curve")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


def get_feature_names(preprocessor):
    try:
        return preprocessor.get_feature_names_out()
    except Exception:
        return np.array([f"feature_{index}" for index in range(0, 1)])


def save_feature_importance_plot(best_model, output_path):
    preprocessor = best_model.named_steps["preprocessor"]
    classifier = best_model.named_steps["model"]
    feature_names = get_feature_names(preprocessor)

    if hasattr(classifier, "feature_importances_"):
        values = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        values = np.abs(classifier.coef_[0])
    else:
        return False

    if len(feature_names) != len(values):
        feature_names = np.array([f"feature_{index}" for index in range(len(values))])

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": values
        }
    ).sort_values("importance", ascending=False).head(20)

    importance_df = importance_df.sort_values("importance", ascending=True)

    plt.figure(figsize=(9, 7))
    plt.barh(importance_df["feature"], importance_df["importance"])
    plt.title("Top 20 Important Features")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    return True


def write_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def write_text(text, output_path):
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(text)


def main():
    start_time = datetime.now()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    spark = create_spark_session()
    spark_df = spark.read.parquet(HDFS_INPUT_PATH)

    selected_columns = ALL_FEATURES + [TARGET_COLUMN]
    model_df = spark_df.select(*selected_columns).dropna(subset=[TARGET_COLUMN])

    input_rows = model_df.count()
    pdf = model_df.toPandas()

    pdf[TARGET_COLUMN] = pdf[TARGET_COLUMN].astype(int)

    x = pdf[ALL_FEATURES]
    y = pdf[TARGET_COLUMN]

    class_distribution = y.value_counts().sort_index().to_dict()

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    preprocessor_lr = create_preprocessor()
    preprocessor_rf = create_preprocessor()

    logistic_regression = Pipeline(
        steps=[
            ("preprocessor", preprocessor_lr),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced"))
        ]
    )

    random_forest = Pipeline(
        steps=[
            ("preprocessor", preprocessor_rf),
            ("model", RandomForestClassifier(
                n_estimators=120,
                max_depth=18,
                random_state=42,
                class_weight="balanced",
                n_jobs=-1
            ))
        ]
    )

    models = {
        "Logistic Regression": logistic_regression,
        "Random Forest": random_forest
    }

    trained_models = {}
    metrics_by_model = {}
    reports_by_model = {}
    matrices_by_model = {}

    for model_name, model in models.items():
        model.fit(x_train, y_train)
        metrics, report, matrix = evaluate_model(model, x_test, y_test)

        trained_models[model_name] = model
        metrics_by_model[model_name] = metrics
        reports_by_model[model_name] = report
        matrices_by_model[model_name] = matrix.tolist()

    best_model_name = max(metrics_by_model, key=lambda name: metrics_by_model[name]["f1_score"])
    best_model = trained_models[best_model_name]
    best_matrix = np.array(matrices_by_model[best_model_name])

    joblib.dump(best_model, MODEL_DIR / "late_delivery_model.pkl")
    joblib.dump(best_model.named_steps["preprocessor"], MODEL_DIR / "encoders.pkl")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    confusion_matrix_path = FIGURES_DIR / "confusion_matrix.png"
    model_comparison_path = FIGURES_DIR / "model_comparison.png"
    roc_curve_path = FIGURES_DIR / "roc_curve.png"
    feature_importance_path = FIGURES_DIR / "feature_importance_top20.png"

    save_confusion_matrix_plot(best_matrix, confusion_matrix_path)
    save_model_comparison_plot(metrics_by_model, model_comparison_path)
    save_roc_curve_plot(trained_models, x_test, y_test, roc_curve_path)
    feature_importance_created = save_feature_importance_plot(best_model, feature_importance_path)

    metrics_output = {
        "status": "success",
        "input_path": HDFS_INPUT_PATH,
        "target_column": TARGET_COLUMN,
        "features_used": ALL_FEATURES,
        "excluded_leakage_columns": LEAKAGE_COLUMNS,
        "input_rows": input_rows,
        "train_rows": len(x_train),
        "test_rows": len(x_test),
        "class_distribution": {
            str(key): int(value) for key, value in class_distribution.items()
        },
        "metrics_by_model": {
            model_name: {
                metric_name: round(metric_value, 4) if metric_value is not None else None
                for metric_name, metric_value in metrics.items()
            }
            for model_name, metrics in metrics_by_model.items()
        },
        "best_model": best_model_name,
        "best_model_metrics": {
            metric_name: round(metric_value, 4) if metric_value is not None else None
            for metric_name, metric_value in metrics_by_model[best_model_name].items()
        },
        "confusion_matrix_best_model": matrices_by_model[best_model_name],
        "output_files": {
            "model": str(MODEL_DIR / "late_delivery_model.pkl"),
            "encoders": str(MODEL_DIR / "encoders.pkl"),
            "metrics": str(MODEL_DIR / "model_metrics.json"),
            "confusion_matrix": str(confusion_matrix_path),
            "model_comparison": str(model_comparison_path),
            "roc_curve": str(roc_curve_path),
            "feature_importance": str(feature_importance_path) if feature_importance_created else None
        },
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat()
    }

    write_json(metrics_output, MODEL_DIR / "model_metrics.json")

    report_text = ""
    for model_name, report in reports_by_model.items():
        report_text += f"{model_name}\n"
        report_text += "=" * len(model_name) + "\n"
        report_text += report + "\n\n"

    write_text(report_text, MODEL_DIR / "classification_report.txt")

    log_file = LOG_DIR / f"model_training_log_{timestamp}.json"
    write_json(metrics_output, log_file)

    print("Machine learning model training completed successfully.")
    print(f"Input path: {HDFS_INPUT_PATH}")
    print(f"Input rows: {input_rows}")
    print(f"Train rows: {len(x_train)}")
    print(f"Test rows: {len(x_test)}")
    print("Class distribution:")
    for label, count in class_distribution.items():
        print(f"- {label}: {count}")

    print("Model metrics:")
    for model_name, metrics in metrics_by_model.items():
        print(f"- {model_name}")
        for metric_name, metric_value in metrics.items():
            if metric_value is None:
                print(f"  {metric_name}: None")
            else:
                print(f"  {metric_name}: {metric_value:.4f}")

    print(f"Best model: {best_model_name}")
    print("Saved files:")
    print(f"- {MODEL_DIR / 'late_delivery_model.pkl'}")
    print(f"- {MODEL_DIR / 'encoders.pkl'}")
    print(f"- {MODEL_DIR / 'model_metrics.json'}")
    print(f"- {MODEL_DIR / 'classification_report.txt'}")
    print(f"- {confusion_matrix_path}")
    print(f"- {model_comparison_path}")
    print(f"- {roc_curve_path}")
    if feature_importance_created:
        print(f"- {feature_importance_path}")
    print(f"Log file: {log_file}")

    spark.stop()


if __name__ == "__main__":
    main()