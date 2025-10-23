
import streamlit as st
# --- Interfaz Principal de Streamlit (main) ---

def show_privacy_notice():
    """
    Muestra el aviso de privacidad en pantalla completa y bloquea la app.
    """
    st.title("🔒 Aviso de Privacidad")
    st.markdown("""
    ### Sus datos se procesan localmente en su navegador.

    Para que esta aplicación funcione, su archivo de chat (.zip o .txt) se procesa en la memoria de su navegador. 
    Los datos se utilizan **únicamente** para:
    
    1.  Procesar el texto y extraer los mensajes.
    2.  Alimentar los modelos de análisis de sentimientos.
    3.  Generar los gráficos que se le muestran.

    **Esta aplicación NO almacena sus datos en ningún servidor.**
    
    Toda la información (incluyendo los gráficos generados y los datos cacheados) se elimina permanentemente 
    en el momento en que usted cierra la pestaña del navegador o actualiza esta página.
    
    ---
    **Al hacer clic en 'Aceptar', usted confirma que entiende y acepta este proceso.**
    """)
    
    col1, col2, _ = st.columns([1, 1, 3]) # Columnas para los botones
    
    with col1:
        if st.button("✅ Aceptar", type="primary"):
            st.session_state.privacy_accepted = True
            st.rerun() # Volver a ejecutar el script para mostrar la app
            
    with col2:
        # El botón "Negar" no hace nada, por lo que el aviso permanece
        st.button("❌ Negar", type="secondary")
        
    st.info("Debe aceptar los términos para utilizar la aplicación.")
