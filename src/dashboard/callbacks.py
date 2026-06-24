from pathlib import Path

import dash_bootstrap_components as dbc
import joblib
import pandas as pd
from dash import Input, Output, State, ctx, html

from components import read_table
from layout import render_page

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "late_delivery_model.pkl"


def clicked_value(click_data):
    if not click_data:
        return None

    point = click_data.get("points", [{}])[0]

    if "x" in point and isinstance(point["x"], str):
        return point["x"]

    if "y" in point and isinstance(point["y"], str):
        return point["y"]

    return None


def nav_colors(active_page):
    return [
        "success" if active_page == "overview" else "secondary",
        "success" if active_page == "delivery" else "secondary",
        "success" if active_page == "product" else "secondary",
        "success" if active_page == "profit" else "secondary",
        "success" if active_page == "prediction" else "secondary"
    ]


def register_callbacks(app):
    @app.callback(
        Output("active-page", "data"),
        Output("page-content", "children"),
        Output("nav-overview", "color"),
        Output("nav-delivery", "color"),
        Output("nav-product", "color"),
        Output("nav-profit", "color"),
        Output("nav-prediction", "color"),
        Input("nav-overview", "n_clicks"),
        Input("nav-delivery", "n_clicks"),
        Input("nav-product", "n_clicks"),
        Input("nav-profit", "n_clicks"),
        Input("nav-prediction", "n_clicks"),
        State("active-page", "data")
    )
    def switch_page(n1, n2, n3, n4, n5, current_page):
        trigger = ctx.triggered_id

        mapping = {
            "nav-overview": "overview",
            "nav-delivery": "delivery",
            "nav-product": "product",
            "nav-profit": "profit",
            "nav-prediction": "prediction"
        }

        if trigger in mapping:
            current_page = mapping[trigger]

        colors = nav_colors(current_page)
        return current_page, render_page(current_page), *colors

    @app.callback(
        Output("shipping-click-output", "children"),
        Input("shipping-mode-chart", "clickData")
    )
    def shipping_insight(click_data):
        selected = clicked_value(click_data)

        if not selected:
            return dbc.Alert(
                "Click on a shipping mode bar to display a quick decision-support explanation.",
                color="light",
                style={"borderRadius": "14px"}
            )

        df = read_table("late_by_shipping_mode")
        row = df[df["shipping_mode"] == selected]

        if row.empty:
            return dbc.Alert("No data found for the selected shipping mode.", color="warning", style={"borderRadius": "14px"})

        row = row.iloc[0]
        rate = row["late_delivery_rate"]

        if rate >= 70:
            decision = "This shipping mode has very high late delivery risk. It should be reviewed immediately and avoided for sensitive orders unless the process is improved."
            color = "danger"
        elif rate >= 50:
            decision = "This shipping mode has medium-to-high delivery risk. It should be monitored carefully and compared with safer alternatives."
            color = "warning"
        else:
            decision = "This shipping mode has relatively lower delivery risk and can be used under regular monitoring."
            color = "success"

        return dbc.Alert(
            [
                html.H5(f"Shipping Mode: {selected}", className="fw-bold"),
                html.P(f"Late delivery rate: {rate:.2f}%"),
                html.P(f"Total orders: {int(row['total_orders'])}"),
                html.P(f"Late orders: {int(row['late_orders'])}"),
                html.Hr(),
                html.P(f"Recommended decision: {decision}", className="mb-0")
            ],
            color=color,
            style={"borderRadius": "14px"}
        )

    @app.callback(
        Output("market-click-output", "children"),
        Input("market-chart", "clickData")
    )
    def market_insight(click_data):
        selected = clicked_value(click_data)

        if not selected:
            return dbc.Alert(
                "Click on a market bar to display a market-level explanation.",
                color="light",
                style={"borderRadius": "14px"}
            )

        df = read_table("late_by_market")
        row = df[df["market"] == selected]

        if row.empty:
            return dbc.Alert("No data found for the selected market.", color="warning", style={"borderRadius": "14px"})

        row = row.iloc[0]

        return dbc.Alert(
            [
                html.H5(f"Market: {selected}", className="fw-bold"),
                html.P(f"Late delivery rate: {row['late_delivery_rate']:.2f}%"),
                html.P(f"Total orders: {int(row['total_orders'])}"),
                html.P(f"Late orders: {int(row['late_orders'])}"),
                html.Hr(),
                html.P(
                    "Recommended decision: review logistics planning, supplier coordination, and shipping performance in this market, especially if it also has high order volume.",
                    className="mb-0"
                )
            ],
            color="info",
            style={"borderRadius": "14px"}
        )

    @app.callback(
        Output("prediction-output", "children"),
        Input("predict-button", "n_clicks"),
        State("pred-type", "value"),
        State("pred-shipping-mode", "value"),
        State("pred-market", "value"),
        State("pred-order-region", "value"),
        State("pred-order-country", "value"),
        State("pred-order-state", "value"),
        State("pred-category-name", "value"),
        State("pred-customer-segment", "value"),
        State("pred-department-name", "value"),
        State("pred-sales", "value"),
        State("pred-discount-rate", "value"),
        State("pred-discount", "value"),
        State("pred-quantity", "value"),
        State("pred-scheduled-days", "value"),
        State("pred-item-price", "value")
    )
    def predict_result(
        n_clicks,
        order_type,
        shipping_mode,
        market,
        order_region,
        order_country,
        order_state,
        category_name,
        customer_segment,
        department_name,
        sales,
        discount_rate,
        discount,
        quantity,
        scheduled_days,
        item_price
    ):
        if not n_clicks:
            return dbc.Alert(
                "Fill the form and click Predict Risk to display the model result.",
                color="light",
                style={"borderRadius": "14px"}
            )

        model = joblib.load(MODEL_PATH)

        input_df = pd.DataFrame(
            [
                {
                    "type": order_type,
                    "category_name": category_name,
                    "customer_segment": customer_segment,
                    "department_name": department_name,
                    "market": market,
                    "order_region": order_region,
                    "order_country": order_country,
                    "order_state": order_state,
                    "shipping_mode": shipping_mode,
                    "days_for_shipment_scheduled": scheduled_days,
                    "order_item_quantity": quantity,
                    "order_item_discount": discount,
                    "order_item_discount_rate": discount_rate,
                    "order_item_product_price": item_price,
                    "product_price": item_price,
                    "sales": sales
                }
            ]
        )

        prediction = int(model.predict(input_df)[0])

        probability = None
        if hasattr(model, "predict_proba"):
            probability = float(model.predict_proba(input_df)[0][1])

        if prediction == 1:
            title = "High Late Delivery Risk"
            message = "Recommended decision: prioritize this order, monitor it closely, or consider switching to a safer and faster shipping mode."
            color = "danger"
        else:
            title = "Low Late Delivery Risk"
            message = "Recommended decision: continue with the regular order workflow while maintaining standard operational monitoring."
            color = "success"

        probability_text = ""
        if probability is not None:
            probability_text = f"Predicted late-risk probability: {probability * 100:.2f}%"

        return dbc.Card(
            dbc.CardBody(
                [
                    html.H3(title, className="fw-bold mb-2"),
                    html.P(probability_text, className="fs-5"),
                    html.Hr(),
                    html.P(message, className="mb-0")
                ]
            ),
            color=color,
            inverse=True,
            style={
                "borderRadius": "18px",
                "boxShadow": "0 10px 24px rgba(31, 41, 55, 0.12)"
            }
        )