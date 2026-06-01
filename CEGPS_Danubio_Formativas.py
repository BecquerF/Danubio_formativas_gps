import logging
import os
import sys
import plotly.io as pio
import io
import base64
import textwrap
import html as html_module
import tempfile
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, no_update
import dash
try:
    import dash_auth
except ImportError:
    dash_auth = None
try:
    from weasyprint import HTML as WeasyHTML
except Exception as e:
    logging.warning("WeasyPrint no está disponible: %s", e)
    WeasyHTML = None
from dash import Dash, dcc, html, dash_table, Input, Output, State, no_update, ctx, ALL
from openpyxl.drawing.image import Image as ExcelImage
from fileinput import filename
from datetime import datetime
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / "assets" / "fonts"


def register_pdf_fonts():
    try:
        pdfmetrics.registerFont(TTFont("ClashDisplay-Semibold", str(FONT_DIR / "ClashDisplay-Semibold.otf")))
    except Exception:
        pass
    try:
        pdfmetrics.registerFont(TTFont("Manrope-Light", str(FONT_DIR / "Manrope-Light.ttf")))
    except Exception:
        pass


register_pdf_fonts()
logging.basicConfig(level=logging.INFO)

# Leer datos
df = pd.read_excel("GPS_Formativas_2026.xlsx")
df["Date"] = pd.to_datetime(
    df["Date"],
    errors="coerce"
)

if "Duration" in df.columns:
    if pd.api.types.is_numeric_dtype(df["Duration"]):
        df["Duration"] = pd.to_timedelta(df["Duration"], unit="D", errors="coerce").dt.total_seconds() / 60.0
    else:
        df["Duration"] = pd.to_timedelta(df["Duration"], errors="coerce").dt.total_seconds() / 60.0

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
# Configurar una clave secreta para las sesiones desde la variable de entorno SECRET_KEY
SECRET_KEY = os.environ["SECRET_KEY"]
server.secret_key = SECRET_KEY
VALID_USERNAME_PASSWORD_PAIRS = {
    "Danubioformativas": "formativas2026"
}

if dash_auth is not None:
    auth = dash_auth.BasicAuth(
        app,
        VALID_USERNAME_PASSWORD_PAIRS
    )
else:
    auth = None
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

metricas_radar = [
    "Meterage Per Minute",
    "Accel + Decel Efforts Per Minute",
    "High Speed Distance Per Minute",
    "Sprint Dist Per Min",
    "High Speed Efforts",
    "Sprint Efforts"
]

metricas_promedios = metricas_radar + ["Max Velocity", "Duration"]


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
    "actividad_promedios": "Actividad_Promedios",
    "acwr": "ACWR_Zona_Segura",
    "plyr_vs_plyr": "PLYR_vs_PLYR",
    "informe": "Informe"
}

informe_sections = [
    {"label": "Actividad", "value": "actividad"},
    {"label": "Actividad Comparativa Individual", "value": "actividad_comparativa"},
    {"label": "Actividad/Promedios", "value": "actividad_promedios"},
    {"label": "ACWR", "value": "acwr"},
    {"label": "PLYR vs PLYR", "value": "plyr_vs_plyr"},
    {"label": "Comparativo", "value": "comparativas"},
    {"label": "Cronológico", "value": "cronologico"}
]

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

    if tab == "actividad_promedios":
        title = "Actividad / Promedios"
        if categorias:
            title += f" - Categoría(s): {categoria_text}"
        return title

    if tab == "plyr_vs_plyr":
        title = "Comparativa Jugador vs Jugador"
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

    if tab == "plyr_vs_plyr":
        item_name = "Comparativa Jugador vs Jugador"

    metadata = (
        f"Descargado: {item_name}\n"
        f"Impresión: {printed_at}\n"
        f"Categorías: {category_text}\n"
        f"Métricas: {metric_text}\n"
        f"Comparar por: {referencia}\n"
    )
    return item_name, metadata, printed_at


def build_plyr_vs_plyr(dff, jugador_1, jugador_2, game_tag=None, period_tag=None, metricas=None):
    metricas = metricas_radar.copy()
    metricas = [m for m in metricas if m in dff.columns]

    dff_filtrado = dff.copy()
    if game_tag:
        dff_filtrado = dff_filtrado[dff_filtrado["Game Tags"] == game_tag]
    if period_tag:
        dff_filtrado = dff_filtrado[dff_filtrado["Period Tags"] == period_tag]

    if not jugador_1 or not jugador_2:
        return go.Figure()

    jugadores = [jugador_1, jugador_2]
    dff_jugadores = dff_filtrado[dff_filtrado["Player Name"].isin(jugadores)]
    if dff_jugadores.empty:
        return go.Figure()

    radar_data = (
        dff_jugadores.groupby("Player Name")[metricas]
        .mean()
        .reset_index()
    )

    radar_data_norm = radar_data.copy()
    for m in metricas:
        col_min = radar_data[m].min()
        col_max = radar_data[m].max()
        if col_max > col_min:
            radar_data_norm[m] = (radar_data[m] - col_min) / (col_max - col_min)

    fig = go.Figure()
    colores = ["#48f788", "#89bcef"]
    for idx, row in radar_data_norm.iterrows():
        rgb = tuple(int(colores[idx % len(colores)][1+i:3+i], 16) for i in (0, 2, 4))
        fig.add_trace(go.Scatterpolar(
            r=row[metricas].values.flatten().tolist(),
            theta=metricas,
            fill="toself",
            name=row["Player Name"],
            mode="markers+lines",
            marker=dict(size=6, color=colores[idx % len(colores)]),
            line=dict(color=colores[idx % len(colores)], width=2),
            fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.25)",
            text=[f"{val:.2f}" for val in row[metricas].values.flatten().tolist()],
            textposition="top center",
            textfont=dict(size=10, color="#edf1f2")
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showline=True,
                linewidth=1,
                gridcolor="rgba(200,200,200,0.25)",
                gridwidth=0.8,
                tickfont=dict(size=12, color="#edf1f2")
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#edf1f2")
            )
        ),
        showlegend=True,
        template="plotly_dark",
        title=dict(
            text=f"{jugador_1}  ||  {jugador_2}",
            font=dict(size=20, color="#a3e3d0", family="Manrope Light"),
            x=0.5
        ),
        legend=dict(
            font=dict(size=13, color="#edf1f2"),
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="rgba(137,188,239,0.25)",
            borderwidth=1
        )
    )

    return fig


def build_comparativas(dff, categorias, metricas, referencia):
    metricas = metricas or ["Distance"]
    metricas = [m for m in metricas if m in dff.columns]
    if referencia not in dff.columns or not metricas:
        return go.Figure()

    promedio = (
        dff.groupby(referencia)[metricas]
        .mean()
        .reset_index()
    )

    promedio_melt = pd.melt(
        promedio,
        id_vars=[referencia],
        value_vars=metricas,
        var_name="Métrica",
        value_name="Valor"
    )

    fig = px.bar(
        promedio_melt,
        x="Valor",
        y=referencia,
        color="Métrica",
        orientation="h",
        barmode="group",
        template="plotly_dark",
        color_discrete_sequence=["#edf1f2", "#f1a3fd", "#a3e3d0", "#89bcef", "#48f788", "#f96e83"]
    )

    fig.update_layout(
        title={
            "text": f"Comparativo de métricas por {referencia}",
            "font": {"color": "#f5f5f5", "family": "'Clash Display Semibold', 'Helvetica Neue'", "size": 22}
        },
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"},
        legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#89bcef", borderwidth=1)
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

    return fig


def build_cronologico(dff, categorias, metricas, referencia):
    metricas = metricas or ["Distance"]
    metricas = [m for m in metricas if m in dff.columns]
    if "Date" not in dff.columns or not metricas:
        return go.Figure()

    dff = dff.dropna(subset=["Date"]).copy()
    if dff.empty:
        return go.Figure()

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
            "text": f"Evolución cronológica de {' / '.join(metricas)}",
            "font": {"color": "#f5f5f5", "family": "'Clash Display Semibold', 'Helvetica Neue'", "size": 22}
        },
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"},
        legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#89bcef", borderwidth=1)
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

    return fig


def truncate_to_n_words(text, n=500):
    words = text.split()
    return " ".join(words[:n])


