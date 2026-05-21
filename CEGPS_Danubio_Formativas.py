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

metricas = [
    "Distance",
    "Player Load",
    "Max Velocity",
    "Desaceleration Efforts",
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

    html.Div([

        html.Img(
            src="/assets/Banner_titulo.png",
            style={
                "width":"100%",
                "borderRadius":"0px",
                "marginBottom":"20px",
                "maxheight":"150px",
                "objectFit":"contain"   
            }
        ),

        html.P(
            f"Última actualización: {ultima_actualizacion}",
            style={
                "color":"#dcdcdc",
                "textAlign":"right",
                "padding":"10px"
            }
        )

    ]),

    html.Div([

        # IZQUIERDA
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

        # DERECHA
        html.Div([

            # Categorías
            html.Div([

                html.H4(
                    "Categorías",
                    style={"color":"white"}
                ),

                dcc.Checklist(
                    id="categoria",
                    options=[
                        {"label":c,"value":c}
                        for c in sorted(
                            df["Category"]
                            .dropna()
                            .unique()
                        )
                    ],
                    inline=False
                )

            ],

            style={

                "background":"#2C2C2CE0",
                "padding":"15px",
                "borderRadius":"15px",
                "marginBottom":"15px"
            }),

            # Métricas
            html.Div([

                html.H4(
                    "Métricas",
                    style={"color":"white"}
                ),

                dcc.Checklist(
                    id="metrica",
                    options=[
                        {"label":m,"value":m}
                        for m in metricas
                    ],
                    value=["Distance"],
                    inline=False
                )

            ],

            style={

                "background":"#2C2C2CE0",
                "padding":"15px",
                "borderRadius":"15px",
                "marginBottom":"15px"
            }),

            # Referencia
            html.Div([

                html.H4(
                    "Comparar por",
                    style={"color":"white"}
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
                    value="Category"
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
    "fontFamily":
    '"ITC Avant Garde Gothic", Century Gothic, sans-serif'
})


@app.callback(
    Output("grafico1","figure"),

    Input("categoria","value"),
    Input("metrica","value"),
    Input("referencia","value")
)

def actualizar(
    categorias,
    metricas_seleccionadas,
    referencia
):

    dff=df.copy()

    if categorias:

        dff=dff[
            dff["Category"]
            .isin(categorias)
        ]

    promedio=(
        dff.groupby(
            referencia
        )[metricas_seleccionadas]
        .mean()
        .reset_index()
    )

    promedio=pd.melt(

        promedio,
        id_vars=[referencia],
        value_vars=metricas_seleccionadas,
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
            "#f7f6f4",
            "#C5C3C3",
            "#999999",
            "#6e6e6e",
            "#b1b369",
        ]
    )

    fig.update_traces(
        width=.25,
        opacity=.65
    )

    fig.update_layout(

        paper_bgcolor="#1a1a1a",
        plot_bgcolor="#1a1a1a",

        font={
            "color":"#dcdcdc",
            "family":'"ITC Avant Garde Gothic", Century Gothic, sans-serif',
            "size":11
        },

        height=650
    )

    return fig

if __name__ == "__main__":
    app.run(debug=True)