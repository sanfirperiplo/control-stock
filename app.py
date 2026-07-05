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

        # Limpiar espacios en los encabezados de las columnas
        df_folleto.columns = df_folleto.columns.str.strip()
        df_stock.columns = df_stock.columns.str.strip()

        st.success("¡Ficheros cargados con éxito!")

        # Validar que ambos tienen la columna clave 'ID'
        if 'ID' in df_folleto.columns and 'ID' in df_stock.columns:
            
            # --- TRATAMIENTO MATEMÁTICO AVANZADO PARA CORREGIR DECIMALES DE EXCEL (.1, .0) ---
            # Pasamos a número flotante y extraemos la parte entera para que 24.1 o 24.0 sea 24 exactamente
            df_folleto['ID_limpio'] = pd.to_numeric(df_folleto['ID'], errors='coerce').fillna(-1).apply(lambda x: int(float(x)) if float(x) >= 0 else -1)
            df_stock['ID_limpio'] = pd.to_numeric(df_stock['ID'], errors='coerce').fillna(-2).apply(lambda x: int(float(x)) if float(x) >= 0 else -2)

            # Columnas requeridas del archivo 010 original
            columnas_stock_necesarias = ['ID_limpio', 'ID', 'EAN', 'Descripción Artículo', 'PVP normal', 'Stock Disp']
            
            # Verificar que existan en el archivo de stock original
            missing_cols = [col for col in ['ID', 'EAN', 'Descripción Artículo', 'PVP normal', 'Stock Disp'] if col not in df_stock.columns]
            
            if not missing_cols:
                # --- TRATAMIENTO DE STOCK ---
                # Convertimos 'Stock Disp' a número. Si está vacío (NaN), cuenta como 0 rotura.
                df_stock['Stock Disp'] = pd.to_numeric(df_stock['Stock Disp'], errors='coerce').fillna(0)

                # Cruzar los archivos usando el ID entero unificado matemáticamente
                df_cruce = pd.merge(df_folleto[['ID_limpio']], df_stock[columnas_stock_necesarias], on='ID_limpio', how='inner')
                
                # Eliminar duplicados si un artículo viene repetido
                df_cruce = df_cruce.drop_duplicates(subset=['ID_limpio'])

                # --- FILTRO REAL DE ROTURAS (Stock Disp <= 0) ---
                df_roturas = df_cruce[df_cruce['Stock Disp'] <= 0].copy()

                # Limpieza estricta de códigos largos (EAN) para pasarlos a texto plano sin decimales
                df_roturas['EAN'] = pd.to_numeric(df_roturas['EAN'], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
                df_roturas['ID'] = df_roturas['ID_limpio'].astype(str)

                # Reordenar las columnas al formato exacto de 5 columnas solicitado
                df_formato_solicitado = df_roturas[['EAN', 'ID', 'Descripción Artículo', 'PVP normal', 'Stock Disp']]

                # --- MOSTRAR RESULTADOS ---
                st.subheader("📊 2. Resumen de Alertas")
                c1, c2 = st.columns(2)
                c1.metric("Artículos en Folleto", len(df_folleto['ID_limpio'].unique()) - (1 if -1 in df_folleto['ID_limpio'].values else 0))
                c2.metric("Roturas de Folleto 🚨", len(df_formato_solicitado), delta_color="inverse")

                st.subheader("📋 3. Vista Previa del Fichero de Roturas")
                
                if len(df_formato_solicitado) > 0:
                    # Mostrar la tabla limpia en pantalla de forma nativa
                    st.dataframe(df_formato_solicitado, use_container_width=True, hide_index=True)
                    
                    # --- BOTONES DE ACCIÓN E IMPRESIÓN ---
                    st.subheader("🛠️ 4. Acciones e Impresión")
                    
                    # 1. Botón para Descargar CSV (con formato texto para Excel)
                    df_descarga = df_formato_solicitado.copy()
                    df_descarga['EAN'] = df_descarga['EAN'].apply(lambda x: f"'\t{x}")
                    csv_data = df_descarga.to_csv(index=False, sep=';', encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Descargar Fichero para Excel",
                        data=csv_data,
                        file_name="roturas_folleto_formato_final.csv",
                        mime="text/csv",
                    )
                    
                    st.write("") # Espacio visual

                    # 2. SISTEMA DE IMPRESIÓN PREMIUM CON CÓDIGO DE BARRAS A LA IZQUIERDA
                    filas_html = ""
                    for _, fila in df_formato_solicitado.iterrows():
                        filas_html += f"""
                        <tr>
                            <td class="barcode-cell">{fila['EAN']}</td>
                            <td>{fila['EAN']}</td>
                            <td>{fila['ID']}</td>
                            <td>{fila['Descripción Artículo']}</td>
                            <td style="text-align: right;">{fila['PVP normal']}</td>
                            <td style="text-align: center; font-weight: bold; color: #DC2626;">{int(float(fila['Stock Disp']))}</td>
                        </tr>
                        """

                    # Construimos el documento HTML completo que se mandará a la impresora/PDF
                    html_impresion = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Informe de Roturas Escaneable</title>
                        <link href="https://fonts.googleapis.com/css2?family=Libre+Barcode+128&display=swap" rel="stylesheet">
                        <style>
                            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; padding: 10px; color: #333; }}
                            .header-container {{ text-align: center; margin-bottom: 25px; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; }}
                            h2 {{ color: #1E3A8A; margin: 0; font-size: 22px; text-transform: uppercase; }}
                            p.sub {{ font-size: 14px; color: #666; margin: 5px 0 0 0; }}
                            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                            th {{ background-color: #1E3A8A; color: white; padding: 10px 8px; text-align: left; font-size: 12px; text-transform: uppercase; }}
                            td {{ padding: 8px; border-bottom: 1px solid #E5E7EB; font-size: 12px; vertical-align: middle; }}
                            tr:nth-child(even) {{ background-color: #F9FAFB; }}
                            .barcode-cell {{ 
                                font-family: 'Libre Barcode 128', sans-serif; 
                                font-size: 44px; 
                                padding: 0px 8px; 
                                line-height: 1; 
                                letter-spacing: 0px;
                                white-space: nowrap;
                            }}
                            .print-btn {{
                                display: block;
                                width: 100%;
                                background-color: #1E3A8A;
                                color: white;
                                text-align: center;
                                padding: 14px;
                                font-size: 16px;
                                font-weight: bold;
                                border: none;
                                border-radius: 10px;
                                cursor: pointer;
                                text-decoration: none;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                font-family: Arial, sans-serif;
                            }}
                            .print-btn:hover {{ background-color: #1D4ED8; }}
                        </style>
                    </head>
                    <body>
                        <button class="print-btn" onclick="window.print();">CONFIRMAR IMPRESIÓN / GUARDAR EN PDF</button>
                        
                        <div class="header-container" style="margin-top: 25px;">
                            <h2>📋 INFORME DE ROTURAS DE STOCK ESCANEABLE</h2>
                            <p class="sub">Total artículos agotados en folleto: <b>{len(df_formato_solicitado)}</b></p>
                        </div>
                        
                        <table>
                            <thead>
                                <tr>
                                    <th style="width: 25%;">CÓDIGO BARRAS (ESCANEABLE)</th>
                                    <th>EAN</th>
                                    <th>ID</th>
                                    <th>DESCRIPCIÓN ARTÍCULO</th>
                                    <th style="text-align: right;">PVP NORMAL</th>
                                    <th style="text-align: center;">STOCK DISP</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filas_html}
                            </tbody>
                        </table>
                    </body>
                    </html>
                    """

                    # Codificar el HTML de forma segura para incrustar un botón directo que no bloquee ningún móvil
                    import datetime
                    st.components.v1.html(f"""
                        <html>
                        <body>
                            <button onclick="abrirInforme()" style="display: block; width: 100%; background-color: #1E3A8A; color: white; text-align: center; padding: 14px; font-size: 16px; font-weight: bold; border-radius: 10px; font-family: Arial, sans-serif; border: none; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                               🖨️ IMPRIMIR / VER INFORME CON CÓDIGOS DE BARRAS
                            </button>
                            <script>
                                function abrirInforme() {{
                                    var ventana = window.open('', '_blank');
                                    ventana.document.write(document.getElementById('html_code').value);
                                    ventana.document.close();
                                }}
                            </script>
                            <textarea id="html_code" style="display:none;">{html_impresion.replace('</script>', '<\\/script>')}</textarea>
                        </body>
                        </html>
                    """, height=65)

                else:
                    st.success("✅ ¡Todo en orden! Todos los artículos del folleto tienen Stock Disponible en tienda.")
            else:
                st.error(f"❌ El archivo de stock (010) no contiene todas las columnas requeridas. Faltan: {missing_cols}")
        else:
            st.error("❌ Error: No se encontró la columna 'ID' en alguno de los dos archivos para poder cruzarlos.")
            
    except Exception as e:
        st.error(f"Ocurrió un error en el procesado: {e}")
else:
    st.info("💡 Sube ambos ficheros para generar automáticamente el documento con la estructura solicitada.")
