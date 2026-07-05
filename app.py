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
st.write("Sube los archivos para extraer el listado formateado listo para revisión e impresión.")

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
            
            # --- SOLUCIÓN DEFINITIVA AL CRUCE DE IDs DECIMALES ---
            # Forzamos la conversión a números flotantes limpios para que 766420.0 y 766420 sean tratados de forma idéntica matemáticamente
            df_folleto['ID_match'] = pd.to_numeric(df_folleto['ID'], errors='coerce')
            df_stock['ID_match'] = pd.to_numeric(df_stock['ID'], errors='coerce')

            # Eliminar filas donde el ID no sea un número válido
            df_folleto = df_folleto.dropna(subset=['ID_match'])
            df_stock = df_stock.dropna(subset=['ID_match'])

            # Columnas requeridas del archivo 010
            columnas_stock_necesarias = ['ID_match', 'ID', 'EAN', 'Descripción Artículo', 'PVP normal', 'Stock Disp']
            
            # Verificar que existan en el archivo de stock original (menos ID_match que la creamos nosotros)
            missing_cols = [col for col in ['ID', 'EAN', 'Descripción Artículo', 'PVP normal', 'Stock Disp'] if col not in df_stock.columns]
            
            if not missing_cols:
                # --- TRATAMIENTO DE STOCK ---
                # Convertimos 'Stock Disp' a número. Si está vacío (NaN), cuenta como 0 rotura.
                df_stock['Stock Disp'] = pd.to_numeric(df_stock['Stock Disp'], errors='coerce').fillna(0)

                # Cruzar los archivos usando el ID matemático limpio
                df_cruce = pd.merge(df_folleto[['ID_match']], df_stock[columnas_stock_necesarias], on='ID_match', how='inner')
                
                # Eliminar duplicados si un artículo viene repetido
                df_cruce = df_cruce.drop_duplicates(subset=['ID_match'])

                # --- FILTRO REAL DE ROTURAS (Stock Disp <= 0) ---
                df_roturas = df_cruce[df_cruce['Stock Disp'] <= 0].copy()

                # Limpieza estricta y visual del EAN y del ID original para la pantalla
                df_roturas['EAN'] = pd.to_numeric(df_roturas['EAN'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
                df_roturas['ID'] = pd.to_numeric(df_roturas['ID'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()

                # Reordenar las columnas al formato exacto de 5 columnas solicitado
                df_formato_solicitado = df_roturas[['EAN', 'ID', 'Descripción Artículo', 'PVP normal', 'Stock Disp']]

                # --- MOSTRAR RESULTADOS ---
                st.subheader("📊 2. Resumen de Alertas")
                c1, c2 = st.columns(2)
                c1.metric("Artículos en Folleto", len(df_folleto['ID_match'].unique()))
                c2.metric("Roturas de Folleto 🚨", len(df_formato_solicitado), delta_color="inverse")

                st.subheader("📋 3. Vista Previa del Fichero de Roturas")
                
                if len(df_formato_solicitado) > 0:
                    # Mostrar la tabla limpia en pantalla de forma nativa
                    st.dataframe(df_formato_solicitado, use_container_width=True, hide_index=True)
                    
                    # --- BOTONES DE ACCIÓN ---
                    st.subheader("🛠️ 4. Acciones")
                    col_btn1, col_btn2 = st.columns(2)
                    
                    # 1. Botón para Descargar CSV (con formato texto para Excel)
                    with col_btn1:
                        df_descarga = df_formato_solicitado.copy()
                        df_descarga['EAN'] = df_descarga['EAN'].apply(lambda x: f"'\t{x}")
                        csv_data = df_descarga.to_csv(index=False, sep=';', encoding='utf-8-sig')
                        st.download_button(
                            label="📥 Descargar para Excel",
                            data=csv_data,
                            file_name="roturas_folleto_formato_final.csv",
                            mime="text/csv",
                        )
                    
                    # 2. Botón para Imprimir / Guardar en PDF
                    with col_btn2:
                        # Creamos una estructura HTML simple para mandarla al menú de impresión nativo
                        html_table = df_formato_solicitado.to_html(index=False, classes='table')
                        print_html = f"""
                        <html>
                        <head>
                        <meta charset="utf-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                            h2 {{ text-align: center; color: #1E3A8A; }}
                            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                            th {{ background-color: #1E3A8A; color: white; padding: 10px; text-align: left; font-size: 14px; }}
                            td {{ padding: 10px; border-bottom: 1px solid #ddd; font-size: 13px; }}
                            tr:nth-child(even) {{ background-color: #f9f9f9; }}
                        </style>
                        </head>
                        <body>
                            <h2>📋 INFORME DE ROTURAS DE STOCK - FOLLETO ACTIVADO</h2>
                            <p><strong>Total Roturas Detectadas:</strong> {len(df_formato_solicitado)} artículos</p>
                            {html_table}
                            <script>
                                function abrirImpresion() {{
                                    var vent = window.open('', '_blank');
                                    vent.document.write({repr(html_table)});
                                    vent.document.write('<style>body{{font-family:Arial;margin:30px}}h2{{color:#1E3A8A;text-align:center}}table{{width:100%;border-collapse:collapse}}th{{background:#1E3A8A;color:white;padding:10px;text-align:left}}td{{padding:10px;border-bottom:1px solid #ddd}}tr:nth-child(even){{background:#f9f9f9}}</style>');
                                    vent.document.write('<h2>📋 INFORME DE ROTURAS DE STOCK</h2>');
                                    vent.document.write(document.getElementsByTagName('table')[0].outerHTML);
                                    vent.document.close();
                                    vent.print();
                                }}
                            </script>
                        </body>
                        </html>
                        """
                        
                        # Generación del script embebido seguro de Streamlit para llamar a la ventana de impresión
                        if st.button("🖨️ Imprimir / Informe PDF"):
                            st.components.v1.html(f"""
                                <script>
                                    var docHtml = `
                                    <html>
                                    <head>
                                        <title>Informe de Roturas</title>
                                        <style>
                                            body {{ font-family: Arial, sans-serif; padding: 20px; }}
                                            h2 {{ color: #1E3A8A; text-align: center; margin-bottom: 5px; }}
                                            p {{ font-size: 14px; margin-bottom: 20px; color: #555; }}
                                            table {{ width: 100%; border-collapse: collapse; }}
                                            th {{ background: #1E3A8A; color: white; padding: 10px; text-align: left; font-size: 13px; }}
                                            td {{ padding: 10px; border-bottom: 1px solid #ddd; font-size: 12px; }}
                                            tr:nth-child(even) {{ background: #f9f9f9; }}
                                        </style>
                                    </head>
                                    <body>
                                        <h2>📋 LISTADO DE ROTURAS DE STOCK - FOLLETO</h2>
                                        <p>Generado automáticamente. Total artículos agotados: {len(df_formato_solicitado)}</p>
                                        {html_table}
                                    </body>
                                    </html>
                                    `;
                                    var ventana = window.open('', '_blank');
                                    ventana.document.write(docHtml);
                                    ventana.document.close();
                                    ventana.focus();
                                    setTimeout(function() {{ ventana.print(); }}, 500);
                                </script>
                            """, height=0, width=0)
                            
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
