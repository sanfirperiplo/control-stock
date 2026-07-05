import streamlit as st
import pandas as pd
import base64
import urllib.parse

# 1. CONFIGURACIÓN CORPORATIVA DE LA PÁGINA
st.set_page_config(
    page_title="Control de Roturas de Folleto",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS avanzados para una interfaz moderna, limpia y adaptada a iPhone y PC
st.markdown("""
    <style>
    .main .block-container { 
        padding-top: 2.5rem; 
        padding-bottom: 3.5rem; 
        max-width: 800px;
    }
    
    h1 { 
        font-size: 30px !important; 
        font-weight: 800; 
        text-align: center; 
        color: #1E3A8A; 
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    h3 {
        font-size: 19px !important;
        font-weight: 600;
        color: #374151;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    .subtitle-app {
        text-align: center;
        color: #6B7280;
        font-size: 14px;
        margin-bottom: 35px;
    }
    
    .stFileUploader {
        padding: 20px;
        background-color: #F9FAFB;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.4em; 
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); 
        color: white; 
        font-weight: bold; 
        border: none;
        box-shadow: 0 4px 10px -2px rgba(37, 99, 235, 0.2);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 14px -1px rgba(37, 99, 235, 0.3);
    }
    
    div[data-testid="stMetric"] {
        background-color: #F3F4F6;
        padding: 18px;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
    }
    div[data-testid="stMetricValue"] { 
        font-size: 34px !important; 
        font-weight: 800;
        color: #111827;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado de la aplicación
st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)
st.markdown("<p class=\"subtitle-app\">Panel analítico profesional • Cruce automático de stock de tienda frente a folleto promocional</p>", unsafe_allow_html=True)

st.markdown("### 📁 1. Entrada de Datos")
file_folleto = st.file_uploader("Fichero del Folleto (Formatos SMS, Fotos, etc.)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Fichero de Stock (Plantilla de volcado 010 actual)", type=["xlsx", "csv"], key="stock")

# Declaración lineal de variables de control de flujo
ejecutar_procesado = False
if file_folleto and file_stock:
    ejecutar_procesado = True

if not ejecutar_procesado:
    st.info("💡 Sube ambos documentos para realizar la consolidación y aplicar las reglas de stock crítico.")

# --- NÚCLEO DE PROCESAMIENTO PLANO ---
if ejecutar_procesado:
    try:
        # Lectura de ficheros
        df_folleto = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
        df_stock = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)

        # Normalizador de cadenas
        def get_mapeo(df):
            return {str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' '): col for col in df.columns}

        mapeo_folleto = get_mapeo(df_folleto)
        mapeo_stock = get_mapeo(df_stock)

        col_id_folleto = mapeo_folleto.get('id')
        col_id_stock = mapeo_stock.get('id')
        col_ean = mapeo_stock.get('ean')
        col_desc = mapeo_stock.get('descripcion articulo')
        col_pvp = mapeo_stock.get('pvp normal')
        col_stock = mapeo_stock.get('stock disp')
        col_fap = mapeo_stock.get('fap')
        col_ubi = mapeo_stock.get('ubicacion')
        col_promo = mapeo_folleto.get('descriptivo promocion')
        
        col_pcb = next((val for key, val in mapeo_stock.items() if 'pcb' in key or 'unidades caja' in key), None)

        if all([col_id_folleto, col_id_stock, col_ean, col_desc, col_pvp, col_stock]):
            df_folleto['ID_limpio'] = df_folleto[col_id_folleto].astype(str).str.split('.').str[0]
            df_stock['ID_limpio'] = df_stock[col_id_stock].astype(str).str.split('.').str[0]

            columnas_a_extraer = ['ID_limpio', col_id_stock, col_ean, col_desc, col_pvp, col_stock]
            if col_pcb: columnas_a_extraer.append(col_pcb)
            if col_fap: columnas_a_extraer.append(col_fap)
            if col_ubi: columnas_a_extraer.append(col_ubi)

            df_cruce = pd.merge(df_folleto[['ID_limpio']], df_stock[columnas_a_extraer], on='ID_limpio', how='inner')
            
            if col_promo:
                df_cruce = pd.merge(df_cruce, df_folleto[['ID_limpio', col_promo]].drop_duplicates(subset=['ID_limpio']), on='ID_limpio', how='left')

            df_roturas = df_cruce[pd.to_numeric(df_cruce[col_stock], errors='coerce').fillna(0) <= 2].copy()
            df_roturas['Stock_Numerico'] = pd.to_numeric(df_roturas[col_stock], errors='coerce').fillna(0)
            df_roturas['EAN_Limpiado'] = pd.to_numeric(df_roturas[col_ean], errors='coerce').fillna(0).astype(int).astype(str)

            st.markdown("### 📊 2. Indicadores de Estado")
            c1, c2 = st.columns(2)
            c1.metric("Artículos en Folleto", f"{len(df_folleto['ID_limpio'].unique())} uds")
            c2.metric("Roturas de Stock 🚨", f"{len(df_roturas)} uds")

            if len(df_roturas) > 0:
                st.dataframe(df_roturas[['EAN_Limpiado', col_desc, col_stock]], use_container_width=True, hide_index=True)
                
                st.markdown("### 🛠— 4. Herramientas de Exportación")
                
                # Preparación del CSV
                df_excel = df_roturas.copy()
                csv_data = df_excel.to_csv(index=False, sep=';', encoding='utf-8-sig')
                
                st.download_button(
                    label="DESCARGA EL FICHERO ROTURAS DE FOLLETO",
                    data=csv_data,
                    file_name="roturas_folleto_tienda.csv",
                    mime="text/csv"
                )
            else:
                st.success("✨ ¡Todo correcto! No hay roturas detectadas.")

    except Exception as e:
        st.error(f"Error técnico: {e}")
