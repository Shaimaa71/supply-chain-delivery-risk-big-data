from dash import dcc, html
import dash_bootstrap_components as dbc

from components import (
    ACCENT,
    BG_COLOR,
    BORDER,
    CARD_STYLE,
    INPUT_STYLE,
    PRIMARY,
    SECONDARY,
    SIDEBAR_BG,
    SIDEBAR_SOFT,
    TEXT_DARK,
    TEXT_MUTED,
    chart_card,
    format_number,
    get_prediction_options,
    graph_component,
    info_card,
    kpi_card,
    make_bar,
    make_pie,
    page_title,
    read_table
)


def sidebar_button(label, button_id, color):
    return dbc.Button(
        label,
        id=button_id,
        color=color,
        className="w-100 mb-2",
        style={
            "borderRadius": "14px",
            "fontWeight": "700",
            "padding": "12px 14px",
            "textAlign": "left"
        }
    )


def input_dropdown(label, component_id, options, value=None):
    if value is None and options:
        value = options[0]["value"]

    return dbc.Col(
        [
            dbc.Label(label, className="fw-bold", style={"color": TEXT_DARK}),
            dcc.Dropdown(
                id=component_id,
                options=options,
                value=value,
                clearable=False,
                style=INPUT_STYLE
            )
        ],
        md=4,
        className="mb-3"
    )


def input_number(label, component_id, value, min_value=None):
    return dbc.Col(
        [
            dbc.Label(label, className="fw-bold", style={"color": TEXT_DARK}),
            dbc.Input(
                id=component_id,
                type="number",
                value=value,
                min=min_value,
                style=INPUT_STYLE
            )
        ],
        md=4,
        className="mb-3"
    )


