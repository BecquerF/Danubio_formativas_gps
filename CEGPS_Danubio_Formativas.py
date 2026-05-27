import io
import base64
from pathlib import Path
import pandas as pd
import plotly.express as px
import dash
import dash_auth
from dash import Dash, dcc, html, dash_table, Input, Output, no_update
from openpyxl.drawing.image import Image as ExcelImage

# Leer datos
df = pd.read_excel("GPS_Formativas_2026.xlsx")
df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

fecha_max = df["Date"].max()

ultimos21 = fecha_max - pd.Timedelta(days=21)
ultimos7 = fecha_max - pd.Timedelta(days=7)

# Eliminar columnas innecesarias
columnas_eliminar = [
    "Period Number",
    "Work/Rest Ratio",
    "Max Heart Rate",
    "Avg Heart Rate",
    "Max HR (% Max)",
    "Avg HR (% Max)",
    "HR Exertion",
    "Red Zone",
    "Heart Rate Band 1 Duration",
    "Heart Rate Band 2 Duration",
    "Heart Rate Band 3 Duration",
    "Heart Rate Band 5 Duration",
    "Heart Rate Band 6 Duration",
    "Energy",
    "High Metabolic Load Distance",
    "Standing Distance",
    "Walking Distance",
    "Jogging Distance",
    "Running Distance",
    "Athlete Participation Tags"
]

df = df.drop(columns=columnas_eliminar, errors="ignore")

