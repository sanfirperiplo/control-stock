import streamlit as st
import pandas as pd

# Configuración de la página para que se adapte perfectamente a móviles (iOS/Android) y PC
st.set_page_config(
    page_title="Control de Stock - Folletos",
    page_icon="📊",
    layout="centered", # Centrado funciona mejor en pantallas verticales de teléfonos
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para mejorar la apariencia en iPhone (fuentes más limpias, botones grandes)
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        font-size: 24px !important;
        font-weight: 700;
        text-align: center;
        color: #1E3A8A;
        margin-bottom: 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #1E3A8A;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Control de Roturas de Stock")
st.write("Sube tus archivos desde cualquier PC o Teléfono para cruzar los datos en tiempo real.")

# Sección de subida de archivos
st.subheader("📁 1. Cargar Archivos")

file_folleto = st.file_uploader("Fichero del Folleto / Campaña (Excel o CSV)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Fichero de Stock Actualizado (Excel o CSV)", type=["xlsx", "csv"], key="stock")

# Inicializar proceso al tener ambos ficheros
if file_folleto and file_stock:
    try:
        # Carga inteligente de datos según formato
        if file_folleto.name.endswith('.xlsx'):
            df_folleto = pd.read_excel(file_folleto)
        else:
            df_folleto = pd.read_csv(file_folleto)
            
        if file_stock.name.endswith('.xlsx'):
            df_stock = pd.read_excel(file_stock)
        else:
            df_stock = pd.read_csv(file_stock)

        # Normalización automática de las columnas (pasa todo a minúsculas y quita espacios)
        df_folleto.columns = df_folleto.columns.str.lower().str.strip()
        df_stock.columns = df_stock.columns.str.lower().str.strip()

        st.success("¡Ficheros cargados con éxito!")

        # Buscador de columna de enlace (Código de barras, Referencia, SKU, EAN)
        columnas_posibles = ['codigo', 'id', 'referencia', 'sku', 'ean', 'cod', 'articulo']
        col_clave = None
        
        for col in columnas_posibles:
            if col in df_folleto.columns and col in df_stock.columns:
                col_clave = col
                break
        
        # Si no detecta una columna común por defecto, toma la primera columna que coincida en ambos
        if not col_clave:
            coincidencias = list(set(df_folleto.columns).intersection(set(df_stock.columns)))
            if coincidencias:
                col_clave = coincidencias[0]

        if col_clave:
            st.info(f"🔗 Cruzando datos automáticamente por la columna: **'{col_clave.upper()}'**")
            
            # Asegurar que el stock se llame 'stock'
            col_stock = None
            for col in ['stock', 'cantidad', 'existencias', 'actual']:
                if col in df_stock.columns:
                    col_stock = col
                    break
            if not col_stock:
                col_stock = df_stock.columns[1] # Si no encuentra, toma la segunda columna del archivo de stock
            
            # Renombrar columna de stock para el análisis uniforme
            df_stock_temp = df_stock[[col_clave, col_stock]].rename(columns={col_stock: 'stock_actual'})
            
            # Cruzar datos (Merge)
            df_analisis = pd.merge(df_folleto, df_stock_temp, on=col_clave, how='left')
            df_analisis['stock_actual'] = df_analisis['stock_actual'].fillna(0) # Si no está en el archivo, el stock es 0

            # Buscar columna de descripción/nombre de producto
            col_desc = None
            for col in ['descripcion', 'nombre', 'producto', 'articulo', 'detalle']:
                if col in df_folleto.columns:
                    col_desc = col
                    break
            if not col_desc:
                col_desc = col_clave # Clave como respaldo

            # Determinar si hay rotura (Stock Actual == 0 o menor que el mínimo si existe)
            col_min = None
            for col in ['minimo', 'stock_min', 'seguridad', 'objetivo']:
                if col in df_folleto.columns:
                    col_min = col
                    break
            
            if col_min:
                df_analisis['en_rotura'] = df_analisis['stock_actual'] < df_analisis[col_min]
            else:
                df_analisis['en_rotura'] = df_analisis['stock_actual'] <= 0

            # Filtrar las roturas detectadas
            df_roturas = df_analisis[df_analisis['en_rotura'] == True]

            # --- VISTA DE RESULTADOS (Métricas optimizadas para móvil) ---
            st.subheader("📊 2. Estado de Alertas")
            
            c1, c2 = st.columns(2)
            c1.metric("Artículos Folleto", len(df_folleto))
            c2.metric("Roturas Detectadas 🚨", len(df_roturas), delta_color="inverse")

            st.subheader("📋 3. Detalle de Productos Afectados")
            if not df_roturas.empty:
                # Mostrar solo las columnas más importantes para que quepa bien en la pantalla del iPhone
                columnas_a_mostrar = [col_clave, col_desc, 'stock_actual']
                if col_min:
                    columnas_a_mostrar.append(col_min)
                
                # Cambiar nombres de columnas para la visualización final
                df_mostrar = df_roturas[columnas_a_mostrar].copy()
                st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
                
                # Descarga del informe en formato CSV (Funciona nativamente en Safari de iOS)
                csv = df_roturas.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Listado de Roturas",
                    data=csv,
                    file_name="roturas_detectadas.csv",
                    mime="text/csv",
                )
            else:
                st.success("✅ ¡Excelente! Todos los artículos del folleto tienen stock suficiente.")

        else:
            st.error("❌ Error: No se ha encontrado ninguna columna común (como 'codigo', 'id' o 'referencia') para cruzar los dos archivos. Revisa los encabezados.")

    except Exception as e:
        st.error(f"Ocurrió un error inesperado al procesar los ficheros: {e}")
else:
    st.info("💡 Esperando archivos... Sube ambos documentos para ver el análisis automáticamente.")