def overview_page():
    kpis = read_table("executive_kpis").iloc[0]
    shipping = read_table("late_by_shipping_mode")
    market = read_table("late_by_market")
    category = read_table("late_by_category")

    most_risky = shipping.sort_values("late_delivery_rate", ascending=False).iloc[0]["shipping_mode"]

    return html.Div(
        [
            page_title(
                "Executive Overview",
                "A quick management view of the main performance indicators related to orders, profit, shipping, and delivery risk."
            ),
            dbc.Row(
                [
                    dbc.Col(kpi_card("Total Orders", format_number(kpis["total_orders"]), "Unique orders in the dataset", PRIMARY), md=4, lg=2),
                    dbc.Col(kpi_card("Total Sales", format_number(kpis["total_sales"]), "Overall sales amount", SECONDARY), md=4, lg=2),
                    dbc.Col(kpi_card("Total Profit", format_number(kpis["total_profit"]), "Overall profit amount", ACCENT), md=4, lg=2),
                    dbc.Col(kpi_card("Late Delivery Rate", f"{kpis['late_delivery_rate']:.2f}%", "Overall late delivery level", PRIMARY), md=4, lg=2),
                    dbc.Col(kpi_card("Avg Shipping Days", f"{kpis['average_shipping_days']:.2f}", "Average real shipping time", SECONDARY), md=4, lg=2),
                    dbc.Col(kpi_card("Most Risky Mode", most_risky, "Shipping mode with the highest late risk", ACCENT), md=4, lg=2)
                ],
                className="g-3 mb-4"
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Late Delivery Rate by Shipping Mode", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "overview-shipping-chart",
                                        make_bar(
                                            shipping,
                                            "shipping_mode",
                                            "late_delivery_rate",
                                            hover_data=["total_orders", "late_orders", "total_profit"]
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=7,
                        className="mb-4"
                    ),
                    dbc.Col(
                        info_card(
                            "Management Interpretation",
                            "This page helps managers understand the overall status of the supply chain before going into deeper analysis. It highlights total business activity, the current late delivery level, and the shipping mode that needs the most attention.",
                            PRIMARY
                        ),
                        lg=5,
                        className="mb-4"
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Top Categories by Sales", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "overview-category-sales-chart",
                                        make_bar(
                                            category.sort_values("total_sales", ascending=False).head(10),
                                            "total_sales",
                                            "category_name",
                                            hover_data=["total_orders", "late_delivery_rate", "total_profit"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=7,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Orders Distribution by Market", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "overview-market-pie",
                                        make_pie(market, "market", "total_orders")
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=5,
                        className="mb-4"
                    )
                ]
            )
        ]
    )


def delivery_page():
    shipping = read_table("late_by_shipping_mode")
    market = read_table("late_by_market")
    region = read_table("late_by_region").head(12)
    country = read_table("late_by_country").head(12)

    return html.Div(
        [
            page_title(
                "Delivery Risk Analysis",
                "Interactive analysis of risk across shipping modes, markets, regions, and countries."
            ),
            dbc.Alert(
                "Hover over any chart to inspect details, and click on a shipping mode or market to see a decision explanation.",
                color="warning",
                style={"borderRadius": "14px"}
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Late Delivery by Shipping Mode", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "shipping-mode-chart",
                                        make_bar(
                                            shipping,
                                            "shipping_mode",
                                            "late_delivery_rate",
                                            hover_data=["total_orders", "late_orders", "average_shipping_days", "total_profit"]
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Late Delivery by Market", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "market-chart",
                                        make_bar(
                                            market,
                                            "market",
                                            "late_delivery_rate",
                                            hover_data=["total_orders", "late_orders", "average_shipping_days", "total_profit"]
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(html.Div(id="shipping-click-output"), lg=6, className="mb-4"),
                    dbc.Col(html.Div(id="market-click-output"), lg=6, className="mb-4")
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Top Regions by Late Delivery Risk", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "region-chart",
                                        make_bar(
                                            region,
                                            "late_delivery_rate",
                                            "order_region",
                                            hover_data=["total_orders", "late_orders", "total_profit"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Top Countries by Late Delivery Risk", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "country-chart",
                                        make_bar(
                                            country,
                                            "late_delivery_rate",
                                            "order_country",
                                            hover_data=["total_orders", "late_orders", "total_profit"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    )
                ]
            )
        ]
    )


def product_page():
    category = read_table("late_by_category")
    top_products = read_table("top_products_by_sales")
    risky_products = read_table("risky_products")

    return html.Div(
        [
            page_title(
                "Product and Category Analysis",
                "This page connects product categories and products with sales performance and delivery risk."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Top Categories by Sales", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "category-sales-chart",
                                        make_bar(
                                            category.sort_values("total_sales", ascending=False).head(12),
                                            "total_sales",
                                            "category_name",
                                            hover_data=["total_orders", "late_delivery_rate", "total_profit"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Top Categories by Late Risk", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "category-risk-chart",
                                        make_bar(
                                            category.sort_values("late_delivery_rate", ascending=False).head(12),
                                            "late_delivery_rate",
                                            "category_name",
                                            hover_data=["total_orders", "late_orders", "total_sales"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Top Products by Sales", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "top-products-sales-chart",
                                        make_bar(
                                            top_products.head(12),
                                            "total_sales",
                                            "product_name",
                                            hover_data=["category_name", "total_orders", "late_delivery_rate"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("High Sales and High Risk Products", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "risky-products-chart",
                                        make_bar(
                                            risky_products.head(12),
                                            "late_delivery_rate",
                                            "product_name",
                                            hover_data=["category_name", "total_sales", "total_orders"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    )
                ]
            )
        ]
    )


def profit_page():
    profit = read_table("profit_impact")
    loss_market = read_table("loss_by_market")
    discount = read_table("discount_profit_summary")
    profit_category = read_table("profit_margin_by_category")

    return html.Div(
        [
            page_title(
                "Profitability Impact",
                "This page shows how delivery outcomes, discounts, and product categories affect profitability."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Profit by Delivery Status", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "profit-status-chart",
                                        make_bar(
                                            profit,
                                            "delivery_status",
                                            "total_profit",
                                            hover_data=["total_orders", "loss_orders", "loss_rate"]
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Loss Orders by Market", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "loss-market-chart",
                                        make_bar(
                                            loss_market,
                                            "market",
                                            "loss_rate",
                                            hover_data=["total_orders", "loss_orders", "total_profit"]
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    )
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Discount vs Profitability", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "discount-profit-chart",
                                        make_bar(
                                            discount,
                                            "discount_level",
                                            "loss_rate",
                                            hover_data=["total_orders", "average_discount_rate", "total_profit"]
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Profit Margin by Category", className="fw-bold mb-3", style={"fontSize": "18px", "color": TEXT_DARK}),
                                    graph_component(
                                        "profit-category-chart",
                                        make_bar(
                                            profit_category,
                                            "average_profit_margin",
                                            "category_name",
                                            hover_data=["total_orders", "total_sales", "total_profit"],
                                            orientation="h"
                                        )
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=6,
                        className="mb-4"
                    )
                ]
            )
        ]
    )


def prediction_page():
    options = get_prediction_options()

    return html.Div(
        [
            page_title(
                "Late Delivery Risk Prediction",
                "Enter a new order profile and let the trained model estimate its late delivery risk."
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            input_dropdown("Payment Type", "pred-type", options["type"], "DEBIT"),
                                            input_dropdown("Shipping Mode", "pred-shipping-mode", options["shipping_mode"], "Standard Class"),
                                            input_dropdown("Market", "pred-market", options["market"])
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            input_dropdown("Order Region", "pred-order-region", options["order_region"]),
                                            input_dropdown("Order Country", "pred-order-country", options["order_country"]),
                                            input_dropdown("Order State", "pred-order-state", options["order_state"])
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            input_dropdown("Category Name", "pred-category-name", options["category_name"]),
                                            input_dropdown("Customer Segment", "pred-customer-segment", options["customer_segment"], "Consumer"),
                                            input_dropdown("Department Name", "pred-department-name", options["department_name"], "Fitness")
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            input_number("Sales", "pred-sales", 300, 0),
                                            input_number("Discount Rate", "pred-discount-rate", 0.05, 0),
                                            input_number("Order Item Discount", "pred-discount", 10, 0)
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            input_number("Quantity", "pred-quantity", 1, 1),
                                            input_number("Scheduled Shipping Days", "pred-scheduled-days", 4, 0),
                                            input_number("Item / Product Price", "pred-item-price", 300, 0)
                                        ]
                                    ),
                                    dbc.Button(
                                        "Predict Risk",
                                        id="predict-button",
                                        color="success",
                                        size="lg",
                                        style={
                                            "borderRadius": "14px",
                                            "fontWeight": "700",
                                            "padding": "12px 24px"
                                        }
                                    )
                                ]
                            ),
                            style=CARD_STYLE
                        ),
                        lg=8,
                        className="mb-4"
                    ),
                    dbc.Col(
                        info_card(
                            "Decision Meaning",
                            "If the model predicts high risk, managers can prioritize the order, monitor it closely, or consider a different shipping mode. If the model predicts low risk, the order can continue under standard monitoring.",
                            SECONDARY
                        ),
                        lg=4,
                        className="mb-4"
                    )
                ]
            ),
            html.Div(id="prediction-output")
        ]
    )


def render_page(page_name):
    if page_name == "overview":
        return overview_page()
    if page_name == "delivery":
        return delivery_page()
    if page_name == "product":
        return product_page()
    if page_name == "profit":
        return profit_page()
    if page_name == "prediction":
        return prediction_page()
    return overview_page()


def create_layout():
    return html.Div(
        style={
            "backgroundColor": BG_COLOR,
            "minHeight": "100vh",
            "padding": "0"
        },
        children=[
            dcc.Store(id="active-page", data="overview"),
            dbc.Row(
                className="g-0",
                children=[
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "SC Risk DSS",
                                            style={
                                                "color": "white",
                                                "fontWeight": "800",
                                                "marginBottom": "6px"
                                            }
                                        ),
                                        html.P(
                                            "Supply Chain Delivery Risk Decision Support System",
                                            style={
                                                "color": "#D1D5DB",
                                                "fontSize": "14px",
                                                "marginBottom": "18px",
                                                "lineHeight": "1.6"
                                            }
                                        )
                                    ]
                                ),
                                html.Div(
                                    [
                                        sidebar_button("Executive Overview", "nav-overview", "success"),
                                        sidebar_button("Delivery Risk Analysis", "nav-delivery", "secondary"),
                                        sidebar_button("Product & Category", "nav-product", "secondary"),
                                        sidebar_button("Profitability Impact", "nav-profit", "secondary"),
                                        sidebar_button("Prediction", "nav-prediction", "secondary")
                                    ],
                                    style={"marginBottom": "22px"}
                                ),
                              
                            ],
                            style={
                                "background": SIDEBAR_BG,
                                "minHeight": "100vh",
                                "padding": "26px 18px"
                            }
                        ),
                        md=3,
                        lg=2
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            "Big Data Decision Support Dashboard",
                                            style={
                                                "fontSize": "28px",
                                                "fontWeight": "800",
                                                "color": TEXT_DARK,
                                                "marginBottom": "6px"
                                            }
                                        ),
                                        html.Div(
                                            "Interactive analytics, profitability insights, and late delivery prediction.",
                                            style={
                                                "fontSize": "15px",
                                                "color": TEXT_MUTED
                                            }
                                        )
                                    ],
                                    style={
                                        "background": "white",
                                        "border": f"1px solid {BORDER}",
                                        "borderRadius": "20px",
                                        "padding": "22px 24px",
                                        "marginBottom": "24px",
                                        "boxShadow": "0 8px 24px rgba(31, 41, 55, 0.06)"
                                    }
                                ),
                                html.Div(id="page-content", children=overview_page())
                            ],
                            style={"padding": "26px"}
                        ),
                        md=9,
                        lg=10
                    )
                ]
            )
        ]
    )