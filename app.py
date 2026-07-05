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
    /* Fondo general suave y márgenes optimizados */
    .main .block-container { 
        padding-top: 2.5rem; 
        padding-bottom: 3.5rem; 
        max-width: 800px;
    }
    
    /* Encabezados y títulos principales */
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
    
    /* Texto aclaratorio bajo el título */
    .subtitle-app {
        text-align: center;
        color: #6B7280;
        font-size: 14px;
        margin-bottom: 35px;
    }
    
    /* Contenedores estilizados para subida de archivos */
    .stFileUploader {
        padding: 20px;
        background-color: #F9FAFB;
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    /* Botones principales con degradados premium y microanimaciones */
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
    
    /* Tarjetas de métricas unificadas */
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
df_folleto = None
df_stock = None

if file_folleto and file_stock:
    ejecutar_procesado = True

if not ejecutar_procesado:
    st.info("💡 Sube ambos documentos para realizar la consolidación y aplicar las reglas de stock crítico.")

# --- NÚCLEO DE PROCESAMIENTO PLANO ---
if ejecutar_procesado:
    try:
        # Lectura de ficheros tolerante a formatos comunes
        if file_folleto.name.endswith('.xlsx'):
            df_folleto = pd.read_excel(file_folleto)
        else:
            df_folleto = pd.read_csv(file_folleto)
            
        if file_stock.name.endswith('.xlsx'):
            df_stock = pd.read_excel(file_stock)
        else:
            df_stock = pd.read_csv(file_stock)

        # Normalizador de cadenas para nombres de columnas
        mapeo_folleto = {}
        for col in df_folleto.columns:
            col_l = str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' ')
            mapeo_folleto[col_l] = col

        mapeo_stock = {}
        for col in df_stock.columns:
            col_l = str(col).strip().lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('/', ' ')
            mapeo_stock[col_l] = col

        # Identificación automática de columnas críticas
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

        # Verificación estructural sin dependencias de identación profundas
        columnas_validas = False
        if col_id_folleto and col_id_stock and col_ean and col_desc and col_pvp and col_stock:
            columnas_validas = True

        if not columnas_validas:
            st.error("❌ Error de mapeo: No se han localizado las columnas indispensables (ID, EAN, Descripción Artículo, PVP normal o Stock Disp).")

        if columnas_validas:
            # Homogeneización de los códigos ID eliminando decimales espurios
            df_folleto['ID_limpio'] = df_folleto[col_id_folleto].astype(str).str.strip().str.split('.').str[0]
            df_stock['ID_limpio'] = df_stock[col_id_stock].astype(str).str.strip().str.split('.').str[0]

            # Recopilación selectiva de campos presentes del stock
            columnas_a_extraer = ['ID_limpio', col_id_stock, col_ean, col_desc, col_pvp, col_stock]
            if col_pcb: columnas_a_extraer.append(col_pcb)
            if col_fap: columnas_a_extraer.append(col_fap)
            if col_ubi: columnas_a_extraer.append(col_ubi)

            df_stock_limpio = df_stock[columnas_a_extraer].copy()

            # Cruce de datos relacional (Inner Join)
            df_cruce = pd.merge(df_folleto[['ID_limpio']], df_stock_limpio, on='ID_limpio', how='inner')
            
            if col_promo:
                df_folleto_promo = df_folleto[['ID_limpio', col_promo]].drop_duplicates(subset=['ID_limpio'])
                df_cruce = pd.merge(df_cruce, df_folleto_promo, on='ID_limpio', how='left')

            df_cruce = df_cruce.drop_duplicates(subset=['ID_limpio'])

            # Filtrado matemático estricto: Stock Disponible <= 2
            df_cruce['Stock_Numerico'] = pd.to_numeric(df_cruce[col_stock], errors='coerce').fillna(0)
            df_roturas = df_cruce[df_cruce['Stock_Numerico'] <= 2].copy()

            # Limpieza de tipos finales para presentación clara
            df_roturas['EAN_Limpiado'] = pd.to_numeric(df_roturas[col_ean], errors='coerce').fillna(0).astype(int).astype(str).str.strip()
            df_roturas['ID_Final'] = df_roturas['ID_limpio'].astype(str)

            df_roturas['PCB_val'] = df_roturas[col_pcb].fillna('-').astype(str).str.split('.').str[0] if col_pcb else '-'
            df_roturas['FAP_val'] = df_roturas[col_fap].fillna('-').astype(str) if col_fap else '-'
            df_roturas['UBI_val'] = df_roturas[col_ubi].fillna('-').astype(str) if col_ubi else '-'
            df_roturas['PROMO_val'] = df_roturas[col_promo].fillna('-').astype(str) if col_promo else '-'

            # DataFrame refinado para cuadrícula en entorno web
            df_formato_pantalla = pd.DataFrame({
                'EAN': df_roturas['EAN_Limpiado'],
                'ID': df_roturas['ID_Final'],
                'Descripción Artículo': df_roturas[col_desc],
                'PVP': df_roturas[col_pvp],
                'Stock Disp.': df_roturas['Stock_Numerico'].astype(int)
            })

            # --- SECCIÓN: VISUALIZACIÓN DE CUADRO DE MANDOS ---
            st.markdown("### 📊 2. Indicadores de Estado")
            c1, c2 = st.columns(2)
            
            with c1:
                st.metric(label="Artículos Cruzados en Folleto", value=f"{len(df_folleto['ID_limpio'].unique())} uds")
            with c2:
                color_delta = "inverse" if len(df_formato_pantalla) > 0 else "normal"
                st.metric(label="Líneas con Rotura de Stock 🚨", value=f"{len(df_formato_pantalla)} uds", delta_color=color_delta)

            st.markdown("### 📋 3. Lista de Control de Incidencias")
            
            tiene_alertas = len(df_formato_pantalla) > 0

            if not tiene_alertas:
                st.success("✨ ¡Todo correcto! Todos los productos del folleto disponen de niveles estables de stock.")

            if tiene_alertas:
                # Cuadrícula interactiva profesional con columnas expandidas automáticamente
                st.dataframe(
                    df_formato_pantalla, 
                    use_container_width=True, 
                    hide_index=True
                )
                
                st.markdown("### 🛠— 4. Herramientas de Exportación")
                
                # Re-estructuración para la descarga limpia del CSV listo para Excel
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
                
                # Se introduce utf-8-sig para que Excel reconozca eñes y tildes del CSV automáticamente
                csv_data = df_excel_completo.to_csv(index=False, sep=';', encoding='utf-8-sig')
                
                st.download_button(
                    label="DESCARGA EL FICHERO ROTURAS DE FOLLETO",
                    data=csv_data,
                    file_name="roturas_folleto_tienda.csv",
                    mime="text/csv"
                )
                
                st.write("") 

                # Documento de impresión optimizado continuo pieza por pieza sin usar f-strings complejos
                html_parts = []
                html_parts.append('<!DOCTYPE html><html><head><meta charset="utf-8">')
                html_parts.append('<title>Informe de Roturas</title>')
                html_parts.append('<link href="https://fonts.googleapis.com/css2?family=Libre+Barcode+128&display=swap" rel="stylesheet">')
                html_parts.append('<style>')
                html_parts.append("body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 15px; color: #1F2937; } ")
                html_parts.append(".header-container { text-align: center; margin-bottom: 20px; border-bottom: 4px solid #1E3A8A; padding-bottom: 12px; } ")
                html_parts.append("h2 { color: #1E3A8A; margin: 0; font-size: 22px; font-weight: 800; text-transform: uppercase; letter-spacing: -0.5px; } ")
                html_parts.append("p.sub { font-size: 13px; color: #4B5563; margin: 6px 0 0 0; font-weight: 500; } ")
                html_parts.append("table { width: 100%; border-collapse: collapse; margin-top: 15px; } ")
                html_parts.append("th { background-color: #1E3A8A; color: white; padding: 10px 6px; text-align: left; font-size: 11px; text-transform: uppercase; font-weight: 700; } ")
                html_parts.append("td { padding: 8px 6px; border-bottom: 1px solid #E5E7EB; font-size: 11px; vertical-align: middle; } ")
                html_parts.append("tr:nth-child(even) { background-color: #F9FAFB; } ")
                html_parts.append(".barcode-cell { font-family: 'Libre Barcode 128', sans-serif; font-size: 46px; padding: 0px 4px; line-height: 1; white-space: nowrap; }")
                html_parts.append('</style></head><body>')
                html_parts.append('<div class="header-container"><h2>📋 LISTADO DE ROTURAS DE STOCK - FOLLETO</h2>')
                html_parts.append('<p class="sub">Generado automáticamente. Total artículos agotados: <b>' + str(len(df_roturas)) + '</b></p></div>')
                html_parts.append('<table><thead><tr>')
                html_parts.append('<th style="width: 18%;">CÓDIGO BARRAS (PANCHAR)</th><th>EAN</th><th>ID</th><th>DESCRIPCIÓN ARTÍCULO</th>')
                html_parts.append('<th style="text-align: right;">PVP NORMAL</th><th style="text-align: center;">STOCK DISP</th>')
                html_parts.append('<th style="text-align: center;">UDS/CAJA</th><th style="text-align: center;">FAP</th><th>UBICACIÓN</th><th>PROMOCIÓN</th>')
                html_parts.append('</tr></thead><tbody>')

                for idx, fila in df_roturas.iterrows():
                    html_parts.append('<tr>')
                    html_parts.append('<td class="barcode-cell">' + str(fila['EAN_Limpiado']) + '</td>')
                    html_parts.append('<td>' + str(fila['EAN_Limpiado']) + '</td>')
                    html_parts.append('<td>' + str(fila['ID_Final']) + '</td>')
                    html_parts.append('<td>' + str(fila[col_desc]) + '</td>')
                    html_parts.append('<td style="text-align: right; font-weight: 600;">' + str(fila[col_pvp]) + '</td>')
                    
                    # Estilización condicional en rojo suave para destacar la rotura
                    stk_val = int(fila['Stock_Numerico'])
                    html_parts.append('<td style="text-align: center; font-weight: bold; color: #DC2626; background-color: #FEF2F2;">' + str(stk_val) + '</td>')
                    
                    html_parts.append('<td style="text-align: center; font-weight: 600; color: #1E3A8A;">' + str(fila['PCB_val']) + '</td>')
                    html_parts.append('<td style="text-align: center;">' + str(fila['FAP_val']) + '</td>')
                    html_parts.append('<td>' + str(fila['UBI_val']) + '</td>')
                    html_parts.append('<td style="font-size: 11px; color: #2563EB; font-weight: 600;">' + str(fila['PROMO_val']) + '</td>')
                    html_parts.append('</tr>')

                html_parts.append('</tbody></table>')
                html_parts.append('<script>window.onload = function() { setTimeout(function() { window.print(); }, 300); };</script>')
                html_parts.append('</body></html>')

                # Unificación de las piezas y conversión segura a base64 preservando caracteres UTF-8 nativos
                html_impresion = "".join(html_parts)
                html_b64 = base64.b64encode(html_impresion.encode('utf-8')).decode('utf-8')

                # Renderización del botón. Se aplica atob con un wrapper de decodeURIComponent para sanitizar acentos
                st.components.v1.html(f"""
                    <html>
                    <body>
                        <button onclick="abrirInforme()" style="display: block; width: 100%; background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; text-align: center; padding: 14px; font-size: 15px; font-weight: bold; border-radius: 12px; font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif; border: none; cursor: pointer; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2); transition: all 0.2s ease;">
                           🖨️ GENERAR VISTA DE IMPRESIÓN (CON CÓDIGOS DE BARRAS)
                        </button>
                        <script>
                            function abrirInforme() {{
                                var ventana = window.open('', '_blank');
                                var base64data = "{html_b64}";
                                // Decodificación robusta para forzar al navegador a interpretar UTF-8 correcto
                                var strData = atob(base64data);
                                var bytes = new Uint8Array(strData.length);
                                for (var i = 0; i < strData.length; i++) {{
                                    bytes[i] = strData.charCodeAt(i);
                                }}
                                var decoder = new TextDecoder('utf-8');
                                var htmlFinal = decoder.decode(bytes);
                                
                                ventana.document.write(htmlFinal);
                                ventana.document.close();
                            }}
                        </script>
                    </body>
                    </html>
                """, height=65)

    except Exception as e:
        st.error(f"Error técnico durante el procesado: {e}")