app = Dash(__name__)
app.config.suppress_callback_exceptions = True
server = app.server
VALID_USERNAME_PASSWORD_PAIRS = {
    "Danubioformativas": "danubio2026"
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
app.title = "DATA LOAD - Sports Performance Platform"

metricas = [
    "Distance",
    "Meterage Per Minute",
    "Player Load",
    "Player Load Per Minute",
    "Max Velocity",
    "Accel + Decel Efforts",
    "Accel + Decel Efforts Per Minute",
    "High Speed Distance",
    "High Speed Distance Per Minute",
    "High Speed Efforts",
    "Sprint Distance",
    "Sprint Dist Per Min",
    "Sprint Efforts",
    "Impacts"
]

# ======================================================
# ACTIVIDAD COMPARATIVA INDIVIDUAL
# ======================================================

metricas_base = metricas.copy()

# Promedios por jugador
df_promedios = (
    df.groupby("Player Name")[metricas_base]
      .mean()
      .reset_index()
)

# Renombrar columnas de promedio
df_promedios.rename(
    columns={col: f"{col} Prom" for col in metricas_base},
    inplace=True
)

# Acumulados por jugador
df_acumulados = (
    df.groupby("Player Name")[metricas_base]
      .sum()
      .reset_index()
)

# Unir ambos DataFrames
df_Actividad_Comparativa_Individual = pd.merge(
    df_acumulados,
    df_promedios,
    on="Player Name"
)

# Ordenar columnas
orden = ["Player Name"]
for m in metricas_base:
    orden.extend([m, f"{m} Prom"])

df_Actividad_Comparativa_Individual = df_Actividad_Comparativa_Individual[orden]

# ======================================================

referencias = [
    "Category",
    "Player Name",
    "Athlete Tags",
    "Game Tags",
    "Period Tags"
]

tab_titles = {
    "comparativas": "Comparativo",
    "cronologico": "Cronológico",
    "actividad": "Actividad_por_Jugador",
    "actividad_comparativa": "Actividad_Comparativa_Individual",
    "acwr": "ACWR_Zona_Segura",
}

LOGO_PATH = Path("assets/logo_dataload_2.png")
LOGO_BASE64 = ""
if LOGO_PATH.exists():
    with open(LOGO_PATH, "rb") as logo_file:
        LOGO_BASE64 = base64.b64encode(logo_file.read()).decode("ascii")

from datetime import datetime, timedelta

def summarize_items(items, max_items=3, default="todas"):
    if not items:
        return default
    labels = [str(item) for item in items if item is not None]
    if len(labels) == 0:
        return default
    if len(labels) <= max_items:
        return " / ".join(labels)
    return " / ".join(labels[:max_items]) + f" +{len(labels)-max_items}"


def build_chart_title(tab, categorias, metricas, referencia):
    categoria_text = summarize_items(categorias, max_items=3)
    metrica_text = summarize_items(metricas, max_items=3)

    if tab == "comparativas":
        title = f"Comparativo de {metrica_text} por {referencia}"
        if categorias:
            title += f" - Categoría(s): {categoria_text}"
        return title

    if tab == "cronologico":
        title = f"Evolución cronológica de {metrica_text}"
        if categorias:
            title += f" - Categoría(s): {categoria_text}"
        return title

    if tab == "actividad":
        title = "Actividad por jugador"
        if categorias:
            title += f" - Categoría(s): {categoria_text}"
        return title

    if tab == "acwr":
        title = "ACWR - Últimos 7 días vs 21 días"
        if categorias:
            title += f" - Categoría(s): {categoria_text}"
        return title
    
    if tab == "actividad_comparativa":
        title = "Actividad comparativa individual"
        if categorias:
            title += f" - Categoría(s): {categoria_text}"
        return title

    return tab_titles.get(tab, tab)


def build_download_metadata(tab, categorias, metricas, referencia):
    item_name = tab_titles.get(tab, tab)
    if item_name is None:
        item_name = tab
    category_text = summarize_items(categorias, max_items=5)
    metric_text = summarize_items(metricas, max_items=5)
    printed_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    metadata = (
        f"Descargado: {item_name}\n"
        f"Impresión: {printed_at}\n"
        f"Categorías: {category_text}\n"
        f"Métricas: {metric_text}\n"
        f"Comparar por: {referencia}\n"
    )
    return item_name, metadata, printed_at

ultima_actualizacion = (
    datetime.now() - timedelta(hours=3)
).strftime(
    "%d/%m/%Y - %H:%M"
)

app.layout = html.Div([

    # ===== TÍTULO =====

    html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Img(
                                src="/assets/logo_dataload_2.png",
                                style={
                                    "width": "180px",
                                    "height": "auto",
                                    "objectFit": "contain",
                                    "gap": "1px 4px",
                                    "position": "relative",
                                    "left": "1px",
                                    "borderRadius": "1px"
                                }
                            )
                        ],
                        style={
                            "flex": "0 0 140px",
                            "display": "flex",
                            "alignItems": "center"
                        }
                    ),
                    html.Div(
                        [
                            html.H1(
                                "CARGA EXTERNA - DANUBIO FORMATIVAS 2026",
                                style={
                                    "color": "#ffffff",
                                    "textAlign": "center",
                                    "fontSize": "36px",
                                    "fontWeight": "700",
                                    "fontFamily": "'Clash Display Semibold'",
                                    "lineHeight": "1.50",
                                    "letterSpacing": "0.02em",
                                    "margin": "0",
                                    "linecolor": "#89bcef",
                                    "boxSizing": "border-box"
                                }
                            ),
                            html.P(
                                "Plataforma de análisis deportivo",
                                style={
                                    "color": "#d0f0d9",
                                    "margin": "10px 0 0",
                                    "fontSize": "15px",
                                    "textAlign": "center",
                                    "fontFamily": "'Manrope Light', sans-serif",
                                    "lineHeight": "1.4"
                                }
                            )
                        ],
                        style={
                            "flex": "1",
                            "minWidth": "0"
                        }
                    )
                ],
                style={
                    "flex":"1",
                    "height":"100hvh",
                    "width": "100%",
                    "padding": "18px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "gap": "18px",
                    "boxSizing": "border-box"
                }
            )
        ],
        style={
            "width": "100%",
            "paddingTop": "10px",
            "paddingBottom": "4px"
        }
    ),

    # ===== CONTENIDO GENERAL =====

    html.Div([

        # ==================================================
        # SIDEBAR IZQUIERDO
        # ==================================================

        html.Div([

            # MENÚ

            html.Div([

                html.H2(
                    "MENÚ",
                    style={
                        "color":"#edf1f2",
                        "fontSize":"22px",
                        "fontWeight":"700",
                        "textAlign":"center",
                        "marginBottom":"20px"
                    }
                ),

                dcc.Tabs(
    id="tabs",
    value="actividad",
    vertical=True,
    className="tab-menu",
    style={
        "width":"100%",
        "background":"transparent",
        "border":"none"
    },

    children=[

        dcc.Tab( 
            label="ACTIVIDAD",
            value="actividad",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "marginBottom":"8px"
            },

            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "backgroundColor":"#011c24",
                "marginBottom":"8px"
            }
        ),

        dcc.Tab(
            label="ACTIVIDAD COMPARATIVA INDIVIDUAL",
            value="actividad_comparativa",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "marginBottom":"8px"
            },

            selected_style={
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "backgroundColor":"#011c24",
                "marginBottom":"8px"
            }
        ),

        dcc.Tab(
            label="ACWR",
            value="acwr",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "marginBottom":"8px"
            },
            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "gap":"4px",
                "padding":"12px 12px",
                "backgroundColor":"#011c24",
                "marginBottom":"8px"
            }
        ),

        dcc.Tab(
            label="COMPARATIVO",
            value="comparativas",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "marginBottom":"8px"
            },
            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "backgroundColor":"#011c24",
                "marginBottom":"8px"
            }
        ),

        dcc.Tab(
            label="CRONOLÓGICO",
            value="cronologico",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "marginBottom":"8px"
            },
            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "borderLeft":"none",
                "borderRight":"none",
                "borderBottom":"none",
                "gap":"4px",
                "padding":"12px 12px",
                "backgroundColor":"#011c24",
                "marginBottom":"8px"
            }
        )

    ]
),

                html.Div(
                    f"Última actualización: {ultima_actualizacion}",
                    style={
                        "color":"#dcdcdc",
                        "fontSize":"9px",
                        "marginTop":"12px",
                        "padding":"0px 3px",
                        "textAlign":"center"
                    }
                )

            ],

            style={
                "padding":"12px",
                "width":"160px",
                "background":"linear-gradient(180deg,#000c0f,#011c24)",
                "borderRadius":"12px",
                "border":"1px solid rgba(137,188,239,.18)"
                })
            ],

        style={
            "display":"flex",
            "flexDirection":"column",
            "width":"160px",
            "minWidth":"160px",
            "gap":"4px 4px",
            "position":"sticky",
            "top":"10px",
            "alignSelf":"flex-start"
        }),

        # ==================================================
        # CONTENIDO CENTRAL
        # ==================================================

        html.Div([

            dcc.Download(id="download-graph"),
            dcc.Download(id="download-table"),

            # GRÁFICO

            html.Div(    id="contenido-tab",
    style={
        "displey":"flex",
        "flex":"1",
        "padding":"24px",
        "gap":"18px",
        "width":"100%",
        "maxWidth":"1000px",
        "minWidth":"1000px",
        "height":"600px",

        "overflowX":"hidden",
        "overflowY":"hidden",

        "position":"relative",
        "boxShadow":"0 18px 40px rgba(1, 28, 36, 1)",
    }
),

            # BOTONES DE DESCARGA

            html.Div([

                html.Button(
                    html.Img(
                        src="/assets/icon-download-png.svg",
                        style={"width":"16px"}
                    ),
                    id="download-graph-png",
                    className="download-btn"
                ),

                html.Button(
                    html.Img(
                        src="/assets/icon-download-pdf.svg",
                        style={"width":"16px"}
                    ),
                    id="download-graph-pdf",
                    className="download-btn"
                ),

                html.Button(
                    html.Img(
                        src="/assets/icon-download-csv.svg",
                        style={"width":"16px"}
                    ),
                    id="download-table-csv",
                    className="download-btn"
                ),

                html.Button(
                    html.Img(
                        src="/assets/icon-download-xlsx.svg",
                        style={"width":"16px"}
                    ),
                    id="download-table-xlsx",
                    className="download-btn"
                )

            ],

            style={
                "display":"flex",
                "justifyContent":"center",
                "gap":"12px",
                "marginTop":"10px",
                "paddingBottom":"18px"
            })

        ],

        style={
            "display":"flex",
            "flexDirection":"column",
            "flex":"1",
            "gap":"18px"
        }),

            html.Div(
                [
                    html.Div(
                        [
                            html.H4(
                                "Categorías",
                                style={
                                    "color":"#a3e3d0",
                                    "fontSize":"13px",
                                    "fontWeight":"600",
                                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                                    "marginBottom":"12px"
                                }
                            ),
                            dcc.Checklist(
                                id="categoria",
                                options=[
                                    {"label":c, "value":c}
                                    for c in sorted(df["Category"].dropna().unique())
                                ],
                                inline=False,
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                                    "gap": "8px"
                                },
                                labelStyle={
                                    "color":"white",
                                    "fontSize":"10px",
                                    "marginBottom":"6px"
                                }
                            )
                        ],
                        className="filter-card",
                        style={
                            "padding":"14px"
                        }
                    ),
                    html.Div(
                        [
                            html.H4(
                                "Fecha de actividad",
                                style={
                                    "color":"#a3e3d0",
                                    "fontSize":"13px",
                                    "fontWeight":"500",
                                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                                    "padding":"12px 12px",
                                    "marginBottom":"12px"
                                }
                            ),
                            dcc.DatePickerSingle(
                                id="fecha-actividad",
                                date=fecha_max.date(),
                                min_date_allowed=df["Date"].min().date(),
                                max_date_allowed=df["Date"].max().date(),
                                display_format="DD/MM/YYYY",
                                style={
                                    "width": "100%",
                                    "backgroundColor": "#011c24",
                                    "color": "#f5f5f5",
                                    "border": "1px solid rgba(137,188,239,0.22)",
                                    "borderRadius": "8px",
                                    "padding": "8px 8px"
                                }
                            )
                        ],
                        id="actividad-fecha-container",
                        className="filter-card",
                        style={
                            "display": "none",
                            "padding":"8px 8px",
                            "marginBottom":"2px"
                        }
                    ),
                    html.Div(
                        [
                            html.H4(
                                "Métricas",
                                style={
                                    "color":"#a3e3d0",
                                    "fontSize":"13px",
                                    "fontWeight":"600",
                                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                                    "marginBottom":"12px"
                                }
                            ),
                            dcc.Checklist(
                                id="metrica",
                                options=[
                                    {"label":m, "value":m}
                                    for m in metricas
                                ],
                                value=["Distance"],
                                inline=False,
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                                    "gap": "5px"
                                },
                                labelStyle={
                                    "color":"white",
                                    "fontSize":"10px",
                                    "marginBottom":"2px"
                                }
                            )
                        ],
                        className="filter-card",
                        style={
                            "padding":"14px"
                        }
                    ),
                    html.Div(
                        [
                            html.H4(
                                "Comparar por",
                                style={
                                    "color":"#a3e3d0",
                                    "fontSize":"13px",
                                    "fontWeight":"600",
                                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                                    "marginBottom":"12px"
                                }
                            ),
                            dcc.RadioItems(
                                id="referencia",
                                options=[
                                    {"label":r, "value":r}
                                    for r in referencias
                                ],
                                value="Category",
                                style={
                                    "display": "grid",
                                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                                    "gap": "10px"
                                },
                                labelStyle={
                                    "color":"white",
                                    "fontSize":"10px",
                                    "marginBottom":"2px"
                                }
                            )
                        ],
                        className="filter-card",
                        style={
                            "padding":"16px"
                        }
                    ),
                    html.Div(
                        [
                            html.H4(
                                "Filtrar por",
                                style={
                                    "color":"#a3e3d0",
                                    "fontSize":"13px",
                                    "fontWeight":"600",
                                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                                    "marginBottom":"12px"
                                }
                            ),

                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.P(
                                                "Jugador",
                                                style={
                                                    "color":"#f5f5f5",
                                                    "fontSize":"10px",
                                                    "marginBottom":"6px"
                                                }
                                            ),
                                            dcc.Dropdown(
                                                id="jugador",
                                                options=[
                                                    {"label": x, "value": x}
                                                    for x in sorted(
                                                        df["Player Name"]
                                                        .dropna()
                                                        .unique()
                                                    )
                                                ],
                                                multi=True
                                            )
                                        ]
                                    ),

                                    html.Div(
                                        [
                                            html.P(
                                                "Athlete Tags",
                                                style={
                                                    "color":"#f5f5f5",
                                                    "fontSize":"10px",
                                                    "marginBottom":"6px"
                                                }
                                            ),
                                            dcc.Dropdown(
                                                id="athlete",
                                                options=[
                                                    {"label": x, "value": x}
                                                    for x in sorted(
                                                        df["Athlete Tags"]
                                                        .dropna()
                                                        .unique()
                                                    )
                                                ],
                                                multi=True
                                            )
                                        ]
                                    ),

                                    html.Div(
                                        [
                                            html.P(
                                                "Game Tags",
                                                style={
                                                    "color":"#f5f5f5",
                                                    "fontSize":"10px",
                                                    "marginBottom":"6px"
                                                }
                                            ),
                                            dcc.Dropdown(
                                                id="gametag",
                                                options=[
                                                    {"label": x, "value": x}
                                                    for x in sorted(
                                                        df["Game Tags"]
                                                        .dropna()
                                                        .unique()
                                                    )
                                                ],
                                                multi=True
                                            )
                                        ]
                                    ),

                                    html.Div(
                                        [
                                            html.P(
                                                "Period Tags",
                                                style={
                                                    "color":"#f5f5f5",
                                                    "fontSize":"10px",
                                                    "marginBottom":"6px"
                                                }
                                            ),
                                            dcc.Dropdown(
                                                id="periodtag",
                                                options=[
                                                    {"label": x, "value": x}
                                                    for x in sorted(
                                                        df["Period Tags"]
                                                        .dropna()
                                                        .unique()
                                                    )
                                                ],
                                                multi=True
                                            )
                                        ]
                                    )
                                ],
                                className="filter-card",
                                style={
                                    "padding": "16px"
                                }
                            )
                        ],
                        className="filter-card",
                        style={
                            "padding": "16px"
                        }
                    )
                ],
                className="sidebar-panel sidebar-right-panel",
                style={
                    "flex": "0 0 auto",
                    "width": "220px",
                    "minWidth": "220px",
                    "padding": "24px",
                    "backgroundColor": "#011c24",
                    "borderRadius": "24px",
                    "border": "1px solid rgba(137, 188, 239, 0.16)",
                    "boxShadow": "0 18px 48px rgba(0,0,0,0.35)",
                    "position": "relative",
                    "top": "10px",
                    "maxHeight": "100vh",
                    "overflowY": "auto"
                }
            )
        ],
        style={
            "display": "flex",
            "alignItems": "flex-start",
            "gap": "18px",
            "width": "100%",
            "maxHeight": "calc(100vh - 100px)"
        }
    )
],
style={
    "color": "#ffffff",
    "padding": "28px 24px 36px",
    "fontFamily": "'Clash Display Semibold', 'Segoe UI', sans-serif",
    "margin": "0",
    "maxHeight": "calc(100vh - 100px)",
    "overflow": "auto"
}
)

