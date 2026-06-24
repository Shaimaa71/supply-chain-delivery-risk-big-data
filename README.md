# Supply Chain Delivery Risk Big Data

A Big Data decision support system for analyzing supply chain orders and predicting late delivery risk.

## Overview

This project analyzes supply chain delivery performance and identifies factors that may lead to late orders. The system uses a Big Data pipeline to process order, shipping, market, product, sales, and profit data, then trains a machine learning model to predict late delivery risk.

The project was built using HDFS, Apache Spark, PostgreSQL, Machine Learning, and Plotly Dash. The final dashboard helps decision-makers understand delivery risk by shipping mode, market, region, product category, and profitability.

## Features

- Built a Big Data pipeline for supply chain delivery risk analysis.
- Processed and cleaned data using Apache Spark / PySpark.
- Stored processed data using HDFS and PostgreSQL.
- Trained machine learning models to predict late delivery risk.
- Compared Logistic Regression and Random Forest models.
- Built an interactive dashboard using Plotly Dash.
- Generated visual reports such as confusion matrix, ROC curve, and feature importance.

## Technologies

- Python
- HDFS
- Apache Spark / PySpark
- PostgreSQL
- scikit-learn
- Plotly Dash
- Docker

## Machine Learning Result

Random Forest was selected as the final model because it achieved the best overall performance.

| Model | Accuracy | F1-score | ROC AUC |
|---|---:|---:|---:|
| Logistic Regression | 0.6985 | 0.6712 | 0.7554 |
| Random Forest | 0.6948 | 0.6734 | 0.7564 |

## Project Structure

```text
supply-chain-delivery-risk-big-data/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── .gitignore
├── src/
├── models/
└── reports/
    └── figures/