def build_auto_report_title(categorias, fecha_actividad):
    fecha_text = (
        pd.to_datetime(fecha_actividad).strftime("%d/%m/%Y")
        if fecha_actividad else datetime.now().strftime("%d/%m/%Y")
    )
    if categorias:
        categorias_text = ", ".join(categorias[:3])
        if len(categorias) > 3:
            categorias_text += ", ..."
    else:
        categorias_text = "Todas las categorías"
    return f"Informe {fecha_text} - {categorias_text}"


def section_title(section_value):
    titles = {
        "actividad": "Actividad",
        "actividad_comparativa": "Actividad Comparativa Individual",
        "actividad_promedios": "Actividad/Promedios",
        "acwr": "ACWR",
        "plyr_vs_plyr": "PLYR vs PLYR",
        "comparativas": "Comparativo",
        "cronologico": "Cronológico"
    }
    return titles.get(section_value, section_value)


def build_actividad_report_fig(dff, fecha_dt):
    if "Date" not in dff.columns:
        return go.Figure()
    dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
    metrics = [m for m in ["Distance", "Player Load", "Sprint Distance", "High Speed Distance", "Sprint Efforts"] if m in dff_fecha.columns]
    if dff_fecha.empty or not metrics:
        return go.Figure()

    resumen = dff_fecha.groupby("Player Name")[metrics].sum().reset_index()
    resumen = resumen.sort_values(metrics[0], ascending=False).head(6)
    data = pd.melt(resumen, id_vars=["Player Name"], value_vars=metrics, var_name="Métrica", value_name="Valor")

    fig = px.bar(
        data,
        x="Valor",
        y="Player Name",
        color="Métrica",
        orientation="h",
        barmode="group",
        template="plotly_dark",
        color_discrete_sequence=["#edf1f2", "#f1a3fd", "#a3e3d0", "#89bcef", "#48f788", "#f96e83"]
    )
    fig.update_layout(
        title={"text": f"Actividad {fecha_dt.strftime('%d/%m/%Y')}", "font": {"color": "#f5f5f5", "size": 18}},
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"},
        legend=dict(bgcolor="rgba(11,12,14,0.75)", bordercolor="#89bcef", borderwidth=1)
    )
    return fig


def build_actividad_comparativa_report_fig(dff, fecha_dt):
    if "Date" not in dff.columns:
        return go.Figure()
    metrics = [m for m in ["Distance", "Player Load", "Sprint Distance"] if m in dff.columns]
    dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
    if dff_fecha.empty or not metrics:
        return go.Figure()

    resumen = dff_fecha.groupby("Player Name")[metrics].sum().reset_index()
    dff_acum = dff[dff["Date"].dt.normalize() <= fecha_dt]
    promedio = dff_acum.groupby("Player Name")[metrics].mean().reset_index()
    promedio = promedio.rename(columns={m: f"{m} Prom" for m in metrics})
    tabla = resumen.merge(promedio, on="Player Name", how="left").fillna(0)

    rows = []
    for _, row in tabla.iterrows():
        for m in metrics:
            rows.append({"Player Name": row["Player Name"], "Métrica": m, "Tipo": "Actual", "Valor": row[m]})
            rows.append({"Player Name": row["Player Name"], "Métrica": m, "Tipo": "Promedio", "Valor": row[f"{m} Prom"]})
    if not rows:
        return go.Figure()

    data = pd.DataFrame(rows)
    fig = px.bar(
        data,
        x="Valor",
        y="Player Name",
        color="Tipo",
        facet_col="Métrica",
        orientation="h",
        barmode="group",
        template="plotly_dark",
        category_orders={"Tipo": ["Actual", "Promedio"]},
        color_discrete_sequence=["#48f788", "#89bcef"]
    )
    fig.update_layout(
        title={"text": f"Actividad Comparativa Individual {fecha_dt.strftime('%d/%m/%Y')}", "font": {"color": "#f5f5f5", "size": 18}},
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"}
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
    return fig


def build_actividad_promedios_report_fig(dff, fecha_dt):
    metrics = [m for m in metricas_promedios if m in dff.columns]
    dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
    if dff_fecha.empty or not metrics:
        return go.Figure()

    promedio = dff_fecha[metrics].mean().reset_index()
    promedio.columns = ["Métrica", "Valor"]
    fig = px.bar(
        promedio,
        x="Valor",
        y="Métrica",
        orientation="h",
        template="plotly_dark",
        color_discrete_sequence=["#edf1f2"]
    )
    fig.update_layout(
        title={"text": f"Actividad / Promedios {fecha_dt.strftime('%d/%m/%Y')}", "font": {"color": "#f5f5f5", "size": 18}},
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"}
    )
    return fig


def build_acwr_report_fig(dff):
    metrics = [m for m in ["Distance", "Player Load", "Sprint Distance", "High Speed Distance", "Sprint Efforts", "High Speed Efforts", "Impacts"] if m in dff.columns]
    if dff.empty or not metrics:
        return go.Figure()

    ultimos21 = dff["Date"].max() - pd.Timedelta(days=21)
    ultimos7 = dff["Date"].max() - pd.Timedelta(days=7)
    df21 = dff[dff["Date"] >= ultimos21]
    df7 = dff[dff["Date"] >= ultimos7]
    cronica = df21.groupby("Player Name")[metrics].mean().reset_index()
    aguda = df7.groupby("Player Name")[metrics].mean().reset_index()
    tabla = cronica.merge(aguda, on="Player Name", how="outer", suffixes=("_21", "_7")).fillna(0)
    rows = []
    for _, row in tabla.iterrows():
        for m in metrics:
            rows.append({"Player Name": row["Player Name"], "Métrica": m, "Valor": round(row[f"{m}_7"] / row[f"{m}_21"] if row[f"{m}_21"] else 0, 2)})
    data = pd.DataFrame(rows)
    fig = px.bar(
        data,
        x="Valor",
        y="Player Name",
        color="Métrica",
        orientation="h",
        template="plotly_dark",
        color_discrete_sequence=["#edf1f2", "#f1a3fd", "#a3e3d0", "#89bcef", "#48f788", "#f96e83", "#f4c95d"]
    )
    fig.update_layout(
        title={"text": "ACWR - Últimos 7 días vs 21 días", "font": {"color": "#f5f5f5", "size": 18}},
        paper_bgcolor="#0b0c0e",
        plot_bgcolor="#0b0c0e",
        font={"color": "#f5f5f5"}
    )
    return fig


def build_plyr_vs_plyr_report_fig(dff):
    nombres = dff.groupby("Player Name")["Distance"].sum().sort_values(ascending=False).head(2).index.tolist()
    if len(nombres) < 2:
        return go.Figure()
    return build_plyr_vs_plyr(dff, nombres[0], nombres[1], None, None)


def build_section_report_fig(section, dff, fecha_dt, categorias):
    
    if section == "actividad":
        return build_actividad_report_fig(dff, fecha_dt)
    if section == "actividad_comparativa":
        return build_actividad_comparativa_report_fig(dff, fecha_dt)
    if section == "actividad_promedios":
        return build_actividad_promedios_report_fig(dff, fecha_dt)
    if section == "acwr":
        return build_acwr_report_fig(dff)
    if section == "plyr_vs_plyr":
        return build_plyr_vs_plyr_report_fig(dff)
    if section == "comparativas":
        return build_comparativas(dff, categorias, ["Distance"], "Category")
    if section == "cronologico":
        return build_cronologico(dff, categorias, ["Distance"], "Category")
    return go.Figure()


def build_plotly_table(header, rows, title):
    if not rows:
        return None

    columns = [[row.get(col, "") for row in rows] for col in header]
    fig = go.Figure(data=[
        go.Table(
            header=dict(
                values=header,
                fill_color="#1f2c56",
                font=dict(color="white", size=11),
                align="center"
            ),
            cells=dict(
                values=columns,
                fill_color="#0b0c0e",
                font=dict(color="white", size=10),
                align="center"
            )
        )
    ])
    fig.update_layout(
        title={"text": title, "font": {"color": "#f5f5f5", "size": 16}, "x": 0.01},
        width=1200,
        height=max(340, 40 + 20 * len(rows)),
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="#0b0c0e"
    )
    return fig


def build_section_report_table_fig(section, dff, fecha_dt, categorias):
    if section == "actividad":
        if "Date" not in dff.columns:
            return None
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
        metrics = [m for m in ["Distance", "Player Load", "Sprint Distance", "High Speed Distance", "Sprint Efforts"] if m in dff_fecha.columns]
        if dff_fecha.empty or not metrics:
            return None
        resumen = dff_fecha.groupby("Player Name")[metrics].sum().reset_index()
        resumen = resumen.sort_values(metrics[0], ascending=False).head(10).round(2)
        header = ["Player Name"] + metrics
        rows = resumen.to_dict(orient="records")
        return build_plotly_table(header, rows, f"Tabla de Actividad {fecha_dt.strftime('%d/%m/%Y')}")

    if section == "actividad_comparativa":
        if "Date" not in dff.columns:
            return None
        metrics = [m for m in ["Distance", "Player Load", "Sprint Distance"] if m in dff.columns]
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
        if dff_fecha.empty or not metrics:
            return None
        resumen = dff_fecha.groupby("Player Name")[metrics].sum().reset_index()
        promedio = dff[dff["Date"].dt.normalize() <= fecha_dt].groupby("Player Name")[metrics].mean().reset_index()
        resumen = resumen.rename(columns={m: f"{m} Actual" for m in metrics})
        promedio = promedio.rename(columns={m: f"{m} Prom" for m in metrics})
        tabla = resumen.merge(promedio, on="Player Name", how="left").fillna(0).round(2)
        header = ["Player Name"] + [f"{m} Actual" for m in metrics] + [f"{m} Prom" for m in metrics]
        rows = tabla.sort_values(f"{metrics[0]} Actual", ascending=False).head(10).to_dict(orient="records")
        return build_plotly_table(header, rows, f"Tabla de Actividad Comparativa Individual {fecha_dt.strftime('%d/%m/%Y')}")

    if section == "actividad_promedios":
        if "Date" not in dff.columns:
            return None
        metrics = [m for m in metricas_promedios if m in dff.columns]
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]
        if dff_fecha.empty or not metrics:
            return None
        promedio = dff_fecha[metrics].mean().reset_index()
        promedio.columns = ["Métrica", "Valor"]
        promedio["Valor"] = promedio["Valor"].round(2)
        rows = promedio.to_dict(orient="records")
        return build_plotly_table(["Métrica", "Valor"], rows, f"Tabla de Actividad / Promedios {fecha_dt.strftime('%d/%m/%Y')}")

    if section == "acwr":
        metrics = [m for m in ["Distance", "Player Load", "Sprint Distance", "High Speed Distance", "Sprint Efforts", "High Speed Efforts", "Impacts"] if m in dff.columns]
        if dff.empty or not metrics:
            return None
        ultimos21 = dff["Date"].max() - pd.Timedelta(days=21)
        ultimos7 = dff["Date"].max() - pd.Timedelta(days=7)
        df21 = dff[dff["Date"] >= ultimos21]
        df7 = dff[dff["Date"] >= ultimos7]
        cronica = df21.groupby("Player Name")[metrics].mean().reset_index()
        aguda = df7.groupby("Player Name")[metrics].mean().reset_index()
        tabla = cronica.merge(aguda, on="Player Name", how="outer", suffixes=("_21", "_7")).fillna(0)
        rows = []
        for _, row in tabla.iterrows():
            item = {"Player Name": row["Player Name"]}
            for m in metrics:
                item[f"{m} ACWR"] = round((row[f"{m}_7"] / row[f"{m}_21"]) if row[f"{m}_21"] else 0, 2)
            rows.append(item)
        if not rows:
            return None
        header = ["Player Name"] + [f"{m} ACWR" for m in metrics]
        df_ratio = pd.DataFrame(rows).sort_values(f"{metrics[0]} ACWR", ascending=False).head(10)
        return build_plotly_table(header, df_ratio.to_dict(orient="records"), "Tabla ACWR (7 días vs 21 días)")

    return None


