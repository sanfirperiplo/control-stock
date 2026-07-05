import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control de Roturas", layout="wide")
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# 1. Entrada de datos
c1, c2 = st.columns(2)
file_f = c1.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
file_s = c2.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

if file_f and file_s:
    # Usamos un spinner profesional para el tiempo de carga
    with st.spinner('Procesando datos y cruzando referencias...'):
        def leer_archivo(f):
            df = pd.read_excel(f) if f.name.endswith('.xlsx') else pd.read_csv(f)
            df.columns = [str(c).strip().upper().replace(" ", "_") for c in df.columns]
            return df

        df_f = leer_archivo(file_f)
        df_s = leer_archivo(file_s)

        # Diagnóstico de columnas (para depurar por qué da 0)
        st.sidebar.write("### Diagnóstico técnico:")
        st.sidebar.write("Cols Folleto:", df_f.columns.tolist())
        st.sidebar.write("Cols Stock:", df_s.columns.tolist())

        # Búsqueda inteligente de columnas (Hardcoded keys)
        id_f = next((c for c in df_f.columns if 'ID' in c), None)
        id_s = next((c for c in df_s.columns if 'ID' in c), None)
        stk_col = next((c for c in df_s.columns if 'STOCK' in c or 'DISP' in c), None)

        if id_f and id_s and stk_col:
            # Cruce de datos
            df_c = pd.merge(df_f, df_s, left_on=id_f, right_on=id_s, how='inner')
            df_c[stk_col] = pd.to_numeric(df_c[stk_col], errors='coerce').fillna(0)
            df_res = df_c[df_c[stk_col] <= 2]

            st.success(f"✅ Procesamiento finalizado. Incidencias detectadas: {len(df_res)}")
            st.dataframe(df_res)

            # Botones profesionales
            col_d1, col_d2 = st.columns(2)
            csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig')
            col_d1.download_button("📥 DESCARGAR INFORME", csv, "roturas.csv", "text/csv")
            
            if col_d2.button("🖨️ GENERAR IMPRESIÓN"):
                html = f"<html><head><meta charset='utf-8'></head><body>{df_res.to_html()}</body></html>"
                st.components.v1.html(html, height=600)
        else:
            st.error("Error crítico: No se localizaron columnas coincidentes.")
            st.warning("Asegúrate de que ambos archivos tengan una columna con la palabra 'ID'.")
