 import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Roturas", layout="wide")
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# Carga de archivos
c1, c2 = st.columns(2)
f_folleto = c1.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
f_stock = c2.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

if f_folleto and f_stock:
    # Carga inteligente de datos
    df_f = pd.read_excel(f_folleto) if f_folleto.name.endswith('.xlsx') else pd.read_csv(f_folleto)
    df_s = pd.read_excel(f_stock) if f_stock.name.endswith('.xlsx') else pd.read_csv(f_stock)

    # Función para encontrar columnas de forma flexible (no importa el nombre exacto)
    def buscar_col(df, palabras):
        for col in df.columns:
            if any(p.upper() in str(col).upper() for p in palabras):
                return col
        return None

    id_f, id_s = buscar_col(df_f, ['ID']), buscar_col(df_s, ['ID'])
    col_stk = buscar_col(df_s, ['STOCK', 'DISP'])

    if id_f and id_s and col_stk:
        df_cruce = pd.merge(df_f, df_s, left_on=id_f, right_on=id_s, how='inner')
        df_cruce[col_stk] = pd.to_numeric(df_cruce[col_stk], errors='coerce').fillna(0)
        df_roturas = df_cruce[df_cruce[col_stk] <= 2]

        st.subheader(f"Incidencias detectadas: {len(df_roturas)}")
        st.dataframe(df_roturas)

        # Descarga con codificación para Excel
        csv = df_roturas.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("📥 FICHERO ROTURAS DE FOLLETO", csv, "roturas.csv", "text/csv")

        # Impresión (HTML directo, sin Base64 complejo para evitar errores)
        if st.button("🖨️ GENERAR VISTA DE IMPRESIÓN"):
            html = f"<html><head><meta charset='utf-8'></head><body>{df_roturas.to_html()}</body></html>"
            st.components.v1.html(html, height=600, scrolling=True)
    else:
        st.error("No se detectaron las columnas 'ID' o 'STOCK' en los archivos. Revisa los nombres.")
