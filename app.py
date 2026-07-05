import streamlit as st
import pandas as pd

# Configuración óptima para ordenadores y pantallas de iPhone
st.set_page_config(
    page_title="Control de Stock - Folletos",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilos visuales adaptados a móviles
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { font-size: 24px !important; font-weight: 700; text-align: center; color: #1E3A8A; margin-bottom: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1E3A8A; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Control de Roturas de Stock")
st.write("Versión optimizada: Formato ordenado iniciando por el **Código de Barras (EAN)**.")

st.subheader("📁 1. Cargar Archivos")
file_folleto = st.file_uploader("Sube el Fichero del Folleto (SMS CON FOTO...)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Sube el Fichero de Stock (010...)", type=["xlsx", "csv"], key="stock")

if file_folleto and file_stock:
    try:
        # Leer archivos soportando CSV y Excel
        df_folleto = pd.read_excel(file_folleto) if file_folleto.name.endswith('.xlsx') else pd.read_csv(file_folleto)
        df_stock = pd.read_excel(file_stock) if file_stock.name.endswith('.xlsx') else pd.read_csv(file_stock)

        # Limpiar espacios en los encabezados
        df_folleto.columns = df_folleto.columns.str.strip()
        df_stock.columns = df_stock.columns.str.strip()

        st.success("¡Ficheros cargados con éxito!")

        # Cruzar usando la columna común 'ID'
        if 'ID' in df_folleto.columns and 'ID' in df_stock.columns:
            
            # Forzar el mismo formato en los IDs para que coincidan perfectamente
            df_folleto['ID'] = df_folleto['ID'].astype(str).str.strip()
            df_stock['ID'] = df_stock['ID'].astype(str).str.strip()
            
            # Seleccionamos las columnas clave del archivo de stock (ID, EAN y Stock Disponible)
            col_stock_disp = 'Stock Disp' if 'Stock Disp' in df_stock.columns else df_stock.columns[-1]
            col_ean = 'EAN' if 'EAN' in df_stock.columns else df_stock.columns[0]
            
            df_stock_clean = df_stock[['ID', col_ean, col_stock_disp]].copy()
            df_stock_clean.columns = ['ID', 'Código de Barras (EAN)', 'Stock Disponible']
            
            # Cruzar datos (Traer el EAN y el Stock al folleto)
            df_analisis = pd.merge(df_folleto, df_stock_clean, on='ID', how='left')
            df_analisis['Stock Disponible'] = df_analisis['Stock Disponible'].fillna(0)
            df_analisis['Código de Barras (EAN)'] = df_analisis['Código de Barras (EAN)'].fillna('No encontrado').astype(str)

            # Detectar roturas (Stock menor o igual a 0)
            df_roturas = df_analisis[df_analisis['Stock Disponible'] <= 0].copy()

            # --- REORGANIZAR COLUMNAS PARA EMPEZAR POR EL CÓDIGO DE BARRAS ---
            # Ponemos 'Código de Barras (EAN)' al principio de todo
            columnas_ordenadas = ['Código de Barras (EAN)', 'ID']
            
            # Añadir el resto de columnas del folleto originales automáticamente
            for col in df_folleto.columns:
                if col != 'ID' and col in df_analisis.columns:
                    columnas_ordenadas.append(col)
            
            # Añadir la columna del stock al final
            columnas_ordenadas.append('Stock Disponible')
            
            # Aplicamos el nuevo formato ordenado
            df_roturas_formateado = df_roturas[columnas_ordenadas]

            # --- PRESENTACIÓN DE RESULTADOS ---
            st.subheader("📊 2. Resumen de Alertas")
            c1, c2 = st.columns(2)
            c1.metric("Artículos analizados", len(df_folleto))
            c2.metric("Roturas Detectadas 🚨", len(df_roturas), delta_color="inverse")

            st.subheader("📋 3. Listado de Productos Agotados")
            if not df_roturas_formateado.empty:
                # Mostrar tabla optimizada en pantalla
                st.dataframe(df_roturas_formateado, use_container_width=True, hide_index=True)
                
                # Generar el archivo final formateado para descarga (Funciona directo en iPhone y PC)
                csv = df_roturas_formateado.to_csv(index=False, sep=';').encode('utf-8-sig')
                st.download_button(
                    label="📥 Descargar Fichero de Roturas (EAN Primero)",
                    data=csv,
                    file_name="roturas_codigo_barras_primero.csv",
                    mime="text/csv",
                )
            else:
                st.success("✅ ¡Todo excelente! Todos los artículos del folleto tienen existencias disponibles.")
        else:
            st.error("❌ Error: No se encontró la columna 'ID' en alguno de los archivos para poder vincularlos.")
            
    except Exception as e:
        st.error(f"Error procesando el formato de los ficheros: {e}")
else:
    st.info("💡 Sube tus dos archivos modificados para generar de inmediato el fichero con el Código de Barras en la primera columna.")
