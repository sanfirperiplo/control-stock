import streamlit as st
import pandas as pd
import base64

# 1. CONFIGURACIÓN CORPORATIVA DE LA PÁGINA
st.set_page_config(
    page_title="Control de Roturas de Folleto",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos CSS avanzados para una interfaz moderna, limpia y profesional
st.markdown("""
    <style>
    .main .block-container { 
        padding-top: 2.5rem; 
        padding-bottom: 3.5rem; 
        max-width: 850px;
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

st.markdown("<h1>📊 FICHERO ROTURAS DE FOLLETO</h1>", unsafe_allow_html=True)
st.markdown("<p class=\"subtitle-app\">Panel analítico profesional • Cruce automático de stock de tienda frente a folleto promocional</p>", unsafe_allow_html=True)

st.markdown("### 📁 1. Entrada de Datos")
file_folleto = st.file_uploader("Fichero del Folleto (Formatos SMS, Fotos, etc.)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Fichero de Stock (Plantilla de volcado 010 actual)", type=["xlsx", "csv"], key="stock")

ejecutar_procesado = False
df_folleto = None
df_stock = None

if file_folleto and file_stock:
    ejecutar_procesado = True

if not ejecutar_procesado:
    st.info("💡 Sube ambos documentos para realizar la consolidación y aplicar las reglas de stock crítico.")

# --- INICIO DEL PROCESAMIENTO PRINCIPAL ---
if ejecutar_procesado:
    try:
        if file_folleto.name.endswith('.xlsx'):
            df_folleto = pd.read_excel(file_folleto)
        else:
            df_folleto = pd.read_csv(file_folleto)
            
        if file_stock.name.endswith('.xlsx'):
            df_stock = pd.read_excel(file_stock)
        else:
            df_stock = pd.read_csv(file_stock)

        # Mapeo y normalización de nombres de columnas
        mapeo_folleto = {str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' '): col for col in df_folleto.columns}
        mapeo_stock = {str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' '): col for col in df_stock.columns}

        col_id_folleto = mapeo_folleto.get('id')
        col_id_stock = mapeo_stock.get('id')
        col_ean = mapeo_stock.get('ean')
        col_desc = mapeo_stock.get('descripcion articulo')
        col_pvp = mapeo_stock.get('pvp normal')
        col_stock = mapeo_stock.get('stock disp')
        col_fap = mapeo_stock.get('fap')
        col_ubi = mapeo_stock.get('ubicacion')
        col_promo = mapeo_folleto.get('descriptivo promocion')
        
        col_pcb = None
        for key, val in mapeo_stock.items():
            if 'pcb' in key or 'unidades caja' in key:
                col_pcb = val
                break

        if col_id_folleto and col_id_stock and col_ean and col_desc and col_pvp and col_stock:
            # Limpieza de identificadores ID
            df_folleto['ID_limpio'] = df_folleto[col_id_folleto].astype(
