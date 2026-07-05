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
st.write("Sube los archivos para extraer el listado formateado listo para revisión.")

st.subheader("📁 1. Cargar Archivos")
file_folleto = st.file_uploader("Sube el Fichero del Folleto (SMS CON FOTO...)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Sube el Fichero de Stock (010...)", type=["xlsx", "csv"], key="stock")

if file_folleto and file_stock:
    try:
        # Leer ficheros (soporta Excel y CSV)
        df_folleto = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
        df_stock = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)

        # Limpiar espacios en los encabezados de las columnas
        df_folleto.columns = df_folleto.columns.str.strip()
        df_stock.columns = df_stock.columns.str.strip()

        st.success("¡Ficheros cargados con éxito!")

        # Validar que ambos tienen la columna clave 'ID'
        if 'ID' in df_folleto.columns and 'ID' in df_stock.columns:
            
            # --- NORMALIZACIÓN DE IDs ---
            # Pasamos a texto limpio quitando decimales ocultos (.0) para asegurar el cruce
            df_folleto['ID'] = pd.to_numeric(df_folleto['ID'], errors='coerce').fillna(-1).astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_stock['ID'] = pd.to_numeric(df_stock['ID'], errors='coerce').fillna(-2).astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

            # Columnas requeridas del archivo 010
            columnas_stock_necesarias = ['ID', 'EAN', 'Descripción Artículo', 'PVP normal', 'Stock Disp']
            
            # Verificar que existan en el archivo de stock
            missing_cols = [col for col in columnas_stock_necesarias if col not in df_stock.columns]
            
            if not missing_cols:
                # --- CORRECCIÓN CRÍTICA DE STOCK ---
                # Convertimos 'Stock Disp' a número. Si está vacío (NaN) o da error, lo convertimos en 0 de forma automática.
                df_stock['Stock Disp'] = pd.to_numeric(df_stock['Stock Disp'], errors='coerce').fillna(0)

                # Limpieza estricta del EAN (Código de barras) para evitar formatos raros en pantalla
                df_stock['EAN'] = pd.to_numeric(df_stock['EAN'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()

                # Cruzar primero el folleto completo con los datos de stock
                df_cruce = pd.merge(df_folleto[['ID']], df_stock[columnas_stock_necesarias], on='ID', how='inner')
                
                # Eliminar duplicados si un artículo viene repetido
                df_cruce = df_cruce.drop_duplicates(subset=['ID'])

                # --- CORRECCIÓN DEL FILTRO DE ROTURAS ---
                # Extraemos los artículos cuyo stock disponible sea menor o igual a 0
                df_formato_solicitado = df_cruce[df_cruce['Stock Disp'] <= 0].copy()

                # Reordenar las columnas al formato exacto solicitado de 5 columnas
                # Formato: EAN | ID | Descripción Artículo | PVP normal | Stock Disp
                df_formato_solicitado = df_formato_solicitado[['EAN', 'ID', 'Descripción Artículo', 'PVP normal', 'Stock Disp']]

                # --- MOSTRAR RESULTADOS ---
                st.subheader("📊 2. Resumen de Alertas")
                c1, c2 = st.columns(2)
                c1.metric("Artículos en Folleto", len(df_folleto['ID'].unique()))
                c2.metric("Roturas de Folleto 🚨", len(df_formato_solicitado), delta_color="inverse")

                st.subheader("📋 3. Vista Previa del Fichero de Roturas")
                if len(df_formato_solicitado) > 0:
                    # Mostrar la tabla limpia en pantalla de forma nativa y perfecta
                    st.dataframe(df_formato_solicitado, use_container_width=True, hide_index=True)
                    
                    # Preparación exclusiva para la descarga en Excel (Truco del formateo de celdas largas)
                    df_descarga = df_formato_solicitado.copy()
                    df_descarga['EAN'] = df_descarga['EAN'].apply(lambda x: f"'\t{x}")
                    
                    # Guardar en CSV estructurado con punto y coma (;)
                    csv_data = df_descarga.to_csv(index=False, sep=';', encoding='utf-8-sig')
                    
                    st.download_button(
                        label="📥 Descargar Fichero de Roturas Formateado",
                        data=csv_data,
                        file_name="roturas_folleto_formato_final.csv",
                        mime="text/csv",
                    )
                else:
                    st.success("✅ ¡Todo en orden! Todos los artículos del folleto tienen Stock Disponible en tienda.")
            else:
                st.error(f"❌ El archivo de stock (010) no contiene todas las columnas requeridas. Faltan: {missing_cols}")
        else:
            st.error("❌ Error: No se encontró la columna 'ID' en alguno de los dos archivos para poder cruzarlos.")
            
    except Exception as e:
        st.error(f"Ocurrió un error en el procesado: {e}")
else:
    st.info("💡 Sube ambos ficheros para generar automáticamente el documento con la estructura de 5 columnas solicitada.")
