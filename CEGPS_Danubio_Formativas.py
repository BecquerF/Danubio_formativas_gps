import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
import os

# Leer datos
df = pd.read_excel("GPS_Formativas_2026.xlsx")

# Crear gráfico
fig = px.bar(
    df,
    x="Game Tags",
    y="Acceleration Efforts",
    title="Aceleración por Dinámica"
)

# Crear aplicación
app = Dash(__name__)
server = app.server   # <- importante para Render

# Layout
app.layout = html.Div([
    html.H1("Danubio Formativas"),
    dcc.Graph(figure=fig)
])

# Ejecutar local
if __name__ == "__main__":
    app.run(debug=True)