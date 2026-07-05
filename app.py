import streamlit as st
import pandas as pd

# Configuración técnica
st.set_page_config(page_title="Control de Roturas", layout="wide")

st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# 1. Entrada de datos
c1, c2 = st.columns(2)
file_f = c1.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
file_s = c2.file_uploader("Fichero de Stock", type=["xlsx", "csv"])

# 2. Motor de normalización (Soluciona KeyError)
def procesar_archivo(uploaded_file):
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('.xlsx') else pd.read_csv(uploaded_file)
    df.columns = [str(c).strip().upper().replace(" ", "_") for c in df.columns]
    return df

if file_f and file_s:
    df_f = procesar_archivo(file_f)
    df_s = procesar_archivo(file_s)

    # Detección dinámica de columnas clave
    id_col = next((c for c in df_f.columns if 'ID' in c), None)
    stk_col = next((c for c in df_s.columns if 'STOCK' in c or 'DISP' in c), None)

    if id_col and stk_col:
        # Cruce y filtrado
        df_c = pd.merge(df_f, df_s, left_on=id_col, right_on=id_col, how='inner')
        df_c[stk_col] = pd.to_numeric(df_c[stk_col], errors='coerce').fillna(0)
        df_res = df_c[df_c[stk_col] <= 2]

        st.success(f"Procesamiento finalizado: {len(df_res)} incidencias.")
        st.dataframe(df_res)

        # Exportación profesional (UTF-8 con BOM para Excel)
        csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig')
        st.download_button("📥 DESCARGAR INFORME", csv, "roturas.csv", "text/csv")
        
        # Impresión limpia (Inyección HTML directa)
        if st.button("🖨️ GENERAR IMPRESIÓN"):
            html = f"<html><head><meta charset='utf-8'></head><body>{df_res.to_html()}</body></html>"
            st.components.v1.html(html, height=600)
    else:
        st.error("Error de diagnóstico: No se han podido identificar las columnas 'ID' o 'STOCK'. Revisa los encabezados.")
