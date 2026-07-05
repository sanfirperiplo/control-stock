import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Roturas", layout="wide")
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# 1. Carga de archivos
c1, c2 = st.columns(2)
file_f = c1.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
file_s = c2.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

if file_f and file_s:
    with st.spinner('Procesando cruce de datos...'):
        # Carga y limpieza de encabezados
        df_f = pd.read_excel(file_f) if file_f.name.endswith('.xlsx') else pd.read_csv(file_f)
        df_s = pd.read_excel(file_s) if file_s.name.endswith('.xlsx') else pd.read_csv(file_s)
        
        df_f.columns = [str(c).strip().upper().replace(" ", "_") for c in df_f.columns]
        df_s.columns = [str(c).strip().upper().replace(" ", "_") for c in df_s.columns]

        # 2. Búsqueda inteligente de columnas (sin importar el nombre exacto)
        id_f = next((c for c in df_f.columns if 'ID' in c), None)
        id_s = next((c for c in df_s.columns if 'ID' in c), None)
        stk_col = next((c for c in df_s.columns if any(p in c for p in ['STOCK', 'DISP', 'CANTIDAD'])), None)

        if id_f and id_s and stk_col:
            # Cruce de datos
            df_c = pd.merge(df_f, df_s, left_on=id_f, right_on=id_s, how='inner')
            # Forzamos conversión a número para evitar que <= 2 falle
            df_c[stk_col] = pd.to_numeric(df_c[stk_col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            df_res = df_c[df_c[stk_col] <= 2]

            st.success(f"✅ Análisis terminado: {len(df_res)} artículos en rotura.")
            st.dataframe(df_res)

            # 3. Acciones (Botones claros y funcionales)
            col1, col2 = st.columns(2)
            csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig')
            col1.download_button("📥 DESCARGAR INFORME", csv, "roturas.csv", "text/csv")
            
            # Botón de impresión profesional
            if col2.button("🖨️ GENERAR VISTA DE IMPRESIÓN"):
                html = f"<html><head><meta charset='utf-8'></head><body>{df_res.to_html(index=False)}</body></html>"
                st.components.v1.html(html, height=600, scrolling=True)
        else:
            st.error("Error de mapeo. Columnas detectadas:")
            st.write("Folleto:", df_f.columns.tolist())
            st.write("Stock:", df_s.columns.tolist())