def _fig_write_image(fig, width, height, scale):
    buf = io.BytesIO()
    fig.write_image(buf, format="png", width=width, height=height, scale=scale)
    return buf.getvalue()


def fig_to_png_bytes(fig, width=1200, height=900, scale=2):
    if fig is None or not getattr(fig, "data", None):
        return None

    for method, call in [
        ("fig.to_image", lambda: fig.to_image(format="png", width=width, height=height, scale=scale)),
        ("pio.to_image", lambda: pio.to_image(fig, format="png", width=width, height=height, scale=scale)),
        ("fig.write_image", lambda: _fig_write_image(fig, width, height, scale)),
    ]:
        try:
            result = call()
            if result:
                logging.info(
                    "Generado PNG para figura %s usando %s, tamaño=%s bytes",
                    getattr(fig, 'name', '<unnamed>'),
                    method,
                    len(result),
                )
                return result
        except Exception as e:
            logging.warning("%s failed para figura %s: %s", method, getattr(fig, 'name', '<unnamed>'), e)

    logging.warning("No se pudo generar PNG para la figura; revise la instalación del renderer de Plotly.")
    return None


def combine_image_bytes_vertically(image_bytes_list, spacing=20, background=(255, 255, 255, 255)):
    if not image_bytes_list:
        return None

    images = []
    for image_bytes in image_bytes_list:
        try:
            img = PILImage.open(io.BytesIO(image_bytes)).convert("RGBA")
            images.append(img)
        except Exception as e:
            logging.warning("No se pudo abrir imagen para combinar en PNG: %s", e)
            return None

    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images) + spacing * (len(images) - 1)
    combined = PILImage.new("RGBA", (max_width, total_height), background)

    y = 0
    for img in images:
        x = (max_width - img.width) // 2
        combined.paste(img, (x, y), img)
        y += img.height + spacing

    buf = io.BytesIO()
    combined.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def draw_wrapped_text(c, text, x, y, width, leading, page_height, margin, header_func=None):
    font_name = "Manrope-Light" if "Manrope-Light" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    text_obj = c.beginText(x, y)
    text_obj.setFont(font_name, 10)
    for paragraph in text.split("\n"):
        lines = textwrap.wrap(paragraph, width=100)
        if not lines:
            lines = [""]
        for line in lines:
            if y < margin + 60:
                c.drawText(text_obj)
                c.showPage()
                if header_func:
                    y = header_func()
                else:
                    y = page_height - margin
                text_obj = c.beginText(x, y)
                text_obj.setFont(font_name, 10)
            text_obj.textLine(line)
            y -= leading
    c.drawText(text_obj)
    return y