@app.callback(
    Output("actividad-fecha-container","style"),
    Input("tabs","value")
)
def toggle_actividad_fecha(tab):
    if tab in ["actividad", "actividad_comparativa"]:
        return {"display": "block", "marginTop": "10px"}
    return {"display": "none"}

@app.callback(
    Output("contenido-tab","children"),

    Input("tabs","value"),
    Input("categoria","value"),
    Input("metrica","value"),
    Input("referencia","value"),
    Input("jugador","value"),
    Input("athlete","value"),
    Input("gametag","value"),
    Input("periodtag","value"),
    Input("fecha-actividad","date")
)

def actualizar_tab(

    tab,
    categorias,
    metricas,
    referencia,
    jugadores,
    athlete,
    gametags,
    periodtags,
    fecha_actividad
):

    dff=df.copy()

    if categorias:
        dff=dff[
            dff["Category"].isin(categorias)
        ]

    if jugadores:
        dff=dff[
            dff["Player Name"].isin(jugadores)
        ]

    if athlete:
        dff=dff[
            dff["Athlete Tags"].isin(athlete)
        ]

    if gametags:
        dff=dff[
            dff["Game Tags"].isin(gametags)
        ]

    if periodtags:
        dff=dff[
            dff["Period Tags"].isin(periodtags)
        ]

    metricas = metricas or ["Distance"]
    referencia = referencia or "Category"
    title_text = build_chart_title(tab, categorias, metricas, referencia)

    # COMPARATIVAS
    if tab=="comparativas":

        promedio=(

            dff
            .groupby(referencia)[metricas]
            .mean()
            .reset_index()
        )

        promedio=pd.melt(

            promedio,
            id_vars=[referencia],

            value_vars=metricas,

            var_name="Métrica",
            value_name="Valor"
        )
        
        fig=px.bar(

            promedio,

            x="Valor",
            y=referencia,

            color="Métrica",

            orientation="h",
            
            barmode="group",


            color_discrete_sequence=[
                "#edf1f2",
                "#f0c1f7",
                "#a3e3d0",
                "#89bcef",
                "#48f788",
                "#72d2e4"
            ],
            template="plotly_dark"
            
        )

        fig.update_traces(
            marker=dict(
                line=dict(width=1, color="#ffffff")
            ),
            opacity=0.95,
            hoverlabel=dict(
                bgcolor="#0c0d0f",
                font_size=12,
                font_color="#f5f5f5"
            )
        )

        fig.update_layout(
            paper_bgcolor="#0b0c0e",
            plot_bgcolor="#0b0c0e",
            title={
                "text": title_text,
                "font": {
                    "color": "#f5f5f5",
                    "family": "'Clash Display Semibold', 'Helvetica Neue'",
                    "size": 22
                }
            },
            legend=dict(
                bgcolor="rgba(11,12,14,0.75)",
                bordercolor="#89bcef",
                borderwidth=1
            )
        )

        if LOGO_BASE64:
            fig.add_layout_image(
                dict(
                    source="data:image/png;base64," + LOGO_BASE64,
                    xref="paper",
                    yref="paper",
                    x=0.98,
                    y=0.08,
                    xanchor="right",
                    yanchor="bottom",
                    sizex=0.12,
                    sizey=0.10,
                    opacity=0.7,
                    layer="above"
                )
            )

        fig.update_xaxes(
            showgrid=True,
            gridcolor="rgba(137,188,239,0.18)",
            zerolinecolor="rgba(255,255,255,0.08)",
            linecolor="#89bcef",
            tickfont_color="#f5f5f5",
            title_font_color="#a3e3d0"
        )

        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(137,188,239,0.18)",
            zerolinecolor="rgba(255,255,255,0.08)",
            linecolor="#89bcef",
            tickfont_color="#f5f5f5",
            title_font_color="#a3e3d0"
        )

        return html.Div(
            dcc.Graph(
                figure=fig,
                style={"width":"100%","height":"100%"}
            ),
            style={
                "border":"1px solid rgba(137,188,239,0.18)",
                "borderRadius":"18px",
                "overflow":"hidden",
                "background":"#0b0c0e",
                "boxShadow":(
                    "0 0 20px rgba(72,247,136,0.10), "
                    "0 0 50px rgba(137,188,239,0.08), "
                    "0 18px 40px rgba(0,0,0,0.35)"
                ),
                "padding":"10px"
            }
        )


        # ACTIVIDAD POR JUGADOR
    elif tab == "actividad":
            fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
            dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]

            columnas_requeridas = [
                "Player Name","Accel + Decel Efforts","Accel + Decel Efforts Per Minute",
                "Distance","Player Load","Max Velocity","Meterage Per Minute",
                "Player Load Per Minute","Sprint Distance","Sprint Efforts","Sprint Dist Per Min",
                "High Speed Distance","High Speed Efforts","High Speed Distance Per Minute","Impacts"
            ]

            columnas_presentes = [c for c in columnas_requeridas if c in dff_fecha.columns]
            columnas_actividad = [{"name": c, "id": c} for c in columnas_presentes]

            estilos_condicionales = []
            for col in columnas_presentes:
                if col != "Player Name" and dff_fecha[col].dtype in ['float64','int64']:
                    max_val = dff_fecha[col].max()
                    min_val = dff_fecha[col].min()
                    rango = max_val - min_val if max_val != min_val else 1

                    estilos_condicionales.append({
                        "if": {"filter_query": f"{{{col}}} >= {max_val * 0.8}", "column_id": col},
                        "backgroundColor": "#017351","color": "white"
                    })
                    estilos_condicionales.append({
                        "if": {"filter_query": f"{{{col}}} >= {min_val + rango * 0.5} && {{{col}}} < {max_val * 0.8}", "column_id": col},
                        "backgroundColor": "#F4C95D","color": "black"
                    })
                    estilos_condicionales.append({
                        "if": {"filter_query": f"{{{col}}} < {min_val + rango * 0.5}", "column_id": col},
                        "backgroundColor": "#A40A1C","color": "white"
                    })

            return html.Div([
                html.H3("Actividad por Jugador", style={"color":"white","textAlign":"center","marginBottom":"20px",
                                                        "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"}),
                html.H4(fecha_dt.strftime("%d/%m/%Y"), style={"color":"#a3e3d0","textAlign":"center","marginBottom":"15px",
                                                            "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"}),
                dcc.Loading(
                    dash_table.DataTable(
                        data=dff_fecha[columnas_presentes].to_dict("records") if columnas_presentes else [],
                        columns=columnas_actividad,
                        filter_action="native",
                        sort_action="native",
                        fixed_columns={"headers": True, "data": 1},
                        page_size=20,
                        style_table={"overflowX":"auto","minWidth":"100%","border":"1px solid rgba(137,188,239,0.18)",
                                    "boxShadow":"0 18px 40px rgba(0,0,0,0.25)"},
                        style_header={"backgroundColor":"#000000","color":"white","fontWeight":"bold","position":"sticky","top":0},
                        style_cell={"backgroundColor":"#1a1a1a","color":"white","fontSize":"11px","textAlign":"center",
                                    "minWidth":"100px","whiteSpace":"normal"},
                        style_data_conditional=estilos_condicionales
                    )
                )
            ])
                        



  
