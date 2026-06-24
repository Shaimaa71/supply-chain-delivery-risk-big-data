import os
from pathlib import Path

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import html
from dotenv import load_dotenv
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BG_COLOR = "#F7F4EE"
CARD_BG = "#FFFFFF"
SIDEBAR_BG = "#1F2937"
SIDEBAR_SOFT = "#374151"
PRIMARY = "#1F7A6C"
SECONDARY = "#D9A441"
ACCENT = "#C97B63"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#6B7280"
BORDER = "#E5E7EB"

CHART_COLORS = [
    "#1F7A6C",
    "#D9A441",
    "#C97B63",
    "#4C6FFF",
    "#8B5CF6",
    "#F97316",
    "#10B981",
    "#EF4444"
]

CARD_STYLE = {
    "background": CARD_BG,
    "border": f"1px solid {BORDER}",
    "borderRadius": "20px",
    "boxShadow": "0 8px 24px rgba(31, 41, 55, 0.08)"
}

INPUT_STYLE = {
    "borderRadius": "14px",
    "border": f"1px solid {BORDER}"
}


def get_database_engine():
    load_dotenv(PROJECT_ROOT / ".env")

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "supply_chain_db")
    user = os.getenv("DB_USER", "supply_chain_user")
    password = os.getenv("DB_PASSWORD", "supply_chain_pass")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    return create_engine(url)


def read_table(table_name):
    engine = get_database_engine()
    return pd.read_sql(f"SELECT * FROM dashboard.{table_name};", engine)


def format_number(value):
    if value is None:
        return "0"

    try:
        value = float(value)
    except Exception:
        return str(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"
    if value.is_integer():
        return f"{int(value)}"
    return f"{value:.2f}"


def page_title(title, subtitle):
    return html.Div(
        [
            html.H2(
                title,
                style={
                    "color": TEXT_DARK,
                    "fontWeight": "800",
                    "marginBottom": "6px"
                }
            ),
            html.P(
                subtitle,
                style={
                    "color": TEXT_MUTED,
                    "marginBottom": "0"
                }
            )
        ],
        style={"marginBottom": "22px"}
    )


def kpi_card(title, value, note, color):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div(
                            title,
                            style={
                                "fontSize": "13px",
                                "fontWeight": "700",
                                "color": TEXT_MUTED,
                                "marginBottom": "10px"
                            }
                        ),
                        html.Div(
                            value,
                            style={
                                "fontSize": "30px",
                                "fontWeight": "800",
                                "color": TEXT_DARK,
                                "lineHeight": "1.1"
                            }
                        ),
                        html.Div(
                            note,
                            style={
                                "fontSize": "12px",
                                "color": color,
                                "fontWeight": "700",
                                "marginTop": "10px"
                            }
                        )
                    ]
                )
            ]
        ),
        style={
            **CARD_STYLE,
            "borderTop": f"5px solid {color}",
            "height": "100%"
        }
    )


def chart_card(title, figure, graph_id):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title,
                    style={
                        "fontSize": "18px",
                        "fontWeight": "800",
                        "color": TEXT_DARK,
                        "marginBottom": "12px"
                    }
                ),
                dbc.Spinner(
                    dbc.CardBody(
                        [],
                        style={"padding": "0"}
                    ),
                    size="sm",
                    color="secondary"
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[
                        dbc.Container(
                            fluid=True,
                            className="px-0",
                            children=[]
                        )
                    ]
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[
                        dbc.CardBody([], style={"display": "none"})
                    ]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"display": "none"}
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    [],
                    style={"padding": "0"},
                    children=[]
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"}
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                ),
                dbc.CardBody(
                    children=[],
                    style={"padding": "0"},
                )
            ]
        ),
        style=CARD_STYLE,
        className="h-100"
    )


def graph_component(graph_id, figure):
    from dash import dcc

    return dcc.Graph(
        id=graph_id,
        figure=figure,
        config={"displayModeBar": True},
        style={"height": "380px"}
    )


def info_card(title, text, color):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    title,
                    style={
                        "fontWeight": "800",
                        "fontSize": "17px",
                        "color": TEXT_DARK,
                        "marginBottom": "10px"
                    }
                ),
                html.P(
                    text,
                    style={
                        "color": TEXT_MUTED,
                        "marginBottom": "0",
                        "lineHeight": "1.7"
                    }
                )
            ]
        ),
        style={
            **CARD_STYLE,
            "borderLeft": f"6px solid {color}",
            "height": "100%"
        }
    )


def make_bar(df, x, y, color=None, orientation="v", hover_data=None):
    if df.empty:
        return px.bar(template="plotly_white")

    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        orientation=orientation,
        hover_data=hover_data,
        color_discrete_sequence=CHART_COLORS,
        template="plotly_white"
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="closest",
        clickmode="event+select",
        font=dict(color=TEXT_DARK, size=13),
        legend_title_text=""
    )

    return fig


def make_pie(df, names, values):
    if df.empty:
        return px.pie(template="plotly_white")

    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.45,
        color_discrete_sequence=CHART_COLORS,
        template="plotly_white"
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(color=TEXT_DARK, size=13),
        legend_title_text=""
    )

    return fig


def dropdown_options(values):
    result = []
    for value in values:
        if pd.notna(value):
            result.append(str(value))
    result = sorted(list(set(result)))
    return [{"label": value, "value": value} for value in result]


def get_prediction_options():
    shipping = read_table("late_by_shipping_mode")
    market = read_table("late_by_market")
    region = read_table("late_by_region")
    category = read_table("late_by_category")

    return {
        "shipping_mode": dropdown_options(shipping["shipping_mode"]),
        "market": dropdown_options(market["market"]),
        "order_region": dropdown_options(region["order_region"]),
        "category_name": dropdown_options(category["category_name"]),
        "type": dropdown_options(["DEBIT", "TRANSFER", "CASH", "PAYMENT"]),
        "customer_segment": dropdown_options(["Consumer", "Corporate", "Home Office"]),
        "department_name": dropdown_options(["Fitness", "Fan Shop", "Apparel", "Golf", "Footwear", "Outdoors", "Technology"]),
        "order_country": dropdown_options(["United States", "India", "Australia", "Indonesia", "Mexico", "France", "Germany", "Brazil"]),
        "order_state": dropdown_options(["California", "New York", "Texas", "Queensland", "Java Occidental", "Rajastán", "England", "Ile-de-France"])
    }