import streamlit as st
import pandas as pd

# Configuración técnica de alta estabilidad
st.set_page_config(page_title="Control de Roturas Profesional", layout="wide")
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)

# Entrada de archivos
c1, c2 = st.columns(2)
file_f = c1.file_uploader("Fichero del Folleto (Excel/CSV)", type=["xlsx", "csv"])
file_s = c2.file_uploader("Fichero de Stock (Excel/CSV)", type=["xlsx", "csv"])

if file_f and file_s:
    with st.spinner('Validando y procesando datos...'):
        # 1. Carga técnica
        df_f = pd.read_excel(file_f) if file_f.name.endswith('.xlsx') else pd.read_csv(file_f)
        df_s = pd.read_excel(file_s) if file_s.name.endswith('.xlsx') else pd.read_csv(file_s)
        
        # Limpieza de encabezados (Normalización)
        df_f.columns = [str(c).strip().upper().replace(" ", "_") for c in df_f.columns]
        df_s.columns = [str(c).strip().upper().replace(" ", "_") for c in df_s.columns]

        # 2. Diagnóstico de columnas (Visualización de control para el usuario)
        st.sidebar.markdown("### 🔍 Diagnóstico de Datos")
        st.sidebar.write("Columnas Folleto:", df_f.columns.tolist())
        st.sidebar.write("Columnas Stock:", df_s.columns.tolist())

        # 3. Lógica de cruce blindada
        # Buscamos columnas que contengan 'ID' o 'COD'
        id_f = next((c for c in df_f.columns if 'ID' in c or 'COD' in c), None)
        id_s = next((c for c in df_s.columns if 'ID' in c or 'COD' in c), None)
        # Buscamos columnas de stock más exhaustivamente
        stk_col = next((c for c in df_s.columns if any(x in c for x in ['STOCK', 'DISP', 'CANTIDAD', 'UNIDADES'])), None)

        if id_f and id_s and stk_col:
            # Conversión forzada de stock a numérico real
            df_s[stk_col] = pd.to_numeric(df_s[stk_col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Cruce de datos
            df_res = pd.merge(df_f, df_s, left_on=id_f, right_on=id_s, how='inner')
            
            # Filtrado estricto
            df_final = df_res[df_res[stk_col] <= 2].copy()

            st.success(f"✅ Análisis exitoso: {len(df_final)} artículos detectados en rotura.")
            st.dataframe(df_final, use_container_width=True)

            # 4. Exportación profesional
            col_a, col_b = st.columns(2)
            csv = df_final.to_csv(index=False, sep=';', encoding='utf-8-sig')
            col_a.download_button("📥 DESCARGAR INFORME (CSV)", csv, "informe_roturas.csv", "text/csv")
            
            # Botón de impresión (HTML plano y seguro)
            if col_b.button("🖨️ GENERAR IMPRESIÓN"):
                html = f"<html><head><meta charset='utf-8'></head><body><h2>Informe de Roturas</h2>{df_final.to_html(index=False)}</body></html>"
                st.components.v1.html(html, height=600, scrolling=True)
        else:
            st.error("Error crítico de cruce: No se han encontrado columnas compatibles.")
            st.warning("Asegúrate de que ambos archivos tengan una columna que contenga 'ID' o 'COD' y el archivo de stock contenga 'STOCK', 'DISP' o 'CANTIDAD'.")
