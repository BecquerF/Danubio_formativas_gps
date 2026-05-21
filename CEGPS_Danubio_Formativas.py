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
    "Sprint Distance",
    "High Speed Distance",
    "Sprint Efforts",
    "High Speed Efforts",
    "Impacts",
    "Sprint Dist per Minute",
    "High Speed Dist per Minute"
]

referencias = [
    "Category",
    "Player Name",
    "Athlete Tags",
    "Game Tags",
    "Period Tags"
]

app.layout = html.Div([

    html.H1(
        "Danubio Formativas GPS",
        style={
            "color":"#ffffff",
            "textAlign":"center",
            "marginBottom":"20px"
        }
    ),

    html.Div([

        dcc.Checklist(
            id="categoria",
            options=[
                {"label": c, "value": c}
                for c in sorted(df["Category"].dropna().unique())
            ],
            inline=True
        ),

        html.Br(),

        dcc.Checklist(
            id="metrica",
            options=[
                {"label": m, "value": m}
                for m in metricas
            ],
            value=["Acceleration Efforts"],
            inline=True
        ),

        html.Br(),

        dcc.RadioItems(
            id="referencia",
            options=[
                {"label":r,"value":r}
                for r in referencias
            ],
            value="Category",
            inline=True
        )

    ],

    style={

        "backgroundColor":"#4e4e4e",
        "padding":"15px",
        "borderRadius":"15px",
        "marginBottom":"20px"
    }),

    dcc.Graph(
        id="grafico1",
        style={
            "height":"500px"
        }
    )

],

style={

    "backgroundColor":"#1a1a1a",
    "minHeight":"100vh",
    "padding":"20px",

    "fontFamily":
    '"ITC Avant Garde Gothic", Avantgarde, Century Gothic, sans-serif'
})

@app.callback(
    Output("grafico1", "figure"),

    Input("categoria", "value"),
    Input("jugador", "value"),
    Input("gametag", "value"),
    Input("athlete", "value"),
    Input("metrica", "value"),
    Input("referencia", "value")
)

def actualizar(
    categorias,
    jugadores,
    gametags,
    athlete,
    metrica,
    referencia
):

    dff = df.copy()

    if categorias:
        dff = dff[dff["Category"].isin(categorias)]

    if jugadores:
        dff = dff[dff["Player Name"].isin(jugadores)]

    if gametags:
        dff = dff[dff["Game Tags"].isin(gametags)]

    if athlete:
        dff = dff[dff["Athlete Tags"].isin(athlete)]

    promedio = (
        dff.groupby(referencia)[metrica]
        .mean()
        .reset_index()
    )

    promedio = promedio.sort_values(
        by=metrica,
        ascending=True
    )

    fig = px.bar(
    promedio,
    x=metrica,
    y=referencia,
    orientation="h",
    color=referencia,
    text_auto=".1f",

    color_discrete_sequence=[
        "#9e8330",
        "#d1b77e",
        "#999999",
        "#6e6e6e"
    ]
)

fig.update_traces(

    width=0.35,
    opacity=0.85,
    textposition="outside"
)

fig.update_layout(

    paper_bgcolor="#1a1a1a",
    plot_bgcolor="#1a1a1a",

    font={

        "family":"ITC Avant Garde Gothic",
        "color":"#dcdcdc",
        "size":13
    },

    title={

        "x":0.5,
        "font":{"color":"white"}
    },

    xaxis={

        "showgrid":True,
        "gridcolor":"#4e4e4e",
        "zeroline":False
    },

    yaxis={

        "showgrid":False
    },

    showlegend=False,
    height=500
)

    return fig


if __name__ == "__main__":
    app.run(debug=True)