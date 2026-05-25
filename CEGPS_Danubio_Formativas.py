import io
import pandas as pd
import plotly.express as px
import dash
import dash_auth
from dash import Dash, dcc, html, dash_table, Input, Output, no_update

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
    "Player Load Per Minute"
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

referencias = [
    "Category",
    "Player Name",
    "Athlete Tags",
    "Game Tags",
    "Period Tags"
]

tab_titles = {
    "actividad": "Actividad_por_Jugador",
    "acwr": "ACWR_Zona_Segura",
    "comparativas": "Comparativas",
    "cronologico": "Cronologico"   
}

from datetime import datetime, timedelta

ultima_actualizacion = (
    datetime.now() - timedelta(hours=3)
).strftime(
    "%d/%m/%Y - %H:%M"
)

app.layout = html.Div([

    # ===== TÍTULO =====

    html.Div(
        html.H1(
            "CARGA EXTERNA - DANUBIO FORMATIVAS 2026",
            style={
                "color":"#ffffff",
                "textAlign":"center",
                "fontSize":"38px",
                "fontWeight":"700",
                "fontFamily":"'Clash Display Semibold'",
                "lineHeight":"1.05",
                "letterSpacing":"0.02em",
                "borderBottom":"2px solid #48f788",
                "paddingBottom":"12px",
                "margin":"0"
            }
        ),
        style={
            "width":"100%",
            "paddingTop":"15px",
            "paddingBottom":"8px"
        }
    ),

    # ===== CONTENIDO GENERAL =====

    html.Div([

        # ==================================================
        # SIDEBAR IZQUIERDO
        # ==================================================

        html.Div([

            # LOGO

            html.Div([

                html.Img(
                    src="/assets/logo_dataload_2.png",
                    style={
                        "width":"100%",
                        "height":"auto",
                        "display":"block",
                        "objectFit":"contain",
                        "position":"relative"
                    }
                )

            ],

            style={
                "background":"rgba(13,24,34,0.95)",
                "padding":"1px",
                "borderRadius":"12px",
                "border":"1px solid rgba(137,188,239,0.20)",
                "boxShadow":"0 18px 40px rgba(0,0,0,0.45)",
                "marginBottom":"20px",
                "overflow":"hidden"
            }),

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
    value="comparativas",
    vertical=True,
    style={
        "width":"100%",
        "background":"transparent",
        "border":"none"
    },

    children=[

        dcc.Tab(
            label="COMPARATIVAS",
            value="comparativas",

            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "fontWeight":"600",

                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"12px 12px",
                "marginBottom":"12px"
            },

            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "fontWeight":"700",

                "borderTop":"1px solid #a3e3d0",
                "padding":"12px 12px",

                "backgroundColor":"#011c24",
                "marginBottom":"12px"
            }
        ),

        dcc.Tab(
            label="CRONOLÓGICO",
            value="cronologico",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"12px 12px",
                "marginBottom":"12px"
            },
             selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "fontWeight":"700",

                "borderTop":"1px solid #a3e3d0",
                "padding":"12px 12px",

                "backgroundColor":"#011c24",
                "marginBottom":"12px"
            }
        ),

        dcc.Tab(
            label="ACTIVIDAD",
            value="actividad",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"12px 12px",
                "marginBottom":"12px"
            },
            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "fontWeight":"700",

                "borderTop":"1px solid #a3e3d0",
                "padding":"12px 12px",

                "backgroundColor":"#011c24",
                "marginBottom":"12px"
            }
        ),

        dcc.Tab(
            label="ACWR",
            value="acwr",
            style={
                "color":"#edf1f2",
                "fontSize":"12px",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"12px 12px",
                "marginBottom":"12px"
            },
            selected_style={
                "color":"#a3e3d0",
                "fontSize":"12px",
                "fontWeight":"700",

                "borderTop":"1px solid #a3e3d0",
                "padding":"12px 12px",

                "backgroundColor":"#011c24",
                "marginBottom":"12px"
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
                "padding":"10px 12px",
                "background":"linear-gradient(180deg,#000c0f,#011c24)",
                "borderRadius":"12px",
                "border":"1px solid rgba(137,188,239,.18)"
            })

        ],

        style={
            "display":"flex",
            "flexDirection":"column",
            "width":"140px",
            "minWidth":"140px",
            "gap":"6px",
            "position":"relative",
            "top":"20px",
            "alignSelf":"flex-start"
        }),

        # ==================================================
        # CONTENIDO CENTRAL
        # ==================================================

        html.Div([

            dcc.Download(id="download-graph"),
            dcc.Download(id="download-table"),

            # GRÁFICO

            html.Div(
    id="contenido-tab",
    style={
        "flex":"0",
        "width":"100%",
        "maxWidth":"1000px",
        "minWidth":"1000px",
        "height":"600px",

        "overflowX":"hidden",
        "overflowY":"hidden",

        "position":"relative",
        "border":"2px solid rgba(137,188,239,.18)",
        "boxShadow":"0 18px 40px rgba(0,0,0,0.25)",
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
                                    "marginBottom":"8px"
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
                                    "gap": "10px"
                                },
                                labelStyle={
                                    "color":"white",
                                    "fontSize":"10px",
                                    "marginBottom":"8px"
                                }
                            ),
                            html.Div(
                                [
                                    html.P(
                                        "Fecha de actividad",
                                        style={"color":"#f5f5f5","fontSize":"10px","marginBottom":"8px"}
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
                                            "padding": "8px"
                                        }
                                    )
                                ],
                                id="actividad-fecha-container",
                                style={"display": "none", "marginTop": "16px"}
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
                                    "marginBottom":"8px"
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
                                {"label":x,"value":x}
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
                                {"label":x,"value":x}
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
                                {"label":x,"value":x}
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
                                {"label":x,"value":x}
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

            style={
                "display":"grid",
                "gridTemplateColumns":"1fr",
                "gap":"12px"
            }

        )

    ],

    className="filter-card",
    style={
        "padding":"16px"
    }

)],
                className="sidebar-panel sidebar-right-panel",
                style={
    "width":"200px",
    "minWidth":"200px",

    "padding":"30px",
    "backgroundColor":"#011c24",

    "borderRadius":"24px",
    "border":"1px solid rgba(137, 188, 239, 0.16)",
    "boxShadow":"0 18px 48px rgba(0,0,0,0.35)",

    "position":"sticky",
    "top":"28px",

    "height":"calc(100vh - 56px)",
    "overflowY":"auto"
}
            )
        ],
        style={
            "display": "flex",
            "alignItems": "flex-start",
            "gap": "18px",
            "width": "100%",
            "minHeight": "calc(100vh - 180px)"
        }
    )
],
style={
    "color":"#ffffff",
    "padding": "28px 24px 36px",
    "fontFamily": "'Clash Display Semibold', 'Segoe UI', sans-serif",
    "margin": "0",
    "minHeight": "calc(100vh - 220px)"
}
)
@app.callback(
    Output("actividad-fecha-container","style"),
    Input("tabs","value")
)
def toggle_actividad_fecha(tab):
    if tab == "actividad":
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
                "text":"Comparativas",
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

        return dcc.Graph("Comparativas por" + referencia,
            figure=fig,
            style={"width":"100%","height":"100%"}
        ),
        style={"border":"1px solid rgba(137,188,239,0.18)",
        "borderRadius":"18px",
        "overflow":"hidden",
        "background":"#0b0c0e",
         "boxShadow":(
        "0 0 20px rgba(72,247,136,0.10), "
        "0 0 50px rgba(137,188,239,0.08), "
        "0 18px 40px rgba(0,0,0,0.35)"),
        "padding":"10px"
    }


    # ACTIVIDAD POR JUGADOR
    elif tab=="actividad":

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

        columnas_presentes = [
            c for c in columnas_requeridas
            if c in dff_fecha.columns
        ]

        columnas_actividad = [
            {"name": c, "id": c}
            for c in columnas_presentes
        ]

        # Calcular min/max para colores semáforo
        estilos_condicionales = []
        
        for col in columnas_presentes:
            if col != "Player Name" and dff_fecha[col].dtype in ['float64', 'int64']:
                max_val = dff_fecha[col].max()
                min_val = dff_fecha[col].min()
                rango = max_val - min_val if max_val != min_val else 1
                
                # Verde para máximos
                estilos_condicionales.append({
                    "if": {
                        "filter_query": f"{{{col}}} >= {max_val * 0.8}",
                        "column_id": col
                    },
                    "backgroundColor": "#017351",
                    "color": "white"
                })
                
                # Amarillo para intermedios-altos
                estilos_condicionales.append({
                    "if": {
                        "filter_query": f"{{{col}}} >= {min_val + rango * 0.5} && {{{col}}} < {max_val * 0.8}",
                        "column_id": col
                    },
                    "backgroundColor": "#F4C95D",
                    "color": "black"
                })
                
                # Rojo para mínimos
                estilos_condicionales.append({
                    "if": {
                        "filter_query": f"{{{col}}} < {min_val + rango * 0.5}",
                        "column_id": col
                    },
                    "backgroundColor": "#A40A1C",
                    "color": "white"
                })

        return html.Div([
            html.H3(
                "Actividad por Jugador",
                style={
                    "color": "white",
                    "textAlign": "center",
                    "marginBottom": "20px",
                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                    "fontWeight":"600"
                }
            ),
            html.H4(
                f"{fecha_dt.strftime('%d/%m/%Y')}",
                style={
                    "color": "#a3e3d0",
                    "textAlign": "center",
                    "marginBottom": "15px",
                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                    "fontWeight":"600"
                }
            ),
            dcc.Loading(
                dash_table.DataTable(
                    data=dff_fecha[columnas_presentes].to_dict("records") if columnas_presentes else [],
                    columns=columnas_actividad,
                    filter_action="native",
                    sort_action="native",
                    fixed_columns={"headers": True, "data": 1},
                    page_size=20,
                    style_table={
                        "overflowX": "auto",
                        "minWidth": "100%",
                        "border":"1px solid rgba(137,188,239,0.18)", "boxShadow":"0 18px 40px rgba(0,0,0,0.25)"
                    },
                    style_header={
                        "backgroundColor": "#000000",
                        "color": "white",
                        "fontWeight": "bold",
                        "position": "sticky",
                        "top": 0
                    },
                    style_cell={
                        "backgroundColor": "#1a1a1a",
                        "color": "white",
                        "fontSize": "11px",
                        "textAlign": "center",
                        "minWidth": "100px",
                        "whiteSpace": "normal"
                    },
                    style_data_conditional=estilos_condicionales
                )
            )
        ])


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

        dff["Player Name"] = dff["Player Name"].astype(str).str.strip()

        ultimos21 = dff["Date"].max() - pd.Timedelta(days=21)
        ultimos7 = dff["Date"].max() - pd.Timedelta(days=7)

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

        tabla = tabla.loc[:, ~tabla.columns.duplicated()]

        for m in metricas_acwr:
            tabla[m + "_ACWR"] = (
                tabla[f"{m}_7"] / tabla[f"{m}_21"]
            ).round(2)

        ratio_columns = list(dict.fromkeys([f"{m}_ACWR" for m in metricas_acwr]))
        tabla = tabla[["Player Name"] + ratio_columns].fillna(0)

        return html.Div([
            html.H3(
                "ACWR - Últimos 7 días vs 21 días",
                style={
                    "color": "white",
                    "textAlign": "center",
                    "boxShadow":"0 18px 40px rgba(0,0,0,0.25)"
                }
            ),
            dcc.Loading(
                dash_table.DataTable(
                    data=tabla.to_dict("records"),
                    columns=[
                        {"name": "Player Name", "id": "Player Name"}
                    ] + [
                        {
                            "name": col,
                            "id": col,
                            "type": "numeric",
                            "format": {"specifier": ".2f"}
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
    else:

        cronologico=pd.melt(

            dff,

            id_vars=[
                "Date",
                "Category"
            ],

            value_vars=metricas,

            var_name="Métrica",

            value_name="Valor"
        )

        fig=px.scatter(
            cronologico,
            x="Date",
            y="Valor",
            color="Category",
            symbol="Métrica",
            color_discrete_sequence=["#edf1f2", "#3c4d52", "#a3e3d0", "#89bcef", "#48f788", "#72d2e4"],
            template="plotly_dark"
        )

        fig.update_traces(
            marker=dict(
                size=10,
                line=dict(width=1, color="#ffffff")
            ),
            selector=dict(mode="markers"),
            hoverlabel=dict(
                bgcolor="#011c24",
                font_size=12,
                font_color="#f5f5f5"
            )
        )

        fig.update_layout(
            title="Evolución cronológica",
            paper_bgcolor="#0b0c0e",
            plot_bgcolor="#0b0c0e",
            font={
                "color":"#f5f5f5"
            },
            legend=dict(
                bgcolor="rgba(11,12,14,0.75)",
                bordercolor="#89bcef",
                borderwidth=1
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

        return dcc.Graph(
            figure=fig,
            style={"width":"100%","height":"100%", "boxShadow":"0 18px 40px rgba(0,0,0,0.25)"}
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
            paper_bgcolor="#0b0c0e",
            plot_bgcolor="#0b0c0e",
            font={"color": "#f5f5f5"},
            legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#b7b9c8", borderwidth=1)
        )
        fig.update_layout(
            annotations=[
                dict(
                    text="Desarrollado por: Bécquer Fernández 🌐 https://www.linkedin.com/in/bécquer-fernandez-2108ab152/",
                    x=1,
                    y=-0.08,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(color="#f5f5f5", size=10),
                    xanchor="right",
                    align="right"
                )
            ],
            margin=dict(b=80)
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
            title="Evolución cronológica",
            paper_bgcolor="#0b0c0e",
            plot_bgcolor="#0b0c0e",
            font={"color": "#f5f5f5"},
            legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#b7b9c8", borderwidth=1)
        )
        fig.update_layout(
            annotations=[
                dict(
                    text="Desarrollado por: Bécquer Fernández 🌐 https://www.linkedin.com/in/bécquer-fernandez-2108ab152/",
                    x=1,
                    y=-0.08,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(color="#f5f5f5", size=10),
                    xanchor="right",
                    align="right"
                )
            ],
            margin=dict(b=80)
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
        metadata = (
            "Desarrollado por: Bécquer Fernández 🌐 https://www.linkedin.com/in/bécquer-fernandez-2108ab152/\n\n"
        )
        buffer = io.BytesIO()
        buffer.write(metadata.encode("utf-8"))
        df_export.to_csv(buffer, index=False, line_terminator="\n")
        buffer.seek(0)
        return dcc.send_bytes(lambda b: b.write(buffer.read()), f"tabla_{tab_name}.csv")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        worksheet_name = "Datos"
        df_export.to_excel(writer, sheet_name=worksheet_name, index=False, startrow=4)
        workbook = writer.book
        worksheet = writer.sheets[worksheet_name]
        worksheet.cell(row=1, column=1, value="Desarrollado por: Bécquer Fernández")
        worksheet.cell(row=2, column=1, value="🌐 https://www.linkedin.com/in/bécquer-fernandez-2108ab152/")
        worksheet.cell(row=3, column=1, value=f"Tabla: {tab_name}")
    buffer.seek(0)
    return dcc.send_bytes(lambda b: b.write(buffer.read()), f"tabla_{tab_name}.xlsx")

if __name__ == "__main__":
    app.run(debug=True)