# ACTIVIDAD COMPARATIVA INDIVIDUAL
    elif tab == "actividad_comparativa":
        fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]

        metricas_base = [
            "Distance","Meterage Per Minute","Player Load","Player Load Per Minute",
            "Max Velocity","Accel + Decel Efforts","Accel + Decel Efforts Per Minute",
            "High Speed Distance","High Speed Distance Per Minute","High Speed Efforts",
            "Sprint Distance","Sprint Dist Per Min","Sprint Efforts","Impacts"
        ]

        resumen_fecha = dff_fecha.groupby("Player Name")[metricas_base].sum().reset_index()
        dff_acumulado = dff[dff["Date"].dt.normalize() <= fecha_dt]
        promedio_jugador = dff_acumulado.groupby("Player Name")[metricas_base].mean().reset_index()
        promedio_jugador = promedio_jugador.rename(columns={m: f"{m} Prom" for m in metricas_base})

        tabla_comparativa = resumen_fecha.merge(promedio_jugador, on="Player Name", how="left").fillna(0)

        columnas_comparativa = [{"name": "Player Name", "id": "Player Name"}]
        estilos_condicionales = []

        for m in metricas_base:
            columnas_comparativa.append({"name": m, "id": m, "type": "numeric", "format": {"specifier": ".2f"}})
            columnas_comparativa.append({"name": f"{m} Prom", "id": f"{m} Prom", "type": "numeric", "format": {"specifier": ".2f"}})

            # Calcular umbrales en Python
            for _, row in tabla_comparativa.iterrows():
                prom_val = row[f"{m} Prom"]
                if prom_val > 0:
                    umbral_alto = 1.3 * prom_val
                    umbral_bajo = 0.8 * prom_val

                    estilos_condicionales.append({
                        "if": {"filter_query": f"{{{m}}} > {umbral_alto}", "column_id": m},
                        "backgroundColor": "#017351", "color": "white"
                    })
                    estilos_condicionales.append({
                        "if": {"filter_query": f"{{{m}}} >= {umbral_bajo} && {{{m}}} <= {umbral_alto}", "column_id": m},
                        "backgroundColor": "#e6c200", "color": "black"
                    })
                    estilos_condicionales.append({
                        "if": {"filter_query": f"{{{m}}} < {umbral_bajo}", "column_id": m},
                        "backgroundColor": "#b22222", "color": "white"
                    })

            # Diferenciar columna Prom
            estilos_condicionales.append({
                "if": {"column_id": f"{m} Prom"},
                "backgroundColor": "#2f2f2f", "color": "#d0d0d0", "fontWeight": "bold"
            })

        return html.Div([
            html.H4("Comparativo actual vs promedio",
                    style={"color": "#edf1f2", "fontSize": "14px", "fontWeight": "600",
                        "marginBottom": "12px", "fontFamily": "'Clash Display Semibold', 'Helvetica Neue'"}),
            dcc.Loading(
                dash_table.DataTable(
                    data=tabla_comparativa.to_dict("records"),
                    columns=columnas_comparativa,
                    filter_action="native",
                    sort_action="native",
                    fixed_columns={"headers": True, "data": 1},
                    page_size=20,
                    style_table={"overflowX": "auto", "minWidth": "100%",
                                "border": "1px solid rgba(137,188,239,0.18)",
                                "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"},
                    style_header={"backgroundColor": "#000000", "color": "white",
                                "fontWeight": "bold", "position": "sticky", "top": 0},
                    style_cell={"backgroundColor": "#1a1a1a", "color": "white",
                                "fontSize": "11px", "textAlign": "center",
                                "minWidth": "100px", "whiteSpace": "normal"},
                    style_data_conditional=estilos_condicionales
                )
            )
        ], style={"padding": "22px", "background": "#0b0c0e",
                "border": "1px solid rgba(137,188,239,0.18)", "borderRadius": "24px",
                "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"})



    # ACWR
    
    elif tab=="acwr":
        metricas_acwr = list(dict.fromkeys([

            "Distance",
            "Player Load",
            "Acceleration Efforts",
            "Sprint Distance",
            "High Speed Distance",
            "Sprint Efforts",
            "High Speed Efforts",
            "Impacts"

        ]))

        dff["Player Name"] = (
            dff["Player Name"]
            .astype(str)
            .str.strip()
        )

        ultimos21 = (
            dff["Date"].max()
            - pd.Timedelta(days=21)
        )

        ultimos7 = (
            dff["Date"].max()
            - pd.Timedelta(days=7)
        )

        df21 = dff[
            dff["Date"] >= ultimos21
        ]

        df7 = dff[
            dff["Date"] >= ultimos7
        ]

        cronica = (

            df21
            .groupby("Player Name")[metricas_acwr]
            .mean()
            .reset_index()

        )

        aguda = (

            df7
            .groupby("Player Name")[metricas_acwr]
            .mean()
            .reset_index()

        )

        tabla = cronica.merge(

            aguda,
            on="Player Name",
            how="outer",
            suffixes=("_21", "_7")

        )

        tabla = tabla.loc[
            :,
            ~tabla.columns.duplicated()
        ]

        for m in metricas_acwr:

            tabla[f"{m}_ACWR"] = (

                tabla[f"{m}_7"] /
                tabla[f"{m}_21"]

            ).round(2)

        ratio_columns = [

            f"{m}_ACWR"

            for m in metricas_acwr

        ]

        tabla = tabla[
            ["Player Name"] + ratio_columns
        ].fillna(0)

        return html.Div([

            html.H3(

                "ACWR - Últimos 7 días vs 21 días",

                style={

                    "color":"white",
                    "textAlign":"center",
                    "boxShadow":"0 18px 40px rgba(0,0,0,0.25)"

                }

            ),

            dcc.Loading(

                dash_table.DataTable(

                    data=tabla.to_dict("records"),

                    columns=[

                        {
                            "name":"Player Name",
                            "id":"Player Name"
                        }

                    ] + [

                        {
                            "name":col,
                            "id":col,
                            "type":"numeric",
                            "format":{"specifier":".2f"}
                        }

                        for col in ratio_columns

                    ],
                        filter_action="native",
                        sort_action="native",
                        fixed_columns={"headers": True, "data": 1},
                        style_table={
                            "overflowX": "auto",
                            "minWidth": "100%"
                        },
                        style_header={
                            "backgroundColor": "#0d1620",
                            "color": "#edf1f2",
                            "fontWeight": "bold",
                            "borderBottom": "1px solid rgba(137,188,239,0.2)"
                        },
                        style_cell={
                            "backgroundColor": "#1a1a1a",
                            "color": "white",
                            "fontSize": "11px",
                            "textAlign": "center",
                            "minWidth": "100px",
                            "width": "100px",
                            "maxWidth": "100px",
                            "whiteSpace": "normal"
                        },
                        style_data_conditional=[
                            {
                                "if": {
                                    "filter_query": "{Distance_ACWR} < 0.8",
                                    "column_id": "Distance_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Distance_ACWR} >= 0.8 && {Distance_ACWR} <= 1.3",
                                    "column_id": "Distance_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Distance_ACWR} > 1.3",
                                    "column_id": "Distance_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "black"
                            },
                            {
                                "if": {
                                    "filter_query": "{Player Load_ACWR} < 0.8",
                                    "column_id": "Player Load_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Player Load_ACWR} >= 0.8 && {Player Load_ACWR} <= 1.3",
                                    "column_id": "Player Load_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Player Load_ACWR} > 1.3",
                                    "column_id": "Player Load_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "black"
                            },
                            {
                                "if": {
                                    "filter_query": "{Acceleration Efforts_ACWR} < 0.8",
                                    "column_id": "Acceleration Efforts_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Acceleration Efforts_ACWR} >= 0.8 && {Acceleration Efforts_ACWR} <= 1.3",
                                    "column_id": "Acceleration Efforts_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Acceleration Efforts_ACWR} > 1.3",
                                    "column_id": "Acceleration Efforts_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "black"
                            },
                            {
                                "if": {
                                    "filter_query": "{Sprint Distance_ACWR} < 0.8",
                                    "column_id": "Sprint Distance_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Sprint Distance_ACWR} >= 0.8 && {Sprint Distance_ACWR} <= 1.3",
                                    "column_id": "Sprint Distance_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Sprint Distance_ACWR} > 1.3",
                                    "column_id": "Sprint Distance_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "black"
                            },
                            {
                                "if": {
                                    "filter_query": "{High Speed Distance_ACWR} < 0.8",
                                    "column_id": "High Speed Distance_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{High Speed Distance_ACWR} >= 0.8 && {High Speed Distance_ACWR} <= 1.3",
                                    "column_id": "High Speed Distance_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{High Speed Distance_ACWR} > 1.3",
                                    "column_id": "High Speed Distance_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "black"
                            },
                            {
                                "if": {
                                    "filter_query": "{Sprint Efforts_ACWR} < 0.8",
                                    "column_id": "Sprint Efforts_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Sprint Efforts_ACWR} >= 0.8 && {Sprint Efforts_ACWR} <= 1.3",
                                    "column_id": "Sprint Efforts_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Sprint Efforts_ACWR} > 1.3",
                                    "column_id": "Sprint Efforts_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "black"
                            },
                            {
                                "if": {
                                    "filter_query": "{High Speed Efforts_ACWR} < 0.8",
                                    "column_id": "High Speed Efforts_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{High Speed Efforts_ACWR} >= 0.8 && {High Speed Efforts_ACWR} <= 1.3",
                                    "column_id": "High Speed Efforts_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{High Speed Efforts_ACWR} > 1.3",
                                    "column_id": "High Speed Efforts_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Impacts_ACWR} < 0.8",
                                    "column_id": "Impacts_ACWR"
                                },
                                "backgroundColor": "#A40A1C",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Impacts_ACWR} >= 0.8 && {Impacts_ACWR} <= 1.3",
                                    "column_id": "Impacts_ACWR"
                                },
                                "backgroundColor": "#017351",
                                "color": "white"
                            },
                            {
                                "if": {
                                    "filter_query": "{Impacts_ACWR} > 1.3",
                                    "column_id": "Impacts_ACWR"
                                },
                                "backgroundColor": "#ff5e5e",
                                "color": "white"
                            }
                        ],
                        page_size=20
                    )
                )
            ])

    # CRONOLÓGICO
    elif tab == "cronologico": 
        cronologico = pd.melt(
        dff,
        id_vars=["Date", "Category"],
        value_vars=metricas,
        var_name="Métrica",
        value_name="Valor"
    ) 
        fig = px.scatter(
            cronologico,
        x="Date",
        y="Valor",
        color="Category",
        symbol="Métrica",
        color_discrete_sequence=["#edf1f2", "#f1a3fd", "#a3e3d0", "#89bcef", "#48f788", "#f96e83"],
        template="plotly_dark"
    )

    fig.update_traces(
        marker=dict(size=10, line=dict(width=1, color="#ffffff")),
        selector=dict(mode="markers"),
        hoverlabel=dict(bgcolor="#011c24", font_size=12, font_color="#f5f5f5")
    )

    fig.update_layout(
        title={
            "text": title_text,
            "font": {
                "color": "#f5f5f5",
                "family": "'Clash Display Semibold', 'Helvetica Neue'",
                "size": 22
            }
        },
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"},
        legend=dict(
            bgcolor="rgba(11,12,14,0.75)",
            bordercolor="#89bcef",
            borderwidth=1
        )
    )

    if LOGO_BASE64:
        fig.add_layout_image(
            dict(
                source="data:image/png;base64," + LOGO_BASE64,
                xref="paper",
                yref="paper",
                x=0.99,
                y=0.01,
                xanchor="right",
                yanchor="bottom",
                sizex=0.12,
                sizey=0.10,
                opacity=0.7,
                layer="above"
            )
        )

    fig.update_xaxes(
        tickformat="%d/%m/%Y",
        showgrid=True,
        gridcolor="rgba(137,188,239,0.18)",
        zerolinecolor="rgba(255,255,255,0.08)",
        linecolor="#89bcef",
        tickfont_color="#f5f5f5",
        title_font_color="#a3e3d0"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(137,188,239,0.18)",
        zerolinecolor="rgba(255,255,255,0.08)",
        linecolor="#89bcef",
        tickfont_color="#f5f5f5",
        title_font_color="#a3e3d0"
    )

    return html.Div(
        dcc.Graph(
            figure=fig,
            style={"width": "100%", "height": "100%"}
        ),
        style={
            "border": "1px solid rgba(137,188,239,0.18)",
            "borderRadius": "18px",
            "overflow": "hidden",
            "background": "#0b0c0e",
            "boxShadow": "0 18px 40px rgba(0,0,0,0.25)",
            "padding": "10px"
        }
    )
    
@app.callback(
    Output("download-graph","data"),
    Input("download-graph-png","n_clicks"),
    Input("download-graph-pdf","n_clicks"),
    Input("tabs","value"),
    Input("categoria","value"),
    Input("metrica","value"),
    Input("referencia","value"),
    Input("jugador","value"),
    Input("athlete","value"),
    Input("gametag","value"),
    Input("periodtag","value"),
    Input("fecha-actividad","date")
)
def descargar_grafico(
    n_png,
    n_pdf,
    tab,
    categorias,
    metricas,
    referencia,
    jugadores,
    athlete,
    gametags,
    periodtags,
    fecha_actividad
):
    triggered = dash.callback_context.triggered
    if not triggered:
        return no_update

    trigger_id = triggered[0]["prop_id"].split(".")[0]
    if trigger_id not in ["download-graph-png", "download-graph-pdf"]:
        return no_update

    dff = df.copy()
    if categorias:
        dff = dff[dff["Category"].isin(categorias)]
    if jugadores:
        dff = dff[dff["Player Name"].isin(jugadores)]
    if athlete:
        dff = dff[dff["Athlete Tags"].isin(athlete)]
    if gametags:
        dff = dff[dff["Game Tags"].isin(gametags)]
    if periodtags:
        dff = dff[dff["Period Tags"].isin(periodtags)]

    metricas = metricas or ["Distance"]
    referencia = referencia or "Category"
    item_name, metadata, printed_at = build_download_metadata(tab, categorias, metricas, referencia)

    if tab == "comparativas":
        promedio = (
            dff.groupby(referencia)[metricas].mean().reset_index()
        )
        promedio = pd.melt(
            promedio,
            id_vars=[referencia],
            value_vars=metricas,
            var_name="Métrica",
            value_name="Valor"
        )
        fig = px.bar(
            promedio,
            x="Valor",
            y=referencia,
            color="Métrica",
            orientation="h",
            barmode="group",
            color_discrete_sequence=["#f5f5f5", "#b7b9c8", "#8c91a8", "#7a84b9", "#c3add9"],
            template="plotly_dark"
        )
        fig.update_traces(
            marker=dict(line=dict(width=1, color="#c6cad8")),
            opacity=0.85
        )
        fig.update_layout(
            title={
                "text": build_chart_title(tab, categorias, metricas, referencia),
                "font": {
                    "color": "#f5f5f5",
                    "family": "'Clash Display Semibold', 'Helvetica Neue'",
                    "size": 22
                }
            },
            paper_bgcolor="#0b0c0e",
            plot_bgcolor="#0b0c0e",
            font={"color": "#f5f5f5"},
            legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#b7b9c8", borderwidth=1)
        )
        if LOGO_BASE64:
            fig.add_layout_image(
                dict(
                    source="data:image/png;base64," + LOGO_BASE64,
                    xref="paper",
                    yref="paper",
                    x=0.99,
                    y=0.01,
                    xanchor="right",
                    yanchor="bottom",
                    sizex=0.12,
                    sizey=0.10,
                    opacity=0.7,
                    layer="above"
                )
            )
        fig.update_layout(
            annotations=[
                dict(
                    text=metadata.replace("\n", " | "),
                    x=0,
                    y=-0.12,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(color="#f5f5f5", size=10),
                    xanchor="left",
                    align="left"
                )
            ],
            margin=dict(b=100)
        )
        fig.update_xaxes(
            showgrid=True,
            gridcolor="rgba(183,186,204,0.2)",
            zerolinecolor="rgba(255,255,255,0.06)",
            linecolor="#8c91a8",
            tickfont_color="#f5f5f5",
            title_font_color="#c3c6d5"
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(183,186,204,0.2)",
            zerolinecolor="rgba(255,255,255,0.06)",
            linecolor="#8c91a8",
            tickfont_color="#f5f5f5",
            title_font_color="#c3c6d5"
        )
    elif tab == "cronologico":
        cronologico = pd.melt(
            dff,
            id_vars=["Date", "Category"],
            value_vars=metricas,
            var_name="Métrica",
            value_name="Valor"
        )
        fig = px.scatter(
            cronologico,
            x="Date",
            y="Valor",
            color="Category",
            symbol="Métrica",
            color_discrete_sequence=["#f5f5f5", "#b7b9c8", "#8c91a8", "#7a84b9", "#c3add9"],
            template="plotly_dark"
        )
        fig.update_traces(
            marker=dict(size=8, line=dict(width=1, color="#c6cad8")),
            selector=dict(mode="markers")
        )
        fig.update_layout(
            title={
                "text": build_chart_title(tab, categorias, metricas, referencia),
                "font": {
                    "color": "#f5f5f5",
                    "family": "'Clash Display Semibold', 'Helvetica Neue'",
                    "size": 22
                }
            },
            paper_bgcolor="#0b0c0e",
            plot_bgcolor="#0b0c0e",
            font={"color": "#f5f5f5"},
            legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#b7b9c8", borderwidth=1)
        )
        if LOGO_BASE64:
            fig.add_layout_image(
                dict(
                    source="data:image/png;base64," + LOGO_BASE64,
                    xref="paper",
                    yref="paper",
                    x=0.99,
                    y=0.01,
                    xanchor="right",
                    yanchor="bottom",
                    sizex=0.12,
                    sizey=0.10,
                    opacity=0.7,
                    layer="above"
                )
            )
        fig.update_layout(
            annotations=[
                dict(
                    text=metadata.replace("\n", " | "),
                    x=0,
                    y=-0.12,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(color="#f5f5f5", size=10),
                    xanchor="left",
                    align="left"
                )
            ],
            margin=dict(b=100)
        )
        fig.update_xaxes(
            tickformat="%d/%m/%Y",
            showgrid=True,
            gridcolor="rgba(183,186,204,0.2)",
            zerolinecolor="rgba(255,255,255,0.06)",
            linecolor="#8c91a8",
            tickfont_color="#f5f5f5",
            title_font_color="#c3c6d5"
        )
        fig.update_yaxes(
            showgrid=True,
            gridcolor="rgba(183,186,204,0.2)",
            zerolinecolor="rgba(255,255,255,0.06)",
            linecolor="#8c91a8",
            tickfont_color="#f5f5f5",
            title_font_color="#c3c6d5"
        )
    else:
        return no_update

    fmt = "png" if trigger_id == "download-graph-png" else "pdf"
    tab_name = tab_titles.get(tab, tab)
    filename = f"grafico_{tab_name}.{fmt}"
    image_bytes = fig.to_image(format=fmt, width=1200, height=800, scale=2)
    return dcc.send_bytes(lambda buffer: buffer.write(image_bytes), filename)


@app.callback(
    Output("download-table","data"),
    Input("download-table-csv","n_clicks"),
    Input("download-table-xlsx","n_clicks"),
    Input("tabs","value"),
    Input("categoria","value"),
    Input("metrica","value"),
    Input("referencia","value"),
    Input("jugador","value"),
    Input("athlete","value"),
    Input("gametag","value"),
    Input("periodtag","value"),
    Input("fecha-actividad","date")
)
def descargar_tabla(
    n_csv,
    n_xlsx,
    tab,
    categorias,
    metricas,
    referencia,
    jugadores,
    athlete,
    gametags,
    periodtags,
    fecha_actividad
):
    triggered = dash.callback_context.triggered
    if not triggered:
        return no_update

    trigger_id = triggered[0]["prop_id"].split(".")[0]
    if trigger_id not in ["download-table-csv", "download-table-xlsx"]:
        return no_update

    dff = df.copy()
    if categorias:
        dff = dff[dff["Category"].isin(categorias)]
    if jugadores:
        dff = dff[dff["Player Name"].isin(jugadores)]
    if athlete:
        dff = dff[dff["Athlete Tags"].isin(athlete)]
    if gametags:
        dff = dff[dff["Game Tags"].isin(gametags)]
    if periodtags:
        dff = dff[dff["Period Tags"].isin(periodtags)]

    metricas = metricas or ["Distance"]
    referencia = referencia or "Category"
    item_name, metadata, printed_at = build_download_metadata(tab, categorias, metricas, referencia)

    if tab == "comparativas":
        df_export = dff.groupby(referencia)[metricas].mean().reset_index()
    elif tab == "actividad":
        fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
        columnas_requeridas = [
            "Player Name",
            "Accel + Decel Efforts",
            "Accel + Decel Efforts Per Minute",
            "Distance",
            "Player Load",
            "Max Velocity",
            "Meterage Per Minute",
            "Player Load Per Minute",
            "Sprint Distance",
            "Sprint Efforts",
            "Sprint Dist Per Min",
            "High Speed Distance",
            "High Speed Efforts",
            "High Speed Distance Per Minute",
            "Impacts"
        ]
        columnas_presentes = [c for c in columnas_requeridas if c in dff_fecha.columns]
        df_export = dff_fecha[columnas_presentes]
    elif tab == "actividad_comparativa":
        fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
        metricas_base = [m for m in metricas if m in dff.columns]
        resumen_fecha = (
            dff_fecha.groupby("Player Name")[metricas_base].mean().reset_index()
        )
        promedio_jugador = (
            dff.groupby("Player Name")[metricas_base].mean().reset_index()
        )
        df_export = resumen_fecha.merge(
            promedio_jugador,
            on="Player Name",
            how="outer",
            suffixes=("", "_Promedio")
        ).fillna(0)
    elif tab == "acwr":
        metricas_acwr = list(dict.fromkeys([
            "Distance",
            "Player Load",
            "Acceleration Efforts",
            "Sprint Distance",
            "High Speed Distance",
            "Sprint Efforts",
            "High Speed Efforts",
            "Impacts"
        ]))
        dff["Player Name"] = dff["Player Name"].astype(str).str.strip()
        ultimos21 = dff["Date"].max() - pd.Timedelta(days=21)
        ultimos7 = dff["Date"].max() - pd.Timedelta(days=7)
        df21 = dff[dff["Date"] >= ultimos21]
        df7 = dff[dff["Date"] >= ultimos7]
        cronica = df21.groupby("Player Name")[metricas_acwr].mean().reset_index()
        aguda = df7.groupby("Player Name")[metricas_acwr].mean().reset_index()
        tabla = cronica.merge(aguda, on="Player Name", how="outer", suffixes=("_21", "_7"))
        tabla = tabla.loc[:, ~tabla.columns.duplicated()]
        for m in metricas_acwr:
            tabla[m + "_ACWR"] = (tabla[f"{m}_7"] / tabla[f"{m}_21"]).round(2)
        df_export = tabla[["Player Name"] + [f"{m}_ACWR" for m in metricas_acwr]].fillna(0)
    else:
        df_export = pd.melt(
            dff,
            id_vars=["Date", "Category"],
            value_vars=metricas,
            var_name="Métrica",
            value_name="Valor"
        )

    tab_name = tab_titles.get(tab, tab)
    if trigger_id == "download-table-csv":
        buffer = io.BytesIO()
        buffer.write(metadata.encode("utf-8"))
        buffer.write(b"\n")
        df_export.to_csv(buffer, index=False, line_terminator="\n")
        buffer.seek(0)
        return dcc.send_bytes(lambda b: b.write(buffer.read()), f"tabla_{tab_name}.csv")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        worksheet_name = "Datos"
        df_export.to_excel(writer, sheet_name=worksheet_name, index=False, startrow=7)
        workbook = writer.book
        worksheet = writer.sheets[worksheet_name]
        worksheet.cell(row=1, column=1, value="Danubio Formativas 2026")
        worksheet.cell(row=2, column=1, value=f"Tabla: {item_name}")
        worksheet.cell(row=3, column=1, value=f"Impresión: {printed_at}")
        worksheet.cell(row=4, column=1, value=f"Categorías: {summarize_items(categorias, max_items=10)}")
        worksheet.cell(row=5, column=1, value=f"Métricas: {summarize_items(metricas, max_items=10)}")
        worksheet.cell(row=6, column=1, value=f"Comparar por: {referencia}")
        try:
            image = ExcelImage(str(LOGO_PATH))
            image.width = 120
            image.height = 40
            worksheet.add_image(image, "G1")
        except Exception:
            pass
    buffer.seek(0)
    return dcc.send_bytes(lambda b: b.write(buffer.read()), f"tabla_{tab_name}.xlsx")

if __name__ == "__main__":
    app.run(debug=True)

