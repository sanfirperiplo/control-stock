import streamlit as st
import pandas as pd

# Configuración inicial
st.set_page_config(page_title="Control Roturas", layout="wide")
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# Entrada de archivos
c1, c2 = st.columns(2)
file_folleto = c1.file_uploader("Fichero del Folleto", type=["xlsx", "csv"])
file_stock = c2.file_uploader("Fichero de Stock (010)", type=["xlsx", "csv"])

if file_folleto and file_stock:
    # Usamos un indicador visual profesional mientras trabaja
    with st.spinner('Procesando datos...'):
        # Carga y limpieza de encabezados
        df_f = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
        df_s = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)
        
        df_f.columns = [str(c).strip().upper().replace(" ", "_") for c in df_f.columns]
        df_s.columns = [str(c).strip().upper().replace(" ", "_") for c in df_s.columns]

        # Búsqueda dinámica de columnas
        id_f = next((c for c in df_f.columns if 'ID' in c), None)
        id_s = next((c for c in df_s.columns if 'ID' in c), None)
        stk_col = next((c for c in df_s.columns if 'STOCK' in c or 'DISP' in c), None)

        if id_f and id_s and stk_col:
            # Cruce de datos
            df_c = pd.merge(df_f, df_s, left_on=id_f, right_on=id_s, how='inner')
            # Aseguramos que el stock sea numérico
            df_c[stk_col] = pd.to_numeric(df_c[stk_col], errors='coerce').fillna(0)
            df_roturas = df_c[df_c[stk_col] <= 2]

            st.write(f"### Incidencias detectadas: {len(df_roturas)}")
            st.dataframe(df_roturas)

            # Botones de acción
            col1, col2 = st.columns(2)
            csv = df_roturas.to_csv(index=False, sep=';', encoding='utf-8-sig')
            col1.download_button("📥 DESCARGAR INFORME", csv, "roturas.csv", "text/csv")
            
            # Impresión limpia
            if col2.button("🖨️ GENERAR VISTA DE IMPRESIÓN"):
                html = f"<html><head><meta charset='utf-8'></head><body>{df_roturas.to_html()}</body></html>"
                st.components.v1.html(html, height=600)
        else:
            st.error("No se detectaron las columnas 'ID' o 'STOCK'. Revisa los nombres en tus archivos.")
