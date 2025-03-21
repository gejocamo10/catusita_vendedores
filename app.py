import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# --- CONFIGURAR USUARIO Y CONTRASEÑA ---
USER = "admin"
PASSWORD = "catusita123"

# --- FUNCION DE LOGIN ---
def login():
    st.title("🔐 Inicio de Sesión")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user == USER and password == PASSWORD:
            st.session_state["logueado"] = True
        else:
            st.error("Usuario o contraseña incorrectos")

# --- LOGIN Y CONTROL DE SESIÓN ---
if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

if not st.session_state["logueado"]:
    login()
    st.stop()

# --- CONTENIDO DEL DASHBOARD ---
# Cargar el archivo CSV
ruta_csv = "df_sales_cleaned.csv"  # Ajusta esta ruta según la ubicación de tu archivo CSV
df = pd.read_csv(ruta_csv)

# Convertir columna 'fecha' a datetime
df['fecha'] = pd.to_datetime(df['fecha'])

# Crear columna 'year-month' para agrupar datos por mes y año
df['year-month'] = df['fecha'].dt.strftime('%Y-%m')

# Crear columna de mes en español
df['mes'] = df['fecha'].dt.strftime('%B')
meses_es = {
    "January": "Enero", "February": "Febrero", "March": "Marzo", "April": "Abril",
    "May": "Mayo", "June": "Junio", "July": "Julio", "August": "Agosto",
    "September": "Septiembre", "October": "Octubre", "November": "Noviembre", "December": "Diciembre"
}
df['mes'] = df['mes'].map(meses_es)

# Crear columna de año
df['año'] = df['fecha'].dt.year

# Calcular las fechas límite para los filtros de 3, 6 y 12 meses
hoy = datetime.today()
ayer = hoy - timedelta(days=1)
fecha_3_meses = ayer - pd.DateOffset(months=3)
fecha_6_meses = ayer - pd.DateOffset(months=6)
fecha_12_meses = ayer - pd.DateOffset(months=12)

# Dashboard Streamlit
st.title("📊 Dashboard de Ventas - Catusita")

# Filtros interactivos
lista_vendedores = ["Todos"] + sorted(df['nombre_vendedor'].unique().tolist())
vendedor_especifico = st.selectbox('Selecciona un vendedor:', lista_vendedores)

lista_articulos = ["Todos"] + sorted(df['articulo'].unique().tolist())
articulo_especifico = st.selectbox('Selecciona un artículo:', lista_articulos, index=0)

lista_fuentes = ["Todos"] + sorted(df['fuente_suministro'].astype(str).unique().tolist())
fuente_especifica = st.selectbox('Selecciona una fuente de suministro:', lista_fuentes, index=0)

lista_años = ["Todos"] + sorted(df['año'].unique(), reverse=True)
año_especifico = st.selectbox('Selecciona un año:', lista_años)

# Opciones de filtro por meses
st.subheader("Filtrar por últimos meses")
col1, col2, col3 = st.columns(3)

filtro_meses = None
with col1:
    if st.button("Últimos 3 meses"):
        filtro_meses = fecha_3_meses
with col2:
    if st.button("Últimos 6 meses"):
        filtro_meses = fecha_6_meses
with col3:
    if st.button("Últimos 12 meses"):
        filtro_meses = fecha_12_meses

# Filtrar el DataFrame
if vendedor_especifico != "Todos":
    df = df[df['nombre_vendedor'] == vendedor_especifico]

if articulo_especifico != "Todos":
    df = df[df['articulo'] == articulo_especifico]

if fuente_especifica != "Todos":
    df = df[df['fuente_suministro'].astype(str) == fuente_especifica]

# Aplicar filtros de fechas
if filtro_meses:
    df = df[df['fecha'] >= filtro_meses]
    agrupar_por = 'year-month'
elif año_especifico != "Todos":
    df = df[df['año'] == año_especifico]
    agrupar_por = 'mes'
else:
    agrupar_por = 'Total'

# Ordenar los datos
if agrupar_por == 'year-month':
    df = df.sort_values(by='year-month', ascending=True)
elif agrupar_por == 'mes':
    orden_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    df["mes"] = pd.Categorical(df["mes"], categories=orden_meses, ordered=True)
    df = df.sort_values(by="mes")

# Verificar si hay datos después del filtrado
if df.empty:
    st.warning("No hay datos disponibles para el período seleccionado.")
else:
    # Tabla por fuente de suministro
    tabla_fuente = df.pivot_table(index='fuente_suministro',
                                  columns=agrupar_por if agrupar_por != 'Total' else None,
                                  values='venta_usd',
                                  aggfunc='sum',
                                  fill_value=0,
                                  observed=False)

    tabla_fuente['Total'] = tabla_fuente.sum(axis=1)
    tabla_fuente.loc['Total'] = tabla_fuente.sum()

    tabla_fuente.index.name = "Fuente Suministro"
    tabla_fuente = tabla_fuente.round(0).astype(int)

    # Tabla por cliente
    tabla_cliente = df.pivot_table(index='nombre_cliente',
                                   columns=agrupar_por if agrupar_por != 'Total' else None,
                                   values='venta_usd',
                                   aggfunc='sum',
                                   fill_value=0,
                                   observed=False)

    tabla_cliente['Total'] = tabla_cliente.sum(axis=1)
    tabla_cliente.loc['Total'] = tabla_cliente.sum()

    tabla_cliente.index.name = "Cliente"
    tabla_cliente = tabla_cliente.round(0).astype(int)

    # Mostrar solo "Total" si el año seleccionado es "Todos"
    if año_especifico == "Todos":
        tabla_fuente = tabla_fuente[['Total']]
        tabla_cliente = tabla_cliente[['Total']]

    # Mostrar resultados
    st.subheader("Tabla por Fuente de Suministro")
    st.dataframe(tabla_fuente.style.set_properties(**{'text-align': 'center'}))

    st.subheader("Tabla por Cliente")
    st.dataframe(tabla_cliente.style.set_properties(**{'text-align': 'center'}))
