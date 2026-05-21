import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Leer datos
df = pd.read_excel("GPS_Formativas_2026.xlsx")

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

        # IZQUIERDA → GRÁFICO
        html.Div([

            dcc.Graph(
                id="grafico1",
                style={
                    "height":"700px"
                }
            )

        ],
        style={
            "width":"72%",
            "display":"inline-block",
            "verticalAlign":"top"
        }),

        # DERECHA → PANEL FILTROS
        html.Div([

            # CATEGORÍAS
            html.Div([

                html.H4(
                    "Categorías",
                    style={
                        "color":"white",
                        "fontSize":"14px",
                        "fontWeight":"normal",
                        "marginBottom":"10px"
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
                        "fontSize":"12px",
                        "marginBottom":"5px"
                    }
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"15px",
                "borderRadius":"15px",
                "marginBottom":"15px"
            }),

            # MÉTRICAS
            html.Div([

                html.H4(
                    "Métricas",
                    style={
                        "color":"white",
                        "fontSize":"14px",
                        "fontWeight":"normal",
                        "marginBottom":"10px"
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
                        "fontSize":"12px",
                        "marginBottom":"5px"
                    }
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"15px",
                "borderRadius":"15px",
                "marginBottom":"15px"
            }),

            # COMPARAR POR
            html.Div([

                html.H4(
                    "Comparar por",
                    style={
                        "color":"white",
                        "fontSize":"14px",
                        "fontWeight":"normal",
                        "marginBottom":"10px"
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
                        "fontSize":"12px",
                        "marginBottom":"5px"
                    }
                )

            ],
            style={
                "background":"#2C2C2CE0",
                "padding":"15px",
                "borderRadius":"15px",
                "marginBottom":"15px"
            }),

            # FILTROS COMPARATIVOS
            html.Div([

                html.H4(
                    "Filtros comparativos",
                    style={
                        "color":"white",
                        "fontSize":"14px",
                        "fontWeight":"normal",
                        "marginBottom":"15px"
                    }
                ),

                html.P(
                    "Jugador",
                    style={"color":"#dcdcdc","fontSize":"12px"}
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
                    style={"color":"#dcdcdc","fontSize":"12px"}
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
                    style={"color":"#dcdcdc","fontSize":"12px"}
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
                    style={"color":"#dcdcdc","fontSize":"12px"}
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
                "padding":"15px",
                "borderRadius":"15px"
            })

        ],
        style={
            "width":"25%",
            "display":"inline-block",
            "paddingLeft":"15px",
            "verticalAlign":"top"
        })

    ])

],
style={
    "backgroundColor":"#1a1a1a",
    "padding":"20px",
    "fontFamily":'"ITC Avant Garde Gothic", Century Gothic, sans-serif'
})
@app.callback(
    Output("grafico1","figure"),
    Input("categoria","value"),
    Input("metrica","value"),
    Input("referencia","value"),
    Input("jugador","value"),
Input("athlete","value"),
Input("gametag","value"),
Input("periodtag","value")
)

def actualizar(
    categorias,
    metricas_seleccionadas,
    referencia, 
    jugador,
    athlete,
    gametag,
    periodtag
):

    dff = df.copy()

    if categorias:
        dff = dff[
            dff["Category"].isin(categorias)
        ]

    # Agrupación dinámica
    columnas_agrupacion = [referencia]

    if categorias and referencia != "Category":
        columnas_agrupacion.append("Category")

    promedio = (
        dff.groupby(columnas_agrupacion)[metricas_seleccionadas]
        .mean()
        .reset_index()
    )

    promedio = pd.melt(
        promedio,
        id_vars=columnas_agrupacion,
        value_vars=metricas_seleccionadas,
        var_name="Métrica",
        value_name="Valor"
    )

    fig = px.bar(

        promedio,

        x="Valor",
        y=referencia,

        color=(
            "Category"
            if referencia != "Category"
            and categorias
            else "Métrica"
        ),

        orientation="h",

        barmode="group",

        color_discrete_sequence=[
            "#f7f6f4",
            "#C5C3C3",
            "#999999",
            "#6e6e6e",
            "#b1b369"
        ]
    )

    cantidad_metricas = max(
        len(metricas_seleccionadas),
        1
    )

    altura_categoria = cantidad_metricas * 45

    altura_grafico = max(
        650,
        len(promedio[referencia].unique())
        * altura_categoria
    )

    fig.update_traces(
        opacity=0.75
    )

    fig.update_layout(

        paper_bgcolor="#1a1a1a",
        plot_bgcolor="#1a1a1a",

        font={
            "color":"#dcdcdc",
            "family":'"ITC Avant Garde Gothic", Century Gothic, sans-serif',
            "size":11
        },

        xaxis={
            "showgrid":True,
            "gridcolor":"#4e4e4e"
        },

        yaxis={
            "showgrid":False,
            "automargin":True
        },

        legend={
            "orientation":"h",
            "y":1.05
        },

        bargap=0.35,
        bargroupgap=0.15,

        height=altura_grafico
    )

    return fig


if __name__ == "__main__":
    app.run(debug=True)