import streamlit as st
from Analisis.Utils.aux_opciones import procesar_chat
from Analisis.Opciones.msgcount_01 import mostrar_analisis_conversacion
from Analisis.Opciones.sentimientos_02 import analizar_emociones
from Analisis.Opciones.compatibilidad_03 import analizar_compatibilidad

# --- Interfaz Principal de Streamlit (main) ---

def main():
    """
    Función principal que dibuja la interfaz de Streamlit.
    """
    
    # --- 1. Configuración de la Página ---
    st.set_page_config(
        page_title="Analizador de Chats",
        page_icon="💬",
        layout="wide"
    )

    # --- 2. Inicializar Session State ---
    # Esto es clave para "recordar" datos entre interacciones.
    if 'df_chat' not in st.session_state:
        st.session_state.df_chat = None
        st.session_state.file_name = None

    # --- 3. Título de Bienvenida (Tu solicitud) ---
    st.title("Bienvenido al Analizador de Sentimientos 💬")
    st.write("Sube tu chat de WhatsApp (.zip o .txt) para descubrir las emociones y compatibilidad en tus conversaciones.")

    # --- 4. Definir Layout (Columnas) ---
    col_controles, col_resultados = st.columns([1, 2]) # Columna de control (1/3), resultados (2/3)

    # --- 5. Columna de Controles (Izquierda) ---
    with col_controles:
        st.header("1. Carga tu Archivo")
        
        # --- Lógica de Carga de Archivo ---
        if st.session_state.df_chat is None:
            # Estado A: No hay archivo cargado
            uploaded_file = st.file_uploader(
                "Selecciona tu archivo .zip o .txt",
                type=["zip", "txt"],
                help="Exporta tu chat desde WhatsApp (sin multimedia) y súbelo aquí."
            )
            
            if uploaded_file is not None:
                # Archivo recién subido -> Procesar y guardar en el estado
                with st.spinner("Procesando tu chat... ¡Esto puede tardar un momento!"):
                    st.session_state.df_chat = procesar_chat(uploaded_file)
                    st.session_state.file_name = uploaded_file.name
                st.success("¡Chat procesado con éxito!")
                # Forzar un "re-run" para mostrar el estado B
                st.rerun() 
        
        else:
            # Estado B: Ya hay un archivo cargado
            st.success(f"Archivo cargado: **{st.session_state.file_name}**")
            st.write("Diez mensajes más recientes:")
            # Usamos .tail(10) para los más recientes
            st.dataframe(st.session_state.df_chat[['Autor', 'Mensaje']].tail(10))
            
            if st.button("Cargar otro archivo"):
                # Limpiar el estado para volver al Estado A
                st.session_state.df_chat = None
                st.session_state.file_name = None
                st.rerun()

        # --- Selector de Análisis (Opción 2) ---
        st.header("2. Elige un Análisis")
        # El selectbox solo se activa si el DataFrame está cargado
        opciones = [
            "Selecciona una opción...",
            "1. Análisis de Autores",
            "2. Análisis de Emociones",
            "3. Análisis de Compatibilidad"
        ]
        
        opcion_elegida = st.selectbox(
            "Elige el tipo de análisis que deseas ver:",
            options=opciones,
            disabled=(st.session_state.df_chat is None) # Deshabilitado si no hay archivo
        )

    # --- 6. Columna de Resultados (Derecha) ---
    with col_resultados:
        st.header("Resultados del Análisis")
        
        # Mostrar resultados basados en la selección
        if opcion_elegida == "1. Análisis de Autores":
            # Pasamos el DataFrame desde el session_state
            # La función cacheada se ejecutará solo si es necesario
            mostrar_analisis_conversacion(st.session_state.df_chat)
            
        elif opcion_elegida == "2. Análisis de Emociones":
            analizar_emociones(st.session_state.df_chat)
            
        elif opcion_elegida == "3. Análisis de Compatibilidad":
            analizar_compatibilidad(st.session_state.df_chat)
            
        else:
            # Mensaje por defecto
            st.info("Carga un archivo y selecciona un análisis en el panel izquierdo para ver los resultados aquí.")

# --- Punto de Entrada ---
if __name__ == "__main__":
    main()