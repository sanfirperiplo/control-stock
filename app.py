import streamlit as st
import pandas as pd

st.set_page_config(page_title="Control Roturas", layout="wide")
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

c1, c2 = st.columns(2)
file_f = c1.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
file_s = c2.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

if file_f and file_s:
    with st.spinner('Analizando datos...'):
        # 1. Carga profesional con limpieza de nombres
        df_f = pd.read_excel(file_f) if file_f.name.endswith('.xlsx') else pd.read_csv(file_f)
        df_s = pd.read_excel(file_s) if file_s.name.endswith('.xlsx') else pd.read_csv(file_s)
        
        # Limpieza profunda de espacios y formato
        df_f.columns = [str(c).strip().upper() for c in df_f.columns]
        df_s.columns = [str(c).strip().upper() for c in df_s.columns]

        # 2. Localización flexible de columnas
        id_f = next((c for c in df_f.columns if 'ID' in c), None)
        id_s = next((c for c in df_s.columns if 'ID' in c), None)
        # Buscamos variantes comunes de stock
        stk_col = next((c for c in df_s.columns if any(x in c for x in ['STOCK', 'DISP', 'CANTIDAD'])), None)

        if id_f and id_s and stk_col:
            # 3. Conversión de tipos (CRÍTICO: esto soluciona el problema del 0)
            df_s[stk_col] = pd.to_numeric(df_s[stk_col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Cruce
            df_c = pd.merge(df_f, df_s, left_on=id_f, right_on=id_s, how='inner')
            
            # Filtrado de roturas
            df_res = df_c[df_c[stk_col] <= 2]

            st.success(f"✅ Análisis completado. Se han detectado {len(df_res)} artículos en rotura.")
            st.dataframe(df_res)

            # Exportación
            csv = df_res.to_csv(index=False, sep=';', encoding='utf-8-sig')
            st.download_button("📥 DESCARGAR INFORME", csv, "roturas.csv", "text/csv")
        else:
            st.error("Error: No se pudieron mapear las columnas. Columnas detectadas:")
            st.write("Folleto:", df_f.columns.tolist())
            st.write("Stock:", df_s.columns.tolist())
