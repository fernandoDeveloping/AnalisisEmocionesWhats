import streamlit as st
from Analisis.Utils.aux_opciones import procesar_chat
from Analisis.Opciones.msgcount_01 import mostrar_analisis_conversacion
from Analisis.Opciones.sentimientos_02 import analizar_emociones
from Analisis.Opciones.analizar_nivel_amistad_03 import analizar_nivel_amistad
from Analisis.Opciones.actividad_04 import analizar_actividad
from Analisis.Opciones.palabras_05 import analizar_palabras_y_emojis
from Disclaimer.privacidad import show_privacy_notice

def main():
    """
    Función principal que dibuja la interfaz de Streamlit.
    """
    
    # --- 1. Configuración de la Página (Debe ser lo primero) ---
    st.set_page_config(
        page_title="Analizador de Chats",
        page_icon="💬",
        layout="wide"
    )

    # --- 2. Inicializar Session State ---
    if 'privacy_accepted' not in st.session_state:
        st.session_state.privacy_accepted = False
    
    if 'df_chat' not in st.session_state:
        st.session_state.df_chat = None
        st.session_state.file_name = None
        st.cache_data.clear()
        st.cache_resource.clear()

    # --- 3. PUERTA DE PRIVACIDAD ---
    if not st.session_state.privacy_accepted:
        show_privacy_notice()
        return 

    # --- 4. Título de Bienvenida ---
    st.title("Bienvenido al Analizador de Sentimientos 💬")
    st.write("Sube tu chat de WhatsApp (.zip o .txt) para descubrir las emociones y compatibilidad en tus conversaciones.")

    # --- 5. Definir Layout (Columnas) ---
    col_controles, col_resultados = st.columns([1, 2]) 

    # --- 6. Columna de Controles (Izquierda) ---
    with col_controles:
        st.header("1. Carga tu Archivo")
        
        # --- Lógica de Carga de Archivo ---
        if st.session_state.df_chat is None:
            uploaded_file = st.file_uploader(
                "Selecciona tu archivo .zip o .txt",
                type=["zip", "txt"],
                help="Exporta tu chat desde WhatsApp (sin multimedia) y súbelo aquí."
            )
            
            if uploaded_file is not None:
                mensajes_eliminados = 0
                with st.spinner("Procesando tu chat... ¡Esto puede tardar un momento!"):
                    
                    # 1. Carga inicial del chat
                    df_inicial = procesar_chat(uploaded_file)
                    
                    # 2. --- NUEVA LIMPIEZA CENTRALIZADA ---
                    # Verificamos que el DataFrame se haya cargado y tenga la columna 'Mensaje'
                    if df_inicial is not None and not df_inicial.empty and 'Mensaje' in df_inicial.columns:
                        total_antes = len(df_inicial)
                        
                        # Definir los filtros. case=False ignora mayúsculas/minúsculas.
                        # na=False asegura que los valores NaN no causen errores
                        filtro_eliminaste = ~df_inicial['Mensaje'].str.contains(
                            "eliminaste este mensaje", case=False, na=False
                        )
                        filtro_se_elimino = ~df_inicial['Mensaje'].str.contains(
                            "se eliminó este mensaje", case=False, na=False
                        )
                        
                        # Aplicar ambos filtros
                        df_limpio = df_inicial[filtro_eliminaste & filtro_se_elimino]
                        
                        total_despues = len(df_limpio)
                        mensajes_eliminados = total_antes - total_despues
                        
                        # Guardar el DataFrame limpio en el estado de la sesión
                        st.session_state.df_chat = df_limpio
                    else:
                        # Si el df está vacío o no tiene 'Mensaje', simplemente guardarlo
                        st.session_state.df_chat = df_inicial
                    # --- FIN DE LA LIMPIEZA ---

                    st.session_state.file_name = uploaded_file.name
                
                st.success("¡Chat procesado con éxito!")
                
                # Informar al usuario sobre la limpieza
                if mensajes_eliminados > 0:
                    st.info(f"Se han omitido **{mensajes_eliminados}** mensajes eliminados del análisis.")
                
                st.rerun() 
        
        else:
            # Estado B: Ya hay un archivo cargado
            st.success(f"Archivo cargado: **{st.session_state.file_name}**")
            st.write("Diez mensajes más recientes:")
            st.dataframe(st.session_state.df_chat[['Autor', 'Mensaje']].tail(10))
            
            if st.button("Cargar otro archivo"):
                st.session_state.df_chat = None
                st.session_state.file_name = None
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()

    # --- 7. Columna de Resultados (Derecha) ---
    with col_resultados:
        st.header("2. Elige un Análisis")
        opciones = [
            "Selecciona una opción...",
            "1. Análisis de Autores",
            "2. Análisis de Emociones",
            "3. Análisis de Nivel de Amistad",
            "4. Análisis de Actividad y Horarios", 
            "5. Palabras y Emojis Más Usados"   
        ]
        
        opcion_elegida = st.selectbox(
            "Elige el tipo de análisis que deseas ver:",
            options=opciones,
            disabled=(st.session_state.df_chat is None) 
        )
        
        st.header("Resultados del Análisis")

        # Mostrar resultados basados en la selección
        if st.session_state.df_chat is not None:
            if opcion_elegida == "1. Análisis de Autores":
                mostrar_analisis_conversacion(st.session_state.df_chat)
                
            elif opcion_elegida == "2. Análisis de Emociones":
                analizar_emociones(st.session_state.df_chat)
                
            elif opcion_elegida == "3. Análisis de Nivel de Amistad":
                analizar_nivel_amistad(st.session_state.df_chat)
            
            elif opcion_elegida == "4. Análisis de Actividad y Horarios":
                analizar_actividad(st.session_state.df_chat)
            
            elif opcion_elegida == "5. Palabras y Emojis Más Usados":
                analizar_palabras_y_emojis(st.session_state.df_chat)

            elif opcion_elegida == "Selecciona una opción...":
                st.info("Selecciona un análisis para ver los resultados aquí.")
        
        else:
            st.info("Carga un archivo y selecciona un análisis para ver los resultados aquí.")


