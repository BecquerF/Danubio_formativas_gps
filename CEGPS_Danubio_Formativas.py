import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


# Leer datos
df = pd.read_excel("GPS_Formativas_2026.xlsx")
# Lista de columnas que contienen el archivo excel para eliminar
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
    "Acceleration Efforts",
    "Sprint Distance",
    "High Speed Distance"
]

referencias = [
    "Category",
    "Player Name",
    "Athlete Tags",
    "Game Tags",
    "Period Tags"
]

app.layout = html.Div([

    html.H2("Danubio Formativas GPS"),

    dcc.Dropdown(
        id="categoria",
        options=[
            {"label": c, "value": c}
            for c in sorted(df["Category"].dropna().unique())
        ],
        multi=True,
        placeholder="Seleccionar categoría"
    ),

    dcc.Dropdown(
        id="metrica",
        options=[
            {"label": m, "value": m}
            for m in metricas
        ],
        value="Acceleration Efforts"
    ),

    dcc.Dropdown(
        id="referencia",
        options=[
            {"label": r, "value": r}
            for r in referencias
        ],
        value="Category"
    ),
    
    dcc.Dropdown(
    id="jugador",
    options=[
        {"label": j, "value": j}
        for j in sorted(df["Player Name"].dropna().unique())
    ],
    multi=True,
    placeholder="Seleccionar jugador"
),

dcc.Dropdown(
    id="gametag",
    options=[
        {"label": g, "value": g}
        for g in sorted(df["Game Tags"].dropna().unique())
    ],
    multi=True,
    placeholder="Seleccionar dinámica"
),

dcc.Dropdown(
    id="athlete",
    options=[
        {"label": a, "value": a}
        for a in sorted(df["Athlete Tags"].dropna().unique())
    ],
    multi=True,
    placeholder="Seleccionar etiqueta"
),

    dcc.Graph(id="grafico1")
])


@app.callback(
     Output("grafico1","figure"),

    Input("categoria","value"),
    Input("jugador","value"),
    Input("gametag","value"),
    Input("athlete","value"),
    Input("metrica","value"),
    Input("referencia","value")
)

def actualizar(
    categorias,
    jugadores,
    gametags,
    athlete,
    metrica,
    referencia
):

    dff=df.copy()

    if categorias:
        dff=dff[dff["Category"].isin(categorias)]

    if jugadores:
        dff=dff[dff["Player Name"].isin(jugadores)]

    if gametags:
        dff=dff[dff["Game Tags"].isin(gametags)]

    if athlete:
        dff=dff[dff["Athlete Tags"].isin(athlete)]

    promedio=(
        dff.groupby(referencia)[metrica]
        .mean()
        .reset_index()
    )

    fig=px.bar(
        promedio,
        x=referencia,
        y=metrica,
        title=f"Promedio de {metrica}"
    )

    return fig

if __name__=="__main__":
    app.run(debug=True)