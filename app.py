import streamlit as st
import pandas as pd

st.set_page_config(page_title="Diagnóstico Técnico", layout="wide")
st.title("🛠️ Módulo de Diagnóstico de Datos")

file_f = st.file_uploader("Sube Fichero Folleto", type=["xlsx", "csv"], key="f")
file_s = st.file_uploader("Sube Fichero Stock", type=["xlsx", "csv"], key="s")

if file_f and file_s:
    # Carga de datos
    df_f = pd.read_excel(file_f) if file_f.name.endswith('.xlsx') else pd.read_csv(file_f)
    df_s = pd.read_excel(file_s) if file_s.name.endswith('.xlsx') else pd.read_csv(file_s)
    
    # NORMALIZACIÓN
    df_f.columns = [str(c).strip().upper() for c in df_f.columns]
    df_s.columns = [str(c).strip().upper() for c in df_s.columns]

    # MOSTRAR EN PANTALLA PARA VER EL PROBLEMA
    st.write("### Columnas detectadas en FOLLETO:")
    st.write(df_f.columns.tolist())
    st.write("### Columnas detectadas en STOCK:")
    st.write(df_s.columns.tolist())
    
    st.write("---")
    
    # Intentar identificar ID y STOCK
    id_col = st.text_input("Escribe AQUÍ el nombre exacto de la columna ID (tiene que ser igual a uno de arriba):")
    stk_col = st.text_input("Escribe AQUÍ el nombre exacto de la columna STOCK:")
    
    if id_col and stk_col:
        try:
            df_s[stk_col] = pd.to_numeric(df_s[stk_col], errors='coerce').fillna(0)
            df_res = pd.merge(df_f, df_s, left_on=id_col, right_on=id_col, how='inner')
            df_final = df_res[df_res[stk_col] <= 2]
            
            st.success(f"Se han encontrado {len(df_final)} roturas.")
            st.dataframe(df_final)
        except Exception as e:
            st.error(f"Error en el cruce: {e}")
