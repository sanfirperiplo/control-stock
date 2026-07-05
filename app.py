st.markdown("### 🛠— 4. Herramientas de Exportación")
                
                # Re-estructuración para la descarga limpia del CSV
                df_excel_completo = pd.DataFrame()
                
                # Forzamos formato de texto añadiendo una tabulación al principio para evitar que Excel corrompa los códigos
                df_excel_completo['CÓDIGO BARRAS (PANCHAR)'] = df_roturas['EAN_Limpiado'].apply(lambda x: f"=\"{x}\"")
                df_excel_completo['EAN'] = df_roturas['EAN_Limpiado'].apply(lambda x: f"=\"{x}\"")
                df_excel_completo['ID'] = df_roturas['ID_Final'].apply(lambda x: f"=\"{x}\"")
                
                df_excel_completo['DESCRIPCIÓN ARTÍCULO'] = df_roturas[col_desc]
                df_excel_completo['PVP'] = df_roturas[col_pvp]
                df_excel_completo['STOCK'] = df_roturas['Stock_Numerico'].astype(int)
                df_excel_completo['UDS/CAJA'] = df_roturas['PCB_val']
                df_excel_completo['FAP'] = df_roturas['FAP_val']
                df_excel_completo['UBICACIÓN'] = df_roturas['UBI_val']
                df_excel_completo['PROMOCIÓN'] = df_roturas['PROMO_val']
                
                # Utilizamos 'utf-8-sig' que es la mejor opción para Excel en Windows
                csv_data = df_excel_completo.to_csv(index=False, sep=';', encoding='utf-8-sig')
                
                st.download_button(
                    label="📥 DESCARGAR DATASET COMPLETO PARA EXCEL (.CSV)",
                    data=csv_data,
                    file_name="roturas_folleto_tienda.csv",
                    mime="text/csv"
                )