def draw_page_header(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin):
    y = height - margin
    title_font = "ClashDisplay-Semibold" if "ClashDisplay-Semibold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    small_font = "Manrope-Light" if "Manrope-Light" in pdfmetrics.getRegisteredFontNames() else "Helvetica"

    c.setFont(title_font, 22)
    c.drawString(margin, y, title)
    if logo_bytes:
        try:
            logo = load_image_reader_from_bytes(logo_bytes)
            c.drawImage(logo, width - margin - 100, height - margin - 60, width=100, height=60, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            logging.warning("No se pudo dibujar el logo en PDF: %s", e)
    y -= 22
    c.setFont(small_font, 9)
    c.drawString(margin, y, fecha_text)
    if filters_text:
        y = draw_wrapped_text(c, filters_text, margin, y - 12, width - 2 * margin, 11, height, margin)
    y -= 14
    c.setStrokeColorRGB(0.6, 0.7, 0.8)
    c.setLineWidth(0.5)
    c.line(margin, y, width - margin, y)
    return y - 12


def draw_page_footer(c, author, width, margin):
    footer_font = "ClashDisplay-Semibold" if "ClashDisplay-Semibold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    c.setFont(footer_font, 9)
    footer_text = f"Creado por {author}"
    footer_y = margin / 2
    c.drawRightString(width - margin, footer_y, footer_text)


def draw_page_header_and_footer(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin):
    y = draw_page_header(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin)
    draw_page_footer(c, author, width, margin)
    return y


def load_image_reader_from_bytes(image_bytes):
    try:
        return ImageReader(io.BytesIO(image_bytes))
    except Exception:
        if PILImage is not None:
            try:
                pil_img = PILImage.open(io.BytesIO(image_bytes))
                return ImageReader(pil_img)
            except Exception:
                pass
        raise


def build_report_pdf(title, author, logo_bytes, sections, fecha_text, filters_text=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = inch * 0.5

    y = draw_page_header_and_footer(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin)

    for section in sections:
        if y < margin + 220:
            c.showPage()
            y = draw_page_header_and_footer(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin)

        section_font = "ClashDisplay-Semibold" if "ClashDisplay-Semibold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
        c.setFont(section_font, 16)
        c.drawString(margin, y, section["title"])
        y -= 20

        caption = section.get("caption") or f"Figura: {section['title']} con los filtros seleccionados."
        if section.get("img") is not None:
            try:
                image = load_image_reader_from_bytes(section["img"])
                img_width = width - 2 * margin
                available_height = y - margin - 60
                img_height = min(420, max(260, available_height))
                if y - img_height < margin:
                    c.showPage()
                    y = draw_page_header_and_footer(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin)
                c.drawImage(image, margin, y - img_height, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
                y -= img_height + 8
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(margin, y, caption)
                y -= 18
            except Exception as e:
                logging.warning("No se pudo dibujar imagen de sección %s en PDF: %s", section['title'], e)
                y -= 8

        if section.get("table_img") is not None:
            try:
                image = load_image_reader_from_bytes(section["table_img"])
                img_width = width - 2 * margin
                available_height = y - margin - 60
                img_height = min(360, max(260, available_height))
                if y - img_height < margin:
                    c.showPage()
                    y = draw_page_header_and_footer(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin)
                c.drawImage(image, margin, y - img_height, width=img_width, height=img_height, preserveAspectRatio=True, mask='auto')
                y -= img_height + 8
                c.setFont("Helvetica-Oblique", 9)
                c.drawString(margin, y, section.get("table_caption", ""))
                y -= 18
            except Exception as e:
                logging.warning("No se pudo dibujar tabla de sección %s en PDF: %s", section['title'], e)
                y -= 8

        content = truncate_to_n_words(section.get("text", ""), 500)
        y = draw_wrapped_text(
            c,
            content,
            margin,
            y,
            width - 2 * margin,
            13,
            height,
            margin,
            header_func=lambda: draw_page_header_and_footer(c, title, author, fecha_text, filters_text, logo_bytes, width, height, margin)
        )
        y -= 18

    c.save()
    buffer.seek(0)
    return buffer.read()


def build_report_html(title, author, logo_bytes, sections, fecha_text, filters_text=None):
    logo_html = ""
    if logo_bytes:
        logo_b64 = base64.b64encode(logo_bytes).decode("utf-8")
        logo_html = f'<img class="report-logo" src="data:image/png;base64,{logo_b64}" alt="Logo" />'

    section_blocks = []
    for section in sections:
        section_text = html_module.escape(section.get("text", "")).replace("\n", "<br />")
        block = [f'<section class="report-section">', f'<h2>{html_module.escape(section["title"])}</h2>']

        if section.get("img") is not None:
            img_b64 = base64.b64encode(section["img"]).decode("utf-8")
            block.append(
                f'<img class="report-image" src="data:image/png;base64,{img_b64}" alt="{html_module.escape(section["title"])}" />'
            )
            if section.get("caption"):
                block.append(f'<p class="caption">{html_module.escape(section.get("caption"))}</p>')

        if section.get("table_img") is not None:
            table_b64 = base64.b64encode(section["table_img"]).decode("utf-8")
            block.append(
                f'<img class="report-table-image" src="data:image/png;base64,{table_b64}" alt="{html_module.escape(section["title"])} table" />'
            )
            if section.get("table_caption"):
                block.append(f'<p class="caption">{html_module.escape(section.get("table_caption"))}</p>')

        if section_text:
            block.append(f'<div class="report-text">{section_text}</div>')
        block.append("</section>")
        section_blocks.append("\n".join(block))

    filters_html = html_module.escape(filters_text or "").replace("\n", "<br />")
    html_content = f"""
    <html>
    <head>
      <meta charset="utf-8" />
      <style>
        body {{ font-family: Arial, sans-serif; color: #222; margin: 0; padding: 0; background: #ffffff; }}
        .container {{ width: 100%; max-width: 1100px; margin: 0 auto; padding: 28px; }}
        .header {{ text-align: center; margin-bottom: 28px; }}
        .report-logo {{ max-height: 80px; margin-bottom: 18px; }}
        h1 {{ margin: 0; font-size: 32px; color: #1b3a73; }}
        .meta {{ font-size: 13px; color: #555; margin: 12px 0 24px; }}
        .report-section {{ margin-bottom: 36px; page-break-inside: avoid; }}
        .report-section h2 {{ font-size: 22px; margin-bottom: 12px; color: #1f447f; }}
        .report-image, .report-table-image {{ width: 100%; max-width: 100%; border: 1px solid #d0d0d0; border-radius: 10px; margin-bottom: 10px; }}
        .caption {{ font-size: 12px; color: #666; margin: 0 0 18px; }}
        .report-text {{ font-size: 13px; line-height: 1.7; color: #333; margin-bottom: 0; }}
        .section-header {{ margin-bottom: 4px; color: #444; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          {logo_html}
          <h1>{html_module.escape(title)}</h1>
          <div class="meta">Autor: {html_module.escape(author)} | Fecha: {html_module.escape(fecha_text)}</div>
          <div class="meta">{filters_html}</div>
        </div>
        {"\n".join(section_blocks)}
      </div>
    </body>
    </html>
    """
    return html_content


def build_report_html_pdf(title, author, logo_bytes, sections, fecha_text, filters_text=None):
    if WeasyHTML is None:
        raise ImportError("WeasyPrint no está instalado. Instalar weasyprint para generar PDF desde HTML.")
    html_content = build_report_html(title, author, logo_bytes, sections, fecha_text, filters_text)
    return WeasyHTML(string=html_content).write_pdf()


def build_graph_html_pdf(title, fig_png, table_png=None, filters_text=None, logo_bytes=None):
    if WeasyHTML is None:
        raise ImportError("WeasyPrint no está instalado. Instalar weasyprint para generar PDF desde HTML.")

    logo_html = ""
    if logo_bytes is not None:
        logo_base64 = base64.b64encode(logo_bytes).decode("utf-8")
        logo_html = f'<img class="report-logo" src="data:image/png;base64,{logo_base64}" alt="Logo" />'

    fig_b64 = base64.b64encode(fig_png).decode("utf-8")
    table_html = ""
    if table_png is not None:
        table_b64 = base64.b64encode(table_png).decode("utf-8")
        table_html = f"<div class='report-table'><img class='report-image' src='data:image/png;base64,{table_b64}' alt='Tabla' /></div>"

    filters_html = html_module.escape(filters_text or "").replace("\n", "<br />")

    html_content = f"""
    <html>
    <head>
      <meta charset='utf-8' />
      <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #fff; color: #222; }}
        .container {{ width: 100%; max-width: 1100px; margin: 0 auto; padding: 24px; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .report-logo {{ max-height: 70px; margin-bottom: 16px; }}
        h1 {{ font-size: 28px; color: #1c3d72; margin: 0 0 8px; }}
        .meta {{ font-size: 12px; color: #555; margin-bottom: 18px; }}
        .report-section {{ margin-bottom: 30px; page-break-inside: avoid; }}
        .report-section h2 {{ font-size: 20px; margin-bottom: 10px; color: #1f4a7d; }}
        .report-image, .report-table-image {{ width: 100%; border: 1px solid #ccc; border-radius: 10px; margin-bottom: 10px; }}
        .caption {{ font-size: 12px; color: #555; margin: 0 0 12px; }}
        .report-text {{ font-size: 13px; line-height: 1.6; color: #333; }}
      </style>
    </head>
    <body>
      <div class='container'>
        <div class='header'>
          {logo_html}
          <h1>{html_module.escape(title)}</h1>
          <div class='meta'>{filters_html}</div>
        </div>
        <div class='report-section'>
          <h2>{html_module.escape(title)}</h2>
          <div class='report-image-container'>
            <img class='report-image' src='data:image/png;base64,{fig_b64}' alt='Figura' />
          </div>
          {table_html}
        </div>
      </div>
    </body>
    </html>
    """

    return WeasyHTML(string=html_content).write_pdf()


def save_pdf_bytes_to_temp_file(pdf_bytes, filename=None):
    """Guarda pdf_bytes en un archivo temporal y devuelve la ruta del archivo."""
    if filename is None:
        filename = "reporte_temporal.pdf"
    temp_path = Path(tempfile.gettempdir()) / filename
    temp_path.write_bytes(pdf_bytes)
    return temp_path

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
                                    "width": "90%",
                                    "height": "auto",
                                    "objectFit": "contain",
                                    "marginBottom": "10px",
                                    "border": "1px solid #011c24",
                                    "borderRadius": "12px"
                                }
                            )
                        ],
                        style={
                            "flex": "0 0 160px",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "flex-start"
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
                                "DATA LOAD - Plataforma de Análisis Deportivo",
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
                            "minWidth": "2px"
                        }
                    )
                ],
                style={
                    "flex":"1",
                    "height":"90px",
                    "width": "80%",
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
            "paddingBottom": "12px"
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
    value="actividad_promedios",
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
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
            }
        ),

        dcc.Tab(
            label="ACTIVIDAD COMPARATIVA INDIVIDUAL",
            value="actividad_comparativa",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
            }
        ),

        dcc.Tab(
            label="ACTIVIDAD/PROMEDIOS",
            value="actividad_promedios",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
            }
        ),

        dcc.Tab(
            label="ACWR",
            value="acwr",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
            }
        ),
        
        dcc.Tab(
            label="PLYR vs PLYR",
            value="plyr_vs_plyr",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#edf1f2","fontSize":"12px","textAlign":"center","fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px","marginBottom":"1px"
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0","fontSize":"12px","textAlign":"center","fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px","backgroundColor":"#011c24","marginBottom":"1px"
            }
        ),

        dcc.Tab(
            label="COMPARATIVO",
            value="comparativas",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",      
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
            }
        ),

        dcc.Tab(
            label="CRONOLÓGICO",
            value="cronologico",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",      
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
            }
        ),
        dcc.Tab(
            label="INFORME",
            value="informe",
            className="tab-item",
            selected_className="tab-item-selected",
            style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#edf1f2",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid rgba(137,188,239,.18)",
                "padding":"2px 6px",       
                "marginBottom":"1px"       
            },
            selected_style={
                "whiteSpace": "normal",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "color":"#a3e3d0",
                "fontSize":"11px",
                "textAlign":"center",
                "fontWeight":"600",
                "borderTop":"1px solid #a3e3d0",
                "padding":"2px 6px",
                "backgroundColor":"#011c24",
                "marginBottom":"1px"
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
                "padding":"2px",
                "width":"160px",
                "background":"linear-gradient(180deg,#000c0f,#011c24)",
                "borderRadius":"12px",
                "border":"1px solid rgba(137,188,239,.18)"
                })
            ],

        style={
            "display":"flex",
            "flexDirection":"column",
            "width":"120px",
            "minWidth":"160px",
            "minHeight":"45vh",
            "gap":"2px 4px",
            "position":"sticky",
            "top":"100px",
            "alignSelf":"flex-start",
            "alignItems":"center"
        }),

        # ==================================================
        # CONTENIDO CENTRAL
        # ==================================================

        html.Div([

            dcc.Download(id="download-graph"),
            dcc.Download(id="download-table"),
            dcc.Download(id="download-report"),

            # GRÁFICO

            html.Div(    id="contenido-tab",
    className="tab-content",
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
                    "width": "180px",
                    "minWidth": "180px",
                    "padding": "24px",
                    "backgroundColor": "#011c24",
                    "borderRadius": "24px",
                    "border": "1px solid rgba(137, 188, 239, 0.16)",
                    "boxShadow": "0 18px 48px rgba(0,0,0,0.35)",
                    "position": "relative",
                    "top": "10px",
                    "maxHeight": "200vh",
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
    if tab in ["actividad", "actividad_comparativa", "actividad_promedios"]:
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
    metricas = [m for m in metricas if m in dff.columns]
    referencia = referencia or "Category"
    title_text = build_chart_title(tab, categorias, metricas, referencia)

    # COMPARATIVAS
    if tab == "comparativas":
        fig = build_comparativas(dff, categorias, metricas, referencia)
        return html.Div([
            dcc.Graph(
                className="tab-graph",
                figure=fig,
                style={"width":"100%", "height":"100%"}
            )
        ], style={
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
        })

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
                html.H3("Actividad por Jugador", style={"color":"white","textAlign":"center","marginBottom":"10px",
                                                        "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"}),
                html.H4(fecha_dt.strftime("%d/%m/%Y"), style={"color":"#a3e3d0","textAlign":"center","marginBottom":"15px",
                                                            "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"}),
                dcc.Loading(
                    html.Div(
                        className="tab-table-wrapper",
                        children=[
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
                                style_cell={
                                            "backgroundColor":"#1a1a1a","color":"white",
                                            "fontSize":"11px","textAlign":"center",
                                            "minWidth":"100px","whiteSpace":"normal"
                                            },
                                style_data_conditional=estilos_condicionales
                            )
                        ]
                    )
                )
            ], style={
                    "padding": "22px",
                    "background": "#0b0c0e",
                    "border": "1px solid rgba(137,188,239,0.18)",
                    "borderRadius": "24px",
                    "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"
                })
                        
  
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
            html.H4("Comparativo última ACTIVIDAD vs PROMEDIO",
                    style={"color":"white","textAlign":"center","marginBottom":"10px",
                                                        "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"}),
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

    elif tab == "actividad_promedios":
        fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
        dff_fecha = dff[dff["Date"].dt.normalize() == fecha_dt]

        metricas_promedios_validas = [m for m in metricas_promedios if m in dff_fecha.columns]
        resumen = dff_fecha[metricas_promedios_validas].mean().round(2).to_dict() if not dff_fecha.empty else {}

        categoria_text = summarize_items(categorias, max_items=10, default="Todas")
        gametag_text = summarize_items(gametags, max_items=10, default="Todos")
        periodtag_text = summarize_items(periodtags, max_items=10, default="Todos")
        fecha_text = fecha_dt.strftime("%d/%m/%Y")
        grafico_titulo = (
            f"Actividad {fecha_text}  |  Dinámica: {gametag_text}  |  Microciclo: {periodtag_text}  |  Plantel: {categoria_text}"
        )

        cards = []
        for m in metricas_promedios_validas:
            valor = resumen.get(m, 0)
            cards.append(
                html.Div([
                    html.Div(m, style={"color": "#a3e3d0", "fontSize": "13px", "marginBottom": "8px"}),
                    html.Div(f"{valor:.2f}", style={"color": "#edf1f2", "fontSize": "28px", "fontWeight": "700", "letterspacing": "1px"})
                ], style={
                    "padding": "20px",
                    "background": "#0b0c0e",
                    "border": "1px solid rgba(137,188,239,0.18)",
                    "borderRadius": "20px",
                    "boxShadow": "0 18px 40px rgba(0,0,0,0.25)",
                    "minWidth": "190px",
                    "flex": "1"
                })
            )

        return html.Div([
            html.Div([
                html.H3(grafico_titulo, style={"color":"white","textAlign":"center","marginBottom":"20px",
                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"}),
                html.Div([
                    html.Div([html.Div("Fecha de actividad", style={"color": "#a3e3d0", "fontSize": "12px", "marginBottom": "4px"}),
                              html.Div(fecha_text, style={"color": "#edf1f2", "fontSize": "14px", "fontWeight": "600"})],
                             style={"minWidth": "180px", "padding": "14px", "background": "#071016", "borderRadius": "18px", "border": "1px solid rgba(137,188,239,0.18)"}),
                    html.Div([html.Div("Game Tags", style={"color": "#a3e3d0", "fontSize": "12px", "marginBottom": "4px"}),
                              html.Div(gametag_text, style={"color": "#edf1f2", "fontSize": "14px", "fontWeight": "600"})],
                             style={"minWidth": "180px", "padding": "14px", "background": "#071016", "borderRadius": "18px", "border": "1px solid rgba(137,188,239,0.18)"}),
                    html.Div([html.Div("Period Tags", style={"color": "#a3e3d0", "fontSize": "12px", "marginBottom": "4px"}),
                              html.Div(periodtag_text, style={"color": "#edf1f2", "fontSize": "14px", "fontWeight": "600"})],
                             style={"minWidth": "180px", "padding": "14px", "background": "#071016", "borderRadius": "18px", "border": "1px solid rgba(137,188,239,0.18)"}),
                    html.Div([html.Div("Category", style={"color": "#a3e3d0", "fontSize": "12px", "marginBottom": "4px"}),
                              html.Div(categoria_text, style={"color": "#edf1f2", "fontSize": "14px", "fontWeight": "600"})],
                             style={"minWidth": "180px", "padding": "14px", "background": "#071016", "borderRadius": "18px", "border": "1px solid rgba(137,188,239,0.18)"})
                ], style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(180px, 1fr))", "gap": "16px", "marginBottom": "24px"})
            ], style={"marginBottom": "10px"}),
            html.Div(
                cards if cards else [html.Div("No hay datos para la fecha seleccionada.", style={"color": "#edf1f2", "textAlign": "center", "padding": "24px"})],
                style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))", "gap": "20px"}
            )
        ], style={"padding": "28px", "background": "linear-gradient(145deg, #0b0c0e, #1a1c1f)",
                    "border": "1px solid rgba(137,188,239,0.25)", "borderRadius": "28px",
                    "boxShadow": "0 12px 30px rgba(0,0,0,0.35)", "margin": "20px auto", "maxWidth": "1100px"})


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
                "color":"white","textAlign":"center","marginBottom":"10px",
                "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'","fontWeight":"600"
            }),

            dcc.Loading(

                html.Div(
                    className="tab-table-wrapper",
                    children=[
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
                            "backgroundColor":"#1a1a1a","color":"white",
                            "fontSize":"11px","textAlign":"center",
                            "minWidth":"100px","whiteSpace":"normal"
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
                        ]
                    )
                )
            ],style={
            "padding": "22px",
            "background": "#0b0c0e",
            "border": "1px solid rgba(137,188,239,0.18)",
            "borderRadius": "24px",
            "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"
})

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
                className="tab-graph",
                figure=fig,
                style={"width": "100%", "height": "100%"}
            ),
                style={"padding": "22px", "background": "#0b0c0e",
                    "border": "1px solid rgba(137,188,239,0.18)", "borderRadius": "24px",
                    "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"})

    elif tab == "informe":
        return html.Div([
            html.H2("Informe de Actividad", style={"color":"#edf1f2","textAlign":"center","marginBottom":"20px"}),
            html.Div([
                html.Div([
                    html.Label("Título del informe", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Input(id="report_title", type="text", placeholder="Título personalizado del informe (opcional)", value="", style={"width":"100%","padding":"10px","borderRadius":"12px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"}),
                    html.Div("Deja el título en blanco para generar uno automático.", style={"color":"#dcdcdc","fontSize":"11px","marginTop":"6px"})
                ], style={"flex":"1"}),
                html.Div([
                    html.Label("Creado por", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Input(id="report_author", type="text", placeholder="Nombre del creador", value="", style={"width":"100%","padding":"10px","borderRadius":"12px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"260px","marginLeft":"16px"}),
                html.Div([
                    html.Label("Fecha de actividad", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.DatePickerSingle(
                        id="report_fecha_actividad",
                        date=fecha_max.date(),
                        min_date_allowed=df["Date"].min().date(),
                        max_date_allowed=df["Date"].max().date(),
                        display_format="DD/MM/YYYY",
                        style={
                            "width": "100%",
                            "backgroundColor": "#011c24",
                            "color": "#f5f5f5",
                            "border": "1px solid rgba(137,188,239,0.18)",
                            "borderRadius": "12px",
                            "padding": "10px"
                        }
                    ),
                    html.Div("Selecciona la fecha de actividad para construir el informe.", style={"color":"#dcdcdc","fontSize":"11px","marginTop":"6px"})
                ], style={"flex":"1","minWidth":"260px","marginLeft":"16px"})
            ], style={"display":"flex","gap":"16px","marginBottom":"24px","flexWrap":"wrap"}),
            html.Div([
                html.Label("Secciones del informe", style={"color":"#a3e3d0","marginBottom":"8px"}),
                dcc.Checklist(
                    id="report_sections",
                    options=[
                        {"label": section_title(v), "value": v} for v in [
                            "actividad",
                            "actividad_comparativa",
                            "actividad_promedios",
                            "acwr",
                            "plyr_vs_plyr",
                            "comparativas",
                            "cronologico"
                        ]
                    ],
                    value=["actividad", "actividad_promedios", "acwr"],
                    labelStyle={"display":"block", "color":"#edf1f2", "marginBottom":"6px"},
                    inputStyle={"marginRight":"8px"}
                )
            ], style={"marginBottom":"28px","padding":"20px","background":"#071016","borderRadius":"18px","border":"1px solid rgba(137,188,239,0.18)"}),
            html.Div([
                html.Div([
                    html.Label("Actividad", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_actividad", placeholder="Describe la sección de Actividad. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"}),
                html.Div([
                    html.Label("Actividad Comparativa Individual", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_actividad_comparativa", placeholder="Describe la sección de Actividad Comparativa Individual. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"})
            ], style={"display":"flex","flexWrap":"wrap","gap":"16px","marginBottom":"16px"}),
            html.Div([
                html.Div([
                    html.Label("Actividad/Promedios", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_actividad_promedios", placeholder="Describe la sección de Actividad/Promedios. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"}),
                html.Div([
                    html.Label("ACWR", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_acwr", placeholder="Describe la sección de ACWR. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"})
            ], style={"display":"flex","flexWrap":"wrap","gap":"16px","marginBottom":"16px"}),
            html.Div([
                html.Div([
                    html.Label("PLYR vs PLYR", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_plyr_vs_plyr", placeholder="Describe la sección de PLYR vs PLYR. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"}),
                html.Div([
                    html.Label("Comparativo", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_comparativas", placeholder="Describe la sección de Comparativo. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"})
            ], style={"display":"flex","flexWrap":"wrap","gap":"16px","marginBottom":"16px"}),
            html.Div([
                html.Div([
                    html.Label("Cronológico", style={"color":"#a3e3d0","marginBottom":"6px"}),
                    dcc.Textarea(id="report_text_cronologico", placeholder="Describe la sección Cronológico. Hasta 500 palabras.", style={"width":"100%","height":"140px","borderRadius":"16px","border":"1px solid rgba(137,188,239,0.18)","background":"#071016","color":"#edf1f2"})
                ], style={"flex":"1","minWidth":"280px","marginBottom":"16px"})
            ], style={"display":"flex","flexWrap":"wrap","gap":"16px","marginBottom":"24px"}),
            html.Div(id="report_figures_preview", style={"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(320px,1fr))","gap":"20px","marginBottom":"24px"}),
            html.Div([
                html.Button("Generar PDF", id="generate_report", n_clicks=0, style={"width":"100%","padding":"16px","borderRadius":"18px","border":"none","background":"#89bcef","color":"#0b0c0e","fontWeight":"700","cursor":"pointer"})
            ], style={"maxWidth":"320px","margin":"0 auto"}),
            html.Div("Al hacer clic se generará un PDF con secciones seleccionadas, texto y gráficos incrustados.", style={"color":"#dcdcdc","fontSize":"12px","textAlign":"center","marginTop":"12px"})
        ], style={"padding":"24px","background":"#0b0c0e","border":"1px solid rgba(137,188,239,0.18)","borderRadius":"28px","boxShadow":"0 18px 40px rgba(0,0,0,0.25)","maxWidth":"1180px","margin":"20px auto"})

    # ======================================================
# PLYR vs PLYR
# ======================================================

    elif tab == "plyr_vs_plyr":
        return html.Div([
            html.H3(
                "Comparativa Jugador vs Jugador", 
                style={
                    "color":"white",
                    "textAlign":"center",
                    "marginBottom":"20px",
                    "fontFamily":"'Clash Display Semibold', 'Helvetica Neue'",
                    "fontWeight":"600"
                }
            ),

            # Dropdowns para elegir jugadores
            html.Div([
                dcc.Dropdown(
                    id="jugador_1",
                    options=[{"label": j, "value": j} for j in dff["Player Name"].unique()],
                    value=dff["Player Name"].unique()[0],
                    placeholder="Seleccionar Jugador 1",
                    style={"width":"45%","display":"inline-block","marginRight":"10px", "color":"#0d1620"}
                ),
                dcc.Dropdown(
                    id="jugador_2",
                    options=[{"label": j, "value": j} for j in dff["Player Name"].unique()],
                    value=dff["Player Name"].unique()[1] if len(dff["Player Name"].unique())>1 else None,
                    placeholder="Seleccionar Jugador 2",
                    style={"width":"45%","display":"inline-block","color":"#0d1620"}
                )
            ], style={"display":"flex","justifyContent":"center","marginBottom":"20px"}),

            # Filtros adicionales
            html.Div([
                dcc.Dropdown(
                    id="game_tags",
                    options=[{"label": g, "value": g} for g in dff["Game Tags"].unique()],
                    placeholder="Filtrar por Game Tag",
                    style={"width":"45%","display":"inline-block","marginRight":"10px","color":"#0d1620"}
                ),
                dcc.Dropdown(
                    id="period_tags",
                    options=[{"label": p, "value": p} for p in dff["Period Tags"].unique()],
                    placeholder="Filtrar por Period Tag",
                    style={"width":"45%","display":"inline-block", "color":"#0d1620"}
                )
            ], style={"display":"flex","justifyContent":"center","marginBottom":"20px"}),

            # Gráfico
            dcc.Graph(id="radar_chart", className="tab-graph", style={"height":"600px"})
        ], style={
            "padding":"28px",
            "background":"linear-gradient(145deg, #0b0c0e, #1a1c1f)",
            "border":"1px solid rgba(137,188,239,0.25)",
            "borderRadius":"28px",
            "boxShadow":"0 12px 30px rgba(0,0,0,0.35)",
            "margin":"20px auto",
            "maxWidth":"900px"
        })

    else:
        return no_update


@app.callback(
    Output("gametag", "options"),
    Output("gametag", "value"),
    Output("periodtag", "options"),
    Output("periodtag", "value"),
    Input("fecha-actividad", "date"),
    Input("categoria", "value")
)
def actualizar_tags_por_fecha_categoria(fecha_actividad, categorias):
    dff = df.copy()
    if fecha_actividad:
        fecha_dt = pd.to_datetime(fecha_actividad).normalize()
        dff = dff[dff["Date"].dt.normalize() == fecha_dt]
    if categorias:
        dff = dff[dff["Category"].isin(categorias)]

    gametag_vals = sorted(dff["Game Tags"].dropna().unique())
    periodtag_vals = sorted(dff["Period Tags"].dropna().unique())

    gametag_options = [{"label": x, "value": x} for x in gametag_vals]
    periodtag_options = [{"label": x, "value": x} for x in periodtag_vals]

    return gametag_options, gametag_vals, periodtag_options, periodtag_vals


@app.callback(
    Output("report_figures_preview", "children"),
    Input("report_sections", "value"),
    Input("categoria", "value"),
    Input("report_fecha_actividad", "date")
)
def actualizar_vista_previa_informe(sections, categorias, fecha_actividad):
    if not sections:
        return html.Div(
            "Selecciona al menos una sección para ver las figuras en el informe.",
            style={"color": "#edf1f2", "textAlign": "center", "padding": "20px"}
        )

    dff = df.copy()
    if categorias:
        dff = dff[dff["Category"].isin(categorias)]

    fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
    if fecha_dt is not None:
        dff = dff[dff["Date"].dt.normalize() <= fecha_dt]

    preview_cards = []
    for section in sections:
        try:
            fig = build_section_report_fig(section, dff, fecha_dt, categorias)
        except Exception:
            fig = None

        if fig is None or not fig.data:
            preview_cards.append(
                html.Div(
                    [
                        html.H4(section_title(section), style={"color": "#a3e3d0", "marginBottom": "10px"}),
                        html.Div(
                            "No hay figura disponible para esta sección con los filtros seleccionados.",
                            style={"color": "#edf1f2", "fontSize": "14px"}
                        )
                    ],
                    style={
                        "padding": "18px",
                        "background": "#0b0c0e",
                        "border": "1px solid rgba(137,188,239,0.18)",
                        "borderRadius": "24px",
                        "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"
                    }
                )
            )
        else:
            preview_cards.append(
                html.Div(
                    [
                        html.H4(section_title(section), style={"color": "#a3e3d0", "marginBottom": "10px"}),
                        dcc.Graph(
                            className="tab-graph",
                            figure=fig,
                            config={"displayModeBar": False},
                            style={"height": "320px", "width": "100%"}
                        )
                    ],
                    style={
                        "padding": "18px",
                        "background": "#0b0c0e",
                        "border": "1px solid rgba(137,188,239,0.18)",
                        "borderRadius": "24px",
                        "boxShadow": "0 18px 40px rgba(0,0,0,0.25)"
                    }
                )
            )

    return preview_cards


@app.callback(
    Output("download-report", "data"),
    Input("generate_report", "n_clicks"),
    State("report_title", "value"),
    State("report_author", "value"),
    State("report_sections", "value"),
    State("report_text_actividad", "value"),
    State("report_text_actividad_comparativa", "value"),
    State("report_text_actividad_promedios", "value"),
    State("report_text_acwr", "value"),
    State("report_text_plyr_vs_plyr", "value"),
    State("report_text_comparativas", "value"),
    State("report_text_cronologico", "value"),
    State("categoria", "value"),
    State("report_fecha_actividad", "date"),
    prevent_initial_call=True
)
def generar_informe(
    n_clicks,
    title,
    author,
    sections,
    texto_actividad,
    texto_actividad_comparativa,
    texto_actividad_promedios,
    texto_acwr,
    texto_plyr_vs_plyr,
    texto_comparativas,
    texto_cronologico,
    categorias,
    fecha_actividad
):
    if not n_clicks:
        return no_update

    title = title.strip() if title else build_auto_report_title(categorias, fecha_actividad)
    author = author.strip() if author else "Desconocido"
    fecha_text = pd.to_datetime(fecha_actividad).strftime("%d/%m/%Y") if fecha_actividad else datetime.now().strftime("%d/%m/%Y")

    dff = df.copy()
    if categorias:
        dff = dff[dff["Category"].isin(categorias)]

    fecha_dt = pd.to_datetime(fecha_actividad).normalize() if fecha_actividad else dff["Date"].max().normalize()
    if fecha_dt is not None:
        dff = dff[dff["Date"].dt.normalize() <= fecha_dt]

    section_texts = {
        "actividad": texto_actividad or "",
        "actividad_comparativa": texto_actividad_comparativa or "",
        "actividad_promedios": texto_actividad_promedios or "",
        "acwr": texto_acwr or "",
        "plyr_vs_plyr": texto_plyr_vs_plyr or "",
        "comparativas": texto_comparativas or "",
        "cronologico": texto_cronologico or ""
    }
    selected_sections = sections or ["actividad", "actividad_promedios", "acwr"]

    filtros = []
    if categorias:
        filtros.append(f"Categorías: {', '.join(categorias)}")
    filtros.append(f"Fecha: {fecha_text}")
    filters_text = " | ".join(filtros)

    report_sections = []
    for section in selected_sections:
        fig = None
        table_fig = None
        try:
            fig = build_section_report_fig(section, dff, fecha_dt, categorias)
        except Exception as e:
            logging.exception("Error construyendo figura para sección %s", section)
            fig = None

        try:
            table_fig = build_section_report_table_fig(section, dff, fecha_dt, categorias)
        except Exception as e:
            logging.exception("Error construyendo tabla para sección %s", section)
            table_fig = None

        img_bytes = None
        if fig is not None and getattr(fig, "data", None):
            img_bytes = fig_to_png_bytes(fig, width=1200, height=900, scale=2)
            if img_bytes is None:
                logging.warning("No se generaron bytes PNG para figura de sección %s", section)

        table_bytes = None
        if table_fig is not None and getattr(table_fig, "data", None):
            table_bytes = fig_to_png_bytes(table_fig, width=1200, height=520, scale=2)
            if table_bytes is None:
                logging.warning("No se generaron bytes PNG para tabla de sección %s", section)

        logging.info(
            "Sección %s: img_bytes=%s table_bytes=%s",
            section,
            len(img_bytes) if img_bytes is not None else None,
            len(table_bytes) if table_bytes is not None else None,
        )

        section_img = img_bytes if img_bytes is not None else None
        section_table_img = table_bytes if table_bytes is not None else None

        section_note = ""
        if section_img is None and section_table_img is None:
            section_note = "\nNota: no se generó ninguna imagen o tabla para esta sección con los filtros seleccionados."

        report_sections.append({
            "title": section_title(section),
            "text": truncate_to_n_words(section_texts.get(section, ""), 500) + section_note,
            "img": section_img,
            "table_img": section_table_img,
            "caption": f"Figura: {section_title(section)} con los filtros seleccionados.",
            "table_caption": f"Tabla: {section_title(section)} con los filtros seleccionados."
        })

    if not any(item["text"] for item in report_sections):
        for item in report_sections:
            item["text"] = f"Informe de la sección {item['title']} generado automáticamente."

    logo_bytes = base64.b64decode(LOGO_BASE64) if LOGO_BASE64 else None
    if WeasyHTML is not None:
        try:
            pdf_bytes = build_report_html_pdf(title, author, logo_bytes, report_sections, fecha_text, filters_text)
        except Exception as e:
            logging.exception("Error generando PDF HTML con WeasyPrint, usando ReportLab como fallback.")
            pdf_bytes = build_report_pdf(title, author, logo_bytes, report_sections, fecha_text, filters_text)
    else:
        pdf_bytes = build_report_pdf(title, author, logo_bytes, report_sections, fecha_text, filters_text)
    filename = f"{title.replace(' ', '_')}_{fecha_text.replace('/', '-')}.pdf"
    return dcc.send_bytes(lambda buf: buf.write(pdf_bytes), filename)


@app.callback(
    Output("radar_chart", "figure"),
    [
        Input("jugador_1", "value"),
        Input("jugador_2", "value"),
        Input("game_tags", "value"),
        Input("period_tags", "value")
    ]
)
def actualizar_radar(jugador_1, jugador_2, game_tags, period_tags):
    dff_filtrado = df.copy()

    if game_tags:
        dff_filtrado = dff_filtrado[dff_filtrado["Game Tags"] == game_tags]
    if period_tags:
        dff_filtrado = dff_filtrado[dff_filtrado["Period Tags"] == period_tags]

    if not jugador_1 or not jugador_2:
        return go.Figure()

    jugadores = [jugador_1, jugador_2]
    dff_jugadores = dff_filtrado[dff_filtrado["Player Name"].isin(jugadores)]

    if dff_jugadores.empty:
        return go.Figure()

    # Agrupar métricas
    radar_data = (
        dff_jugadores.groupby("Player Name")[metricas_radar]
        .mean()
        .reset_index()
    )

    # Normalización por columna (min-max a 0–1)
    radar_data_norm = radar_data.copy()
    for m in metricas_radar:
        col_min = radar_data[m].min()
        col_max = radar_data[m].max()
        if col_max > col_min:  # evita división por cero
            radar_data_norm[m] = (radar_data[m] - col_min) / (col_max - col_min)

    # Crear figura
    fig = go.Figure()
    colores = ["#48f788", "#89bcef"]

    for idx, row in radar_data_norm.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=row[metricas_radar].values.flatten().tolist(),
            theta=metricas_radar,
            fill="toself",
            name=row["Player Name"],
            mode="markers+lines",
            marker=dict(size=6, color=colores[idx % len(colores)]),
            line=dict(color=colores[idx % len(colores)], width=2),
             fillcolor=f"rgba{tuple(int(colores[idx % len(colores)][1+i:3+i],16) for i in (0,2,4)) + (0.25,)}",
            text=[f"{val:.2f}" for val in row[metricas_radar].values.flatten().tolist()], 
            textposition="top center",
            textfont=dict(size=10, color="#edf1f2")
            ))

    # Estilo
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                showline=True,
                linewidth=1,
                gridcolor="rgba(200,200,200,0.25)",
                gridwidth=0.8,
                tickfont=dict(size=12, color="#edf1f2")
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#edf1f2")
            )
        ),
        showlegend=True,
        template="plotly_dark",
        title=dict(
            text=f"{jugador_1}  ||  {jugador_2}",  
        font=dict(size=20, color="#a3e3d0", family="Manrope Light"),
        x=0.5
        ),
        legend=dict(
            font=dict(size=13, color="#edf1f2"),
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0.4)",
            bordercolor="rgba(137,188,239,0.25)",
            borderwidth=1
        )
    )

    return fig

                    
@app.callback(
    Output("download-graph","data"),
    Input("download-graph-png","n_clicks"),
    Input("download-graph-pdf","n_clicks"),
    State("tabs","value"),
    State("categoria","value"),
    State("metrica","value"),
    State("referencia","value"),
    State("jugador","value"),
    State("athlete","value"),
    State("gametag","value"),
    State("periodtag","value"),
    State("fecha-actividad","date"),
    State("jugador_1","value"),
    State("jugador_2","value"),
    State("game_tags","value"),
    State("period_tags","value"),
    prevent_initial_call=True
)
def descargar_grafico(_n_png, _n_pdf,
                      tab, categorias, metricas, referencia,
                      jugadores, athlete, gametags, periodtags, fecha_actividad,
                      jugador_1, jugador_2, game_tags, period_tags):

    # Detectar qué botón disparó
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id not in ["download-graph-png", "download-graph-pdf"]:
        return no_update

    fmt = "png" if trigger_id == "download-graph-png" else "pdf"

    # Filtrar dataframe
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

    # Construir figura según tab
    if tab == "actividad":
        fig = build_actividad_report_fig(dff, fecha_actividad)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    elif tab == "actividad_comparativa":
        fig = build_actividad_comparativa_report_fig(dff, fecha_actividad)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    elif tab == "actividad_promedios":
        fig = build_actividad_promedios_report_fig(dff, fecha_actividad)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    elif tab == "acwr":
        fig = build_acwr_report_fig(dff)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    elif tab == "plyr_vs_plyr":
        fig = build_plyr_vs_plyr(dff, jugador_1, jugador_2, game_tags, period_tags)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    elif tab == "comparativas":
        fig = build_comparativas(dff, categorias, metricas, referencia)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    elif tab == "cronologico":
        fig = build_cronologico(dff, categorias, metricas, referencia)
        table_fig = build_section_report_table_fig(tab, dff, fecha_actividad, categorias)
    else:
        return no_update

    if fig is None or not getattr(fig, "data", None):
        logging.warning("No hay figura disponible para exportar en el tab %s", tab)
        return no_update

    tab_name = tab_titles.get(tab, tab).replace(" ", "_")
    filename = f"grafico_{tab_name}.{fmt}"

    table_png = None
    if table_fig is not None and getattr(table_fig, "data", None):
        table_png = fig_to_png_bytes(table_fig, width=1200, height=520, scale=2)
        if table_png is None:
            logging.warning("No se pudo generar PNG de la tabla para el tab %s", tab)

    fig_png = fig_to_png_bytes(fig, width=1200, height=800, scale=2)
    if fig_png is None:
        logging.warning("No se pudo generar PNG para la figura del tab %s", tab)
        return no_update

    if fmt == "png":
        image_bytes = combine_image_bytes_vertically([fig_png, table_png]) if table_png is not None else fig_png
    else:
        filters_text = f"Categorías: {', '.join(categorias) if categorias else 'Todas'}"
        logo_bytes = base64.b64decode(LOGO_BASE64) if LOGO_BASE64 else None
        try:
            image_bytes = build_graph_html_pdf(
                title=tab_titles.get(tab, tab),
                fig_png=fig_png,
                table_png=table_png,
                filters_text=filters_text,
                logo_bytes=logo_bytes,
            )
        except Exception as e:
            logging.exception("Error generando PDF con WeasyPrint para el tab %s: %s", tab, e)
            return no_update

    if image_bytes is None:
        logging.warning("No se pudo exportar el tab %s en formato %s", tab, fmt)
        return no_update

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
    Input("fecha-actividad","date"),
    prevent_initial_call=True
)
def descargar_tabla(
    _n_csv,
    _n_xlsx,
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

