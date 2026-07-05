import streamlit as st
import pandas as pd

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Control Roturas", layout="wide")

st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# CARGA DE FICHEROS
col1, col2 = st.columns(2)
with col1:
    file_folleto = st.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
with col2:
    file_stock = st.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

if file_folleto and file_stock:
    # LECTURA DE DATOS
    df_folleto = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
    df_stock = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)

    # NORMALIZACIÓN BÁSICA (Asumiendo nombres comunes de columnas)
    # Ajusta los nombres de las columnas aquí si es necesario
    df_folleto.columns = [c.strip().upper() for c in df_folleto.columns]
    df_stock.columns = [c.strip().upper() for c in df_stock.columns]

    # PROCESAMIENTO (Ejemplo de cruce)
    # Asegúrate de que los nombres de columnas coincidan con tus archivos reales
    df_cruce = pd.merge(df_folleto, df_stock, left_on='ID', right_on='ID', how='inner')
    df_roturas = df_cruce[df_cruce['STOCK'] <= 2]

    st.subheader("Resumen de Incidencias")
    st.dataframe(df_roturas)

    # EXPORTACIÓN
    csv = df_roturas.to_csv(index=False, sep=';', encoding='utf-8-sig')
    st.download_button(
        label="📥 FICHERO ROTURAS DE FOLLETO",
        data=csv,
        file_name="roturas_folleto.csv",
        mime="text/csv"
    )

    # VISTA DE IMPRESIÓN (HTML limpio)
    html_impresion = f"""
    <html>
    <head><meta charset="utf-8"></head>
    <body>
        <h2>LISTADO DE ROTURAS</h2>
        {df_roturas.to_html(index=False)}
        <script>window.print();</script>
    </body>
    </html>
    """
    st.components.v1.html(html_impresion, height=0)
