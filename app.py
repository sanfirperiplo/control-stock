   import streamlit as st
import pandas as pd

# Configuración de página adaptada para PC y iPhone
st.set_page_config(
    page_title="Control de Stock - Folletos",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos limpios y optimizados para el móvil
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { font-size: 24px !important; font-weight: 700; text-align: center; color: #1E3A8A; margin-bottom: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1E3A8A; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Generador de Fichero de Roturas")
st.write("Sube los archivos para extraer el listado formateado listo para revisión e impresión con códigos escaneables.")

st.subheader("📁 1. Cargar Archivos")
file_folleto = st.file_uploader("Sube el Fichero del Folleto (SMS CON FOTO...)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Sube el Fichero de Stock (010...)", type=["xlsx", "csv"], key="stock")

if file_folleto and file_stock:
    try:
        # Leer ficheros (soporta Excel y CSV)
        df_folleto = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
        df_stock = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)

        # --- NORMALIZADOR DE COLUMNAS INTELIGENTE ---
        def normalizar_columnas(df):
            mapeo = {}
            for col in df.columns:
                col_limpia = str(col).strip().lower()
                col_limpia = col_limpia.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                col_limpia = col_limpia.replace('/', ' ')
                mapeo[col_limpia] = col
            return mapeo

        map_folleto = normalizar_columnas(df_folleto)
        map_stock = normalizar_columnas(df_stock)

        # Identificar las columnas obligatorias principales
        col_id_folleto = map_folleto.get('id')
        col_id_stock = map_stock.get('id')
        col_ean = map_stock.get('ean')
        col_desc = map_stock.get('descripcion articulo')
        col_pvp = map_stock.get('pvp normal')
        col_stock = map_stock.get('stock disp')
        
        # Columnas opcionales
        col_fap = map_stock.get('fap')
        col_ubi = map_stock.get('ubicacion')
        col_promo = map_folleto.get('descriptivo promocion')
        
        # Búsqueda flexible para la columna PCB
        col_pcb = None
        for key in map_stock.keys():
            if 'pcb' in key or 'unidades caja' in key:
                col_pcb = map_stock[key]
                break

        st.success("¡Ficheros cargados con éxito!")

        # Validar que existan las columnas obligatorias
        if col_id_folleto and col_id_stock and col_ean and col_desc and col_pvp and col_stock:
            
            # --- LIMPIEZA DE IDs DE TEXTO RADICAL ---
            def limpiar_id_estricto(serie):
                return serie.astype(str).str.strip().str.split('.').str[0]

            df_folleto['ID_limpio'] = limpiar_id_estricto(df_folleto[col_id_folleto])
            df_stock['ID_limpio'] = limpiar_id_estricto(df_stock[col_id_stock])

            # Preparar dataframe base de stock a extraer
            columnas_a_extraer = ['ID_limpio', col_id_stock, col_ean, col_desc, col_pvp, col_stock]
            if col_pcb: columnas_a_extraer.append(col_pcb)
            if col_fap: columnas_a_extraer.append(col_fap)
            if col_ubi: columnas_a_extraer.append(col_ubi)

            df_stock_limpio = df_stock[columnas_a_extraer].copy()

            # Cruzar folleto con stock (010)
            df_cruce = pd.merge(df_folleto[['ID_limpio']], df_stock_limpio, on='ID_limpio', how='inner')
            
            # Cruzar para rescatar la columna promocional si existe
            if col_promo:
                df_folleto_promo = df_folleto[['ID_limpio', col_promo]].drop_duplicates(subset=['ID_limpio'])
                df_cruce = pd.merge(df_cruce, df_folleto_promo, on='ID_limpio', how='left')

            # Eliminar duplicados si un artículo está repetido
            df_cruce = df_cruce.drop_duplicates(subset=['ID_limpio'])

            # --- CONVERSIÓN DE STOCK ---
            df_cruce['Stock_Numerico'] = pd.to_numeric(df_cruce[col_stock], errors='coerce').fillna(0)

            # --- FILTRO DE CRITERIO SOLICITADO: Stock Disp <= 2 ---
            df_roturas = df_cruce[df_cruce['Stock_Numerico'] <= 2].copy()

            # Limpieza estética de códigos EAN e ID
            df_roturas['EAN_Limpiado'] = pd.to_numeric(df_roturas[col_ean], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
            df_roturas['ID_Final'] = df_roturas['ID_limpio'].astype(str)

            # Asignación segura de campos extras por si vienen vacíos
            df_roturas['PCB_val'] = df_roturas[col_pcb].fillna('-').astype(str).str.split('.').str[0] if col_pcb else '-'
            df_roturas['FAP_val'] = df_roturas[col_fap].fillna('-').astype(str) if col_fap else '-'
            df_roturas['UBI_val'] = df_roturas[col_ubi].fillna('-').astype(str) if col_ubi else '-'
            df_roturas['PROMO_val'] = df_roturas[col_promo].fillna('-').astype(str) if col_promo else '-'

            # Formato de visualización plano en la web (5 columnas originales)
            df_formato_pantalla = pd.DataFrame({
                'EAN': df_roturas['EAN_Limpiado'],
                'ID': df_roturas['ID_Final'],
                'Descripción Artículo': df_roturas[col_desc],
                'PVP normal': df_roturas[col_pvp],
                'Stock Disp': df_roturas['Stock_Numerico']
            })

            # --- MOSTRAR RESULTADOS ---
            st.subheader("📊 2. Resumen de Alertas")
            c1, c2 = st.columns(2)
            c1.metric("Artículos en Folleto", len(df_folleto['ID_limpio'].unique()))
            c2.metric("Roturas de Folleto (Stock <= 2) 🚨", len(df_formato_pantalla), delta_color="inverse")

            st.subheader("📋 3. Vista Previa del Fichero de Roturas")
            
            if len(df_formato_pantalla) > 0:
                st.dataframe(df_formato_pantalla, use_container_width=True, hide_index=True)
                
                # --- BOTONES DE ACCIÓN E IMPRESIÓN ---
                st.subheader("🛠️ 4. Acciones e Impresión")
                
                # 1. Botón para Descargar CSV básico para Excel
                df_descarga = df_formato_pantalla.copy()
                df_descarga['EAN'] = df_descarga['EAN'].apply(lambda x: f"'\t{x}")
                csv_data = df_descarga.to_csv(index=False, sep=';', encoding='utf-8-sig')
                st.download_button(
                    label="📥 Descargar Fichero para Excel",
                    data=csv_data,
                    file_name="roturas_folleto_formato_final.csv",
                    mime="text/csv",
                )
                
                st.write("")
