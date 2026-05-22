import pandas as pd
import plotly.express as px
import dash_auth
from dash import Dash, dcc, html, Input, Output

# Leer datos
df = pd.read_excel("GPS_Formativas_2026.xlsx")
df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

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
server = app.server
VALID_USERNAME_PASSWORD_PAIRS = {
    "Danubioformativas": "danubio2026"
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
app.title = "CARGA EXTERNA - DANUBIO FORMATIVAS 2026"

metricas = [
    "Distance",
    "Player Load",
    "Max Velocity",
    "Deceleration Efforts",
    "Acceleration Efforts",
    "Accel + Decel Efforts",
    "Accel + Decel Efforts Per Minute",
    "Sprint Distance",
    "High Speed Distance",
    "Sprint Efforts",
    "High Speed Efforts",
    "Impacts",
    "Sprint Dist Per Min",
    "High Speed Distance Per Minute"
]

referencias = [
    "Category",
    "Player Name",
    "Athlete Tags",
    "Game Tags",
    "Period Tags"
]

from datetime import datetime

ultima_actualizacion = datetime.now().strftime(
    "%d/%m/%Y - %H:%M"
)

app.layout = html.Div([

    # HEADER
    html.Div([

        html.Img(
            src="/assets/Banner_titulo.png",
            style={
                "width":"100%",
                "borderRadius":"0px",
                "marginBottom":"20px",
                "maxHeight":"150px",
                "objectFit":"contain"
            }
        ),

        html.H1(
            "CARGA EXTERNA - DANUBIO FORMATIVAS 2026",
            style={
                "color":"#ffffff",
                "textAlign":"center",
                "fontSize":"30px",
                "fontWeight":"600",
                "marginTop":"5px",
                "marginBottom":"15px",
                "fontFamily":'"ITC Avant Garde Gothic", Century Gothic, sans-serif',
                "borderBottom":"2px solid #9e8330",
                "paddingBottom":"10px"
            }
        ),

        html.P(
            f"Última actualización: {ultima_actualizacion}",
            style={
                "color":"#dcdcdc",
                "textAlign":"right",
                "padding":"10px",
                "fontSize":"13px"
            }
        )

    ]),

    # CONTENEDOR PRINCIPAL
    html.Div([

     # IZQUIERDA → ÁREA GRÁFICOS
html.Div([

    dcc.Tabs(

        id="tabs",
        value="comparativas",

        children=[

            dcc.Tab(
                label="Comparativas",
                value="comparativas",

                style={
                    "backgroundColor":"#4e4e4e",
                    "color":"white",
                    "border":"0px"
                },

                selected_style={
                    "backgroundColor":"#9e8330",
                    "color":"white",
                    "border":"0px"
                }
            ),

            dcc.Tab(
                label="Cronológico",
                value="cronologico",

                style={
                    "backgroundColor":"#4e4e4e",
                    "color":"white",
                    "border":"0px"
                },

                selected_style={
                    "backgroundColor":"#9e8330",
                    "color":"white",
                    "border":"0px"
                }
            )
        ]
    ),

    html.Div(
        id="contenido-tab"
    )

],

style={

    "width":"72%",
    "display":"inline-block",
    "verticalAlign":"top",

    "position":"sticky",
    "top":"20px"
}),
        # DERECHA → PANEL FILTROS
        html.Div([

            # CATEGORÍAS
            html.Div([

                html.H4(
                    "Categorías",
                    style={
                        "color":"white",
                        "fontSize":"10px",
                        "fontWeight":"normal",
                        "marginBottom":"5px"
                    }
                ),

                dcc.Checklist(
                    id="categoria",

                    options=[
                        {
                            "label":c,
                            "value":c
                        }
                        for c in sorted(
                            df["Category"]
                            .dropna()
                            .unique()
                        )
                    ],

                    inline=False,

                    labelStyle={
                        "display":"block",
                        "color":"white",
                        "fontSize":"10px",
                        "marginBottom":"5px"
                    }
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"12px",
                "borderRadius":"12px",
                "marginBottom":"5px"
            }),

            # MÉTRICAS
            html.Div([

                html.H4(
                    "Métricas",
                    style={
                        "color":"white",
                        "fontSize":"10px",
                        "fontWeight":"normal",
                        "marginBottom":"5px"
                    }
                ),

                dcc.Checklist(
                    id="metrica",

                    options=[
                        {
                            "label":m,
                            "value":m
                        }
                        for m in metricas
                    ],

                    value=["Distance"],

                    inline=False,

                    labelStyle={
                        "display":"block",
                        "color":"white",
                        "fontSize":"10px",
                        "marginBottom":"5px"
                    }
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"12px",
                "borderRadius":"12px",
                "marginBottom":"5px"
            }),

            # COMPARAR POR
            html.Div([

                html.H4(
                    "Comparar por",
                    style={
                        "color":"white",
                        "fontSize":"10px",
                        "fontWeight":"normal",
                        "marginBottom":"5px"
                    }
                ),

                dcc.RadioItems(
                    id="referencia",

                    options=[
                        {
                            "label":r,
                            "value":r
                        }
                        for r in referencias
                    ],

                    value="Category",

                    labelStyle={
                        "display":"block",
                        "color":"white",
                        "fontSize":"10px",
                        "marginBottom":"5px"
                    }
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"12px",
                "borderRadius":"12px",
                "marginBottom":"5px"
            }),

            # FILTROS COMPARATIVOS
            html.Div([

                html.H4(
                    "Filtros comparativos",
                    style={
                        "color":"white",
                        "fontSize":"10px",
                        "fontWeight":"normal",
                        "marginBottom":"12px"
                    }
                ),

                html.P(
                    "Jugador",
                    style={"color":"#dcdcdc","fontSize":"10px"}
                ),

                dcc.Dropdown(
                    id="jugador",
                    options=[
                        {"label":x,"value":x}
                        for x in sorted(
                            df["Player Name"].dropna().unique()
                        )
                    ],
                    multi=True
                ),

                html.Br(),

                html.P(
                    "Athlete Tags",
                    style={"color":"#dcdcdc","fontSize":"10px"}
                ),

                dcc.Dropdown(
                    id="athlete",
                    options=[
                        {"label":x,"value":x}
                        for x in sorted(
                            df["Athlete Tags"].dropna().unique()
                        )
                    ],
                    multi=True
                ),

                html.Br(),

                html.P(
                    "Game Tags",
                    style={"color":"#dcdcdc","fontSize":"10px"}
                ),

                dcc.Dropdown(
                    id="gametag",
                    options=[
                        {"label":x,"value":x}
                        for x in sorted(
                            df["Game Tags"].dropna().unique()
                        )
                    ],
                    multi=True
                ),

                html.Br(),

                html.P(
                    "Period Tags",
                    style={"color":"#dcdcdc","fontSize":"10px"}
                ),

                dcc.Dropdown(
                    id="periodtag",
                    options=[
                        {"label":x,"value":x}
                        for x in sorted(
                            df["Period Tags"].dropna().unique()
                        )
                    ],
                    multi=True
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"12px",
                "borderRadius":"12px"
            })

        ],
        style={
             "width":"25%",
    "display":"inline-block",
    "paddingLeft":"12px",
    "verticalAlign":"top",

    "height":"80vh",
    "overflowY":"auto",
    "paddingRight":"8px"
        })

    ])

],
style={
    "backgroundColor":"#1a1a1a",
    "padding":"20px",
    "fontFamily":'"ITC Avant Garde Gothic", Century Gothic, sans-serif'
})
@app.callback(
    Output("contenido-tab","children"),

    Input("tabs","value"),
    Input("categoria","value"),
    Input("metrica","value"),
    Input("referencia","value"),
    Input("jugador","value"),
    Input("athlete","value"),
    Input("gametag","value"),
    Input("periodtag","value")
)

def actualizar_tab(

    tab,
    categorias,
    metricas,
    referencia,
    jugadores,
    athlete,
    gametags,
    periodtags
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

                "#fafafa",
                "#b3b1af",
                "#F5D888",
                "#5A5A5A",
                "#1B1B1B"
            ]
        )

        return dcc.Graph(
            figure=fig
        )

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

        fig=px.line(

            cronologico,

            x="Date",
            y="Valor",

            color="Category",

            line_dash="Métrica",

            markers=True,

            line={"shape": "spline"},

            color_discrete_sequence=[

                "#fafafa",
                "#b3b1af",
                "#F5D888",
                "#5A5A5A",
                "#1B1B1B"
            ]
        )

        fig.update_layout(

            title="Evolución cronológica",

            paper_bgcolor="#1a1a1a",
            plot_bgcolor="#1a1a1a",

            font={
                "color":"#dcdcdc"
            }
        )

        fig.update_xaxes(tickformat="%d/%m/%Y")

        return dcc.Graph(
            figure=fig
        )
if __name__ == "__main__":
    app.run(debug=True)