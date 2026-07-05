import streamlit as st
import pandas as pd
import base64

# 1. CONFIGURACIÓN E INTERFAZ VISUAL (Adaptada para PC y Móvil)
st.set_page_config(
    page_title="INFORME COMPLETADO DE ROTURAS",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1 { font-size: 24px !important; font-weight: 700; text-align: center; color: #1E3A8A; margin-bottom: 15px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1E3A8A; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 FICHERO ROTURAS DE FOLLETO")
st.write("Sube los archivos para extraer el listado formateado listo para revisión e impresión con códigos escaneables.")

st.subheader("📁 1. Cargar Archivos")
file_folleto = st.file_uploader("Sube el Fichero del Folleto (SMS CON FOTO...)", type=["xlsx", "csv"], key="folleto")
file_stock = st.file_uploader("Sube el Fichero de Stock (010...)", type=["xlsx", "csv"], key="stock")

# Inicialización segura de variables globales para evitar errores de referencia
ejecutar_procesado = False
df_folleto = None
df_stock = None

# Verificación inicial plana de archivos
if file_folleto and file_stock:
    ejecutar_procesado = True

# Si falta algún archivo, mostramos el aviso informativo de forma limpia
if not ejecutar_procesado:
    st.info("💡 Sube ambos ficheros para generar automáticamente el documento con la estructura solicitada.")

# --- BLOQUE DE PROCESADO PRINCIPAL BLINDADO ---
if ejecutar_procesado:
    try:
        # Lectura segura de formatos Excel o CSV
        if file_folleto.name.endswith('.xlsx'):
            df_folleto = pd.read_excel(file_folleto)
        else:
            df_folleto = pd.read_csv(file_folleto)
            
        if file_stock.name.endswith('.xlsx'):
            df_stock = pd.read_excel(file_stock)
        else:
            df_stock = pd.read_csv(file_stock)

        # Normalizador estricto de columnas para evitar fallos de mayúsculas/acentos
        mapeo_folleto = {}
        for col in df_folleto.columns:
            col_l = str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' ')
            mapeo_folleto[col_l] = col

        mapeo_stock = {}
        for col in df_stock.columns:
            col_l = str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' ')
            mapeo_stock[col_l] = col

        # Mapeo de columnas requeridas
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

        # Validación estructural estricta de columnas obligatorias
        columnas_validas = False
        if col_id_folleto and col_id_stock and col_ean and col_desc and col_pvp and col_stock:
            columnas_validas = True

        if not columnas_validas:
            st.error("❌ Error: No se encontraron las columnas obligatorias necesarias (ID, EAN, Descripción, PVP normal o Stock Disp) en los ficheros.")

        if columnas_validas:
            st.success("¡Ficheros cargados con éxito!")

            # Limpieza homogénea de IDs de texto
            df_folleto['ID_limpio'] = df_folleto[col_id_folleto].astype(str).str.strip().str.split('.').str[0]
            df_stock['ID_limpio'] = df_stock[col_id_stock].astype(str).str.strip().str.split('.').str[0]

            # Recompilación de datos requeridos de stock
            columnas_a_extraer = ['ID_limpio', col_id_stock, col_ean, col_desc, col_pvp, col_stock]
            if col_pcb: columnas_a_extraer.append(col_pcb)
            if col_fap: columnas_a_extraer.append(col_fap)
            if col_ubi: columnas_a_extraer.append(col_ubi)

            df_stock_limpio = df_stock[columnas_a_extraer].copy()

            # Cruce inteligente (Inner Join) entre Folleto y Stock
            df_cruce = pd.merge(df_folleto[['ID_limpio']], df_stock_limpio, on='ID_limpio', how='inner')
            
            if col_promo:
                df_folleto_promo = df_folleto[['ID_limpio', col_promo]].drop_duplicates(subset=['ID_limpio'])
                df_cruce = pd.merge(df_cruce, df_folleto_promo, on='ID_limpio', how='left')

            df_cruce = df_cruce.drop_duplicates(subset=['ID_limpio'])

            # Filtrado matemático: Stock Disp <= 2
            df_cruce['Stock_Numerico'] = pd.to_numeric(df_cruce[col_stock], errors='coerce').fillna(0)
            df_roturas = df_cruce[df_cruce['Stock_Numerico'] <= 2].copy()

            # Homogeneización de campos finales
            df_roturas['EAN_Limpiado'] = pd.to_numeric(df_roturas[col_ean], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
            df_roturas['ID_Final'] = df_roturas['ID_limpio'].astype(str)

            df_roturas['PCB_val'] = df_roturas[col_pcb].fillna('-').astype(str).str.split('.').str[0] if col_pcb else '-'
            df_roturas['FAP_val'] = df_roturas[col_fap].fillna('-').astype(str) if col_fap else '-'
            df_roturas['UBI_val'] = df_roturas[col_ubi].fillna('-').astype(str) if col_ubi else '-'
            df_roturas['PROMO_val'] = df_roturas[col_promo].fillna('-').astype(str) if col_promo else '-'

            # DataFrame simplificado para el visor web en iPhone/PC
            df_formato_pantalla = pd.DataFrame({
                'EAN': df_roturas['EAN_Limpiado'],
                'ID': df_roturas['ID_Final'],
                'Descripción Artículo': df_roturas[col_desc],
                'PVP normal': df_roturas[col_pvp],
                'Stock Disp': df_roturas['Stock_Numerico']
            })

            # --- MOSTRAR RESULTADOS REVISADOS ---
            st.subheader("📊 2. Resumen de Alertas")
            c1, c2 = st.columns(2)
            c1.metric("Artículos en Folleto", len(df_folleto['ID_limpio'].unique()))
            c2.metric("Roturas de Folleto 🚨", len(df_formato_pantalla), delta_color="inverse")

            st.subheader("📋 3. Vista Previa del Fichero de Roturas")
            
            # Verificación del volumen de alertas mediante variables de conteo plano
            tiene_alertas = len(df_formato_pantalla) > 0

            if not tiene_alertas:
                st.success("✅ ¡Todo en orden! Ningún artículo del folleto tiene un Stock Disponible crítico.")

            if tiene_alertas:
                st.dataframe(df_formato_pantalla, use_container_width=True, hide_index=True)
                st.subheader("🛠️ 4. Acciones e Impresión")
                
                # Generación plana del archivo Excel/CSV (Formato estricto solicitado)
                df_excel_completo = pd.DataFrame()
                df_excel_completo['CÓDIGO BARRAS (PANCHAR)'] = df_roturas['EAN_Limpiado'].apply(lambda x: f"'\t{x}")
                df_excel_completo['EAN'] = df_roturas['EAN_Limpiado'].apply(lambda x: f"'\t{x}")
                df_excel_completo['ID'] = df_roturas['ID_Final']
                df_excel_completo['DESCRIPCIÓN ARTÍCULO'] = df_roturas[col_desc]
                df_excel_completo['PVP'] = df_roturas[col_pvp]
                df_excel_completo['STOCK'] = df_roturas['Stock_Numerico'].astype(int)
                df_excel_completo['UDS/CAJA'] = df_roturas['PCB_val']
                df_excel_completo['FAP'] = df_roturas['FAP_val']
                df_excel_completo['UBICACIÓN'] = df_roturas['UBI_val']
                df_excel_completo['PROMOCIÓN'] = df_roturas['PROMO_val']
                
                csv_data = df_excel_completo.to_csv(index=False, sep=';', encoding='utf-8-sig')
                
                st.download_button(
                    label="📥 Descargar Fichero Completo para Excel",
                    data=csv_data,
                    file_name="roturas_folleto_formato_final.csv",
                    mime="text/csv"
                )
                
                st.write("") 

                # Construcción segura del HTML de impresión por piezas individuales continuas
                html_parts = []
                html_parts.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
                html_parts.append('<title>INFORME COMPLETADO DE ROTURAS</title>')
                html_parts.append('<link href="https://fonts.googleapis.com/css2?family=Libre+Barcode+128&display=swap" rel="stylesheet">')
                html_parts.append('<style>')
                html_parts.append("body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 10px; color: #333; } ")
                html_parts.append(".header-container { text-align: center; margin-bottom: 25px; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; } ")
                html_parts.append("h2 { color: #1E3A8A; margin: 0; font-size: 20px; text-transform: uppercase; } ")
                html_parts.append("p.sub { font-size: 14px; color: #666; margin: 5px 0 0 0; } ")
                html_parts.append("table { width: 100%; border-collapse: collapse; margin-top: 10px; } ")
                html_parts.append("th { background-color: #1E3A8A; color: white; padding: 10px 4px; text-align: left; font-size: 11px; text-transform: uppercase; } ")
                html_parts.append("td { padding: 8px 4px; border-bottom: 1px solid #E5E7EB; font-size: 11px; vertical-align: middle; } ")
                html_parts.append("tr:nth-child(even) { background-color: #F9FAFB; } ")
                html_parts.append(".barcode-cell { font-family: 'Libre Barcode 128', sans-serif; font-size: 44px; padding: 0px 4px; line-height: 1; letter-spacing: 0px; white-space: nowrap; }")
                html_parts.append('</style></head><body>')
                html_parts.append('<div class="header-container"><h2>📋 FICHERO ROTURAS DE FOLLETO</h2>')
                html_parts.append('<p class="sub">Total alertas detectadas para revisión: <b>' + str(len(df_roturas)) + '</b></p></div>')
                html_parts.append('<table><thead><tr>')
                html_parts.append('<th style="width: 18%;">CÓDIGO BARRAS (PANCHAR)</th><th>EAN</th><th>ID</th><th>DESCRIPCIÓN ARTÍCULO</th>')
                html_parts.append('<th style="text-align: right;">PVP</th><th style="text-align: center;">STOCK</th>')
                html_parts.append('<th style="text-align: center;">UDS/CAJA</th><th style="text-align: center;">FAP</th><th>UBICACIÓN</th><th>PROMOCIÓN</th>')
                html_parts.append('</tr></thead><tbody>')

                for idx, fila in df_roturas.iterrows():
                    html_parts.append('<tr>')
                    html_parts.append('<td class="barcode-cell">' + str(fila['EAN_Limpiado']) + '</td>')
                    html_parts.append('<td>' + str(fila['EAN_Limpiado']) + '</td>')
                    html_parts.append('<td>' + str(fila['ID_Final']) + '</td>')
                    html_parts.append('<td>' + str(fila[col_desc]) + '</td>')
                    html_parts.append('<td style="text-align: right;">' + str(fila[col_pvp]) + '</td>')
                    html_parts.append('<td style="text-align: center; font-weight: bold; color: #DC2626;">' + str(int(fila['Stock_Numerico'])) + '</td>')
                    html_parts.append('<td style="text-align: center; font-weight: bold; color: #1E3A8A;">' + str(fila['PCB_val']) + '</td>')
                    html_parts.append('<td style="text-align: center;">' + str(fila['FAP_val']) + '</td>')
                    html_parts.append('<td>' + str(fila['UBI_val']) + '</td>')
                    html_parts.append('<td style="font-size: 11px; color: #1E3A8A;">' + str(fila['PROMO_val']) + '</td>')
                    html_parts.append('</tr>')

                html_parts.append('</tbody></table>')
                html_parts.append('<script>window.onload = function() { setTimeout(function() { window.print(); }, 500); };</script>')
                html_parts.append('</body></html>')

                html_impresion = "".join(html_parts)
                html_b64 = base64.b64encode(html_impresion.encode('utf-8')).decode('utf-8')

                st.components.v1.html(f"""
                    <html>
                    <body>
                        <button onclick="abrirInforme()" style="display: block; width: 100%; background-color: #1E3A8A; color: white; text-align: center; padding: 14px; font-size: 16px; font-weight: bold; border-radius: 10px; font-family: Arial, sans-serif; border: none; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                           🖨️ IMPRIMIR / VER INFORME COMPLETO CON CÓDIGOS DE BARRAS
                        </button>
                        <script>
                            function abrirInforme() {{
                                var ventana = window.open('', '_blank');
                                var contenido = atob("{html_b64}");
                                ventana.document.write(contenido);
                                ventana.document.close();
                            }}
                        </script>
                    </body>
                    </html>
                """, height=65)

    except Exception as e:
        st.error(f"Ocurrió un error en el procesado técnico: {e}")
