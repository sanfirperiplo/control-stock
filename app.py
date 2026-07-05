import streamlit as st
import pandas as pd

# Configuración de página profesional
st.set_page_config(page_title="Control de Roturas", layout="wide")

st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# Carga de ficheros con manejo de tipos
col1, col2 = st.columns(2)
with col1:
    file_folleto = st.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
with col2:
    file_stock = st.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

# Función para limpiar encabezados y evitar errores de columna
def normalizar_df(df):
    df.columns = [str(c).strip().upper().replace(" ", "_") for c in df.columns]
    return df

if file_folleto and file_stock:
    try:
        # Carga inteligente
        df_f = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
        df_s = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)
        
        df_f = normalizar_df(df_f)
        df_s = normalizar_df(df_s)

        # Cruce de datos (ajustado a nombres comunes tras normalización)
        # Asegúrate de que tus archivos tengan una columna ID en ambos
        df_cruce = pd.merge(df_f, df_s, on='ID', how='inner')
        
        # Búsqueda dinámica de la columna stock (busca cualquiera que contenga la palabra STOCK)
        col_stock = [c for c in df_cruce.columns if 'STOCK' in c][0]
        
        # Filtrado de roturas (stock <= 2)
        df_roturas = df_cruce[pd.to_numeric(df_cruce[col_stock], errors='coerce') <= 2]

        st.subheader(f"Incidencias detectadas: {len(df_roturas)}")
        st.dataframe(df_roturas)

        # Descarga en formato limpio (UTF-8 con BOM para Excel)
        csv = df_roturas.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("📥 FICHERO ROTURAS DE FOLLETO", csv, "roturas.csv", "text/csv")

        # Impresión limpia (sin errores de codificación)
        if st.button("🖨️ GENERAR VISTA DE IMPRESIÓN"):
            html_impresion = f"<html><head><meta charset='utf-8'></head><body><h2>Informe de Roturas</h2>{df_roturas.to_html()}<script>window.print();</script></body></html>"
            st.components.v1.html(html_impresion)
            
    except Exception as e:
        st.error(f"Error al procesar: {e}. Revisa que ambos archivos tengan la columna 'ID'.")
