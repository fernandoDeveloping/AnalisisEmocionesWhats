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
            # URL de tu perfil
            linkedin_url = "https://www.linkedin.com/in/fernando-rodriguezr/"

            # Icono de LinkedIn (codificado en Base64 para que no necesites un archivo local)
            linkedin_icon_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAQAElEQVR4AeydB7wtVXXGDxEVsRts0dhrYoui2GIvGGNXNHYUxZbYInaxYcFeIKJRLGCNRkUwURJbNMYSS6xRo9gBFQugCEK+j/su9753T5myZ2btvf/vt9fbc+fM7L3Wf82Z+WZPOX804x8EIAABCEAAAtURQABUl/KSAt6ppGCIBQKNCbDlN0bFggsJzGYIgCVw+Cg6gTOiO4h/EJhPYKf5s5vOZctvSorllhFAACyjw2cQSE6g554/uT8BGqwRCUfwABte3S44egSAKWAQGI0Ae/4tqEGyBQkzIDAGAQTAGJTpAwIQgAAEIBCGwJojCIA1DvwPAQhAAAKlEajx8lKLHCIA1mGxoayToIYABCBQBgEuL83N4/pMBMA6CTaUdRLUEIAABCBQAQEEQAVJJsQuBBgS6kKNdSAAgegENvxDAGywYAoCmwgwJLQJBpMQgECBBBAABSaVkCAAAQhAAALzCGyehwDYTINpCEAAAhCAQCUEEACVJJowIQCBMgkUd7dKcQFF2u629wUBsD0P/oIABCCQFYHi7lYpLqC4mxMCIG5u8AwCEIAABCCQjMCODSEAdiTC3xCAAAQgAIEKCCAAKkgyIUIAAhCAQO0EtsaPANjKhDkQgAAEIACB4gkgAIpPMQFCAAIQgEDtBObFjwCYR4V5EIAABCAAgcIJIAAKTzDh1UOAx6fryTWRQqAdgflLIwDmc2EuBEITmHew5/Hp0CnDOQiEI4AACJcSHILAagIc7FczYgkIQGCNwKL/EQCLyDAfAhCAAAQgUDABBEDBySU0CEAAAhConcDi+BEAi9nwCQQgAAEIQKBYAgiAYlNLYBCAAAQgUDuBZfEjAJbR4TMIQAACEIBAoQQQAIUmlrAgAAEIQKB2AsvjRwAs58OnEIAABCAAgSwIzHs/yDLHEQDL6PAZBCAAAQhAIBMCO74fZJXbGQmAttpmVeh8DgEIQAACEKiXQEYCoK22qTepRA4BCEAAArUTWB1/RgJgdTAsAQEIQAACEIBAMwITCACG8pulhqUgAAEIQAAC3Qg0WWsCAcBQfpPEsAwEIAABCCwjwMnkMjpNPptAADRxi2UgAAEIQAACywhwMrmYTrNPEADNOLEUBCAAgVEIcF47CmY6EQEEgCBQIAABCEQhwHltlEzk60dTz7sJACRqU74sBwEIQAACEAhJoJsAQKIGTCaqLGBScAkCEIDAyASad9dNADRvP8qS55QjF5ZdSnYl2TVk15HtIbtlGXZGIXHMiGMGgzK+k+QxcB5vIt+uK7uW7M9kl5VdXHZeWTWlZAFwIWXxCjIf5B+g+rmyQ2UflP237HOyT8uOxmYwmMGA7wHbQEXbwMcU62dkX5B5+p2qXyl7rGxP2Z/L/kR2DllWpY2zpQmAXRT85WQ+i3ya6vfLfJA/RPVDZbeQ+fOzqaZAAAIQgAAEdhOC3WV3lz1L5pPEj6s+WHYfmUeMvYwmyyqlCIBdlZaryPaWvUvmM1oruatqmgIBCEAAAhBoQ8AjyHfSCm+QfUTmEeQbq76oLHBp59oKARD+xrKdFa4P/I9SfZTMiu3aqikQgAAEIACBFAQsBvZVQ5+QvULmkeQ/Vp19WSEAQt/ufxHRv4vMZ/wvVO2bOFRRIAABCEAAAoMQuKda/TfZAbJrynwSqipGaevFCgHQtrlRlrfPvibzMvXmGzeuppoCAQhAAAIQGIuARwSOVGd7yS4oy7L4YJqT477W7+syPuu/d06O4ysEIAABCBRF4BKK5nDZ02V+4kzVlKV93zkJgAsoPN/J/x7VfpZfFQUCEIAABCAwKQHfcO77z/xOgUkdadt5LgLA1/sfreA87K+KAgEIQAACEAhBwDfL3VqevEXmJwUmuXtefbcu8wVALPf92MWTFNkzZRQIQAACEIBAJALrR0zfj3aYHLuZLIsyXwBYz8Rw3zdXPEyueIhFFQUCEIAABCAQlsCl5dlBsuvJRizdupovALq1lXot3/D3QDXKmb8gUCCwQWD9hGNjDlMQgEB/Aom+WX4Bnd8X4BGB/k4N2EJUAeA83Epxv0BGgUC1BPxF2Bp8nCG6rb4xBwL5Ekj0zXIz1xeFx8v8ewKqhi1dW48qAHw35fMVVNE/xKD4KBBYSsB7kqUL8OEWAvNF05bFmAGBoQisb4IewfZvCXg0e6i+erWbUACsx9zLH698Mf33CJl/olEVBQIQgEBzAoim5qxYcnAC/nEh/+zwgB11bzqhAEjytbOK8GMU+3QPiTUhAAEIQAACIQicS148UnYpWbiSUAAkic03T+yXpCUagQAEIAABCExP4B5ywY8GDvIz9Gq7c4kkAM6uKG4kCztcIt8oEIAABCAAgbYEHq4VLi8LVSIJgCuKzENkFAhAAAIQgEBJBPxUgN8NkHgUoB+iKALAflxboXD2LwgUCEAAAhAojsCDFZFfFKQqRvGBN4Infyon7iyjQAACEIAABEok4PsAkgqAvpCiCADfIXnbvsGwPgQgAAEIQCAwgdvItwvJQpQIAmAXkfC1kfOopkAAAhCAAARKJXB7BXZxWYLSv4kIAuAiCmMPGSU6Ab+lIbqP+AcBCEAgLoGryzUf81RNXyIIgN2EwSMAqiihCSR511PoCHEOAhCAwNAErqkO/IIgVd1LijUjCIALK5BQN0bIHwoEIAABCEBgCALXUaMh7gOYWgD4mUg/ASAeFAhAAAIQ2EqAa29bmWQ957Ly/tyyHiXNqlMLAN/4ZxhpoqEVCEAAAsUR4NpbSSmVnLuM4kEACIIFwCVVUyAAAQhAAALFE5Ccu4SC7CUAtH6SMvUIwM6K4nwyCgQgAAEIQKAWAueIEGgEAbBrBBD4AAEIQAACEBiJQI+nANJ5GEEAhACRDiktQQACEIAABJYSCHHiO7UA2EmIfBlAFQUCEIAABCBQBQEf93z8ax1syhWmFgApY6EtCEAAAhCAAAQaEkAANATFYhCAAAQgAIFpCaTtHQGQlietQQACEIAABLIggADIIk04CQEIZENg8iu72ZDC0ZYEUi8+sgDgm5E6gbQHAQgEI3BGMH9wBwILCIwsAPhmLMgDsyEAAQhAAAJLCKT/aGQBkD4AWoRASQQYIyspm8QCgdgEEACx84N3lRFgjKyyhBMuBBoSGGIxBMAQVGkTAhCAAAQgEJwAAiB4gnAPAhCAAARqJzBM/AiAYbjSKgQgAAEIQCA0AQRA6PTgHAQgAAEI1E5gqPgRAEORpV0IQAACEIBAYAIIgMDJwTUIQAACEEhDIN9HbNPEP68VBMA8KsyDAAQyJ8DuPvMEJnefR2y3IkUAbGXCHAhAIHsC7O6zTyEBnElgyP+6CwAE9pB5oW0IQAACEIDAoAS6CwAE9qCJoXEIQAACEKidwLDxdxcAw/pF6xCAAAQgAAEIDEgAATAg3PGa5nrMeKzpCQIQgMA4BIbuBQEwNOFR2ud6zCiY6QQCEIBAQQQQAAUlk1AgAAEIQCAPAqvHbYePAwEwPGN6gAAEIAABCGxHIP24bXtJgQDYLiX8AQEIQAACEJieQHsP2ksKBEB7yqwBAQhAAAIQyJ5APAHQfhQj+yQQAAQgAAEIQGCDwDhT8QRA+1GMcUjRCwQgAAEIQKAgAvEEwGBwGVoYDC0NQwACEIBAMgJjNVSRAGBoYayNin4gAAEIQCA+gYoEQPxk4CEEIAABCNROYLz4EQDjsaYnCEAAAhCAQBgCCIBRUsH9B6NgphMIQKASAuXuU8dMIAJgFNrcfzAKZjqBAAQqIZDhPjWgZkEAVPJ1IUwIQAACEJiQQCPNMq5/CIBxedMbBCDQm0DAU6neMdFAjgRy3xIRADludfgMgaoJBDyVqjof9QafekscmyQCYGzi9AcBCEAAAhAIQAABECAJuFAvgdyHEOvNHJFDIDWB8dtDAIzPnB4hcBaB3IcQzwqECQhAIDsCCIDsUobDEIAABCBQGoEp4kEATEGdPiEAAQhAAAITE0AATJyAxd03vDrccLHF/cz95Deae6LsDzIKBCAAAQgMSmCaxhEA03Bv0GvDq8MNF9vU4U81/UHZK2V/L9tLdn3ZVWSXl11OdnXZ1WRXlF1B5np31XeRPWa20+wlqo+Q/UhGgQAEIAAB7Rhzg4AAyC1j7f39mVY5TPYw2fVkN5DtLdtf9hrZe2X/Jfum7P9k35Uds808/R1Nf1v2edkHZK+bnTF7jup9ZDeUWRi4vTdp+ngZJSKBYUaKRo60iCBGZkZ34xFofza27ttUNQJgKvLD9vtrNf962Z1kPrt/jGofoD+r+nuyY2W/lJ0kO1XWtJymBU+W/Up2nOz7MguDt6p+nMwC446qXyvzMqooIQjkt2+ag62IIObExSwITEMAATAN96F6/R817APxHqqfIDtS5jP4n6v+nWyo8ns1/AuZxcVRqveTWXjYl//VNAUCEIAABOYSmGDmtsE0BMAE7Afo0kP2+6rdO8s8rP8N1SfIpriJz3367N8+eCTgVvLjIbJvySgQgAAEIDA1gW2DaQiAqRPRr38P4/ts+zZqxkP8vob/W01HKb7E8AM582bZ7WXPk/nyhCoKBCAAAQhMSQABMCX9fn37Tv491cRBMg+zn6I6avElAo8AHCAH/STBJ1RTIAABCEBgQgIIgCXwt10mWbLEJB/5pj1fW/dd/b573zflTeJIh07t679rvfvJLFwaiJagWVAAFAhAAAL9CEy7NgJgCf9tl0mWLDH6R37M7q7q1dfWfQe+JrMsvmfhifL8yTLfoKhqtgD3gtleA4MABCAAgc4EEACd0Y2+4pfUo4fPPfTva+v6M+viGDwK8FhFYUHgU32O9oJBgUBRBPzNLiqgdMFM3RICYOoMNOvfz9o/UIt+Uua77FUVUXxvwOGKxI8s+mVDZe8qyo5OaaRAYA4BZP0cKDFmIQAGz0Pvvf7X5KLfuvdF1SWW0xXUu2R+u+APVZdb2BGWm1sig0BrAtOvgAAYPAe99vp+hM6v2S314L+Z/lv0x0tlfqGQKgoEIAABCAxJAAEwJN3+bT9STXxGVkOxUjpYgfqSgCoKBCAAgXIJRIgMARAhC/N98C/1fWj+R8XO9WOBByq698koEIAABCAwIAEEwIBwezTtn9p9o9b3AVFVVcX3ARyiiP3rhKooEEhEoPftOIn8oBkIzGIgQADEyMNmL/wq3/01Y/35eE1WV/yoo28MLOmJh+qSGC5gX2QK5xQOQWA6AgiA6dgv6tmvy/Wv+i36vJb5hynQj8gmLpw2TpwAuodAcQSiBIQAiJKJNT/8Qpx/1ORpstqLLwH4XoDfTAuC08Zp+dM7BCAwFAEEwFBku7X7cq32MxlljcCRqv5DRoEABCBQCIE4YWwvABjtnDIzP1Xnb5dx3VsQtpXvqj5a9jsZBQIQgAAEEhLYXgAw2pkQbeum/CIc/9hP6xULX+Gjis+vQlZFgQAEIJA3gUjeby8AInlWny8WAH4tbuvICx+4+W8BZLwfbQAAEABJREFU+ayMAgEIQAACCQkgABLC7NGUD3Df0fqdxmA6raTOMioeATg2I39xFQIQCEUgymlSKCgzBECMfPyT3DhVRplPwKMAX5j/EXMhAAEIrCJQwWnSKgRzPkcAzIEywawPq08e/ROEBeXrmu/HAlXFLJxfxMwLXkEgEoFoviAAps+IH/v7ttxAogrCgmI2ZhR2lMQOLvCd2RCAAARCEkAATJ+WT8sFHnMThBXFAsD3SaxYLObHjBDEzAteQWA8AvF6QgBMn5MvyQVOIAVhRfGPBP1oxTJhPybBYVODYxColgACYPrU/69c4PggCCvKcfqcJwEEoaTCyEhJ2SSWZQQifoYAmD4rFgCdnv+f3vVRPUAAjIp7nM5QvuNwphcIzCOAAJhHZdx5P1B37AcFoUGp+SeSG+BhEQhAICaBmF6NKgAY7pu7Efxy7lxmziNw4ryZzIPAuATYk43Lm96GIjCqAOA0d0saPfRv2/IBM+YS+K3mniyjQGBCAuzJJoSfZddRnR5VAESFMKFfPqNlb9I8AT7425qvwZIQgAAEIDCXAAJgLpbRZvrgz3hic9weLbE1X4MlIQABCExKIG7nCIBpc7PrtN1n1/s55LFNFQUCEIhKgLOaqJnZ3i8EwPY8xv7r7OoweQ4K/vKdU7xsqigQgEBUAh7ajOrb2H5F7i/5wSdysMP61vmwe57UfhX85dtFrM4lo6Qm0HnzTe0I7UEAAmMRQAAkI935sHtJucDuVxAalAs0WIZFuhDovPl26Yx1IFALgdhxIgCmz88V5QJ5EIQVZWd9fmEZBQIQgAAEEhDgwJMAYs8mLq/1GQEQhBXFB//dVizDxxCAAATCEIjuCAJg+gxdSy6QB0FYUS6hz22qKBCAAAQg0JcAB56+BPuvf2M1QR4EYUW5nD6/gowCAQhAIAMC8V3kwDN9ji4mFy4jK/wyQO/wfKnErISKAgEIQAACfQkgAPoSTLP+zdXM2WQFl163mZ9fYK4ko0AAAhDIgkAOTiIAYmTpXnKDXAjCgnIdzfe9EqooEEhBoPeIVAonaAMCkxLgoDMp/rM6v5GmLiWjzCdgAXCN+R8xFwJdCPQakerSIetURSCPYBEAMfLk4f+7yhXXqiibCFxE07vLRthWOSsUZwoEBibA92xgwI2bH2Gn2tiX2hfcRwDOK6NsT+Bm+tNPSqgaunBWODRh2ofAbLbke1aINsglywiAOJnyGwH/Su6QE0HYViyIbqPpP5FRciTADj3HrE3n8xJtMJ1T5fbMwSZWbp8gd84to6wRuKWqW8souRJgh55r5vC7M4F8VkQAxMqV73TfSy5x3jSb+bW/dxELbo4UBAoEIACB1AQQAKmJ9m/v6WrCb71TVXW5h6K/o4wCAQhAIBsCOTmKAIiXrUvLpf1k/vU7VVWV9ZEPj4TcT5FfQEaBAAQgAIEBCCAABoCaoMm91ca9ZbUVXzH20P+jFPgNZBQIQAACGRHIy1UEQMx8nV1uPU/mF+CoqqZ4BOChivaeMgoEIAABCAxIAAEwINyeTfunb5+vNrbcD+CjpOaXWHwDpAXAeUoMjpggAIGyCeQWHQIgdsb8CJxFgMXAWZ56nPysP8qZuL1C2V/meyBUFVwKVnAFZ43QIFAcAQRA/JT6rPjZcrPkn8LdU/EdILuqrPxSqIIrP3FECIFlBPL7DAGQR84eJDefI7u8rKTic+E7KaAXyq4po0AAAqUR8Le8tJgKiQcBkE8i/VsBB8rda8t2KFl+w/zGQ8f0UgXDL/0JAgUCRRKoZMQrx9whAPLKmn8x0AdMXxbY9MuB2X3DPJLxNKH3kw5bbnLUfAoEIAABCAxMAAEwMODUzetc/6Zq8xWyJ8kuI2td1EbrdRKt4Mcbfb3/ZWrviTI/86+KAgEIQCBnAnn6jgDILG/bzvV9Q+Bz5fqLZH5mvtUb87a1oVVHLb7G/2T1+BrZHWQT6hD1ToEABCBQOQEEQN4bwN3l/sGyZ8luJdtVFq1cRQ49QnaQzH6W/5ifAqVAAAL1EMg1UgRArpnb8PtCmvw7mQ+wflzQZ9cX199TFt/g51f5PlZOvEr2atmNZBQIQAACEAhCAAEQJBEJ3LiS2ni87HUyvzxoX9W3lI31c7rnUl++m983KD5D04fIfMOiRyYY7hcMCgQgUCKBfGNCAOSbu0WeX1QfPEDma+0+CPsFOxYDt9U8X4dPdeOdRx7+TG3eQnYf2VNlPuC/WbV/zfDqqikQgAAEIBCUAAIgaGISueXH7e6rtiwG3qjaTw/4MoEP0A/U33eReZTg+qr9w0P+GV6/je/K+vvPZT6j3121h/O9nJf3eo/TPF/P9938b9D0YTILAC9zTk1TIAABCFRBIOcgEQA5Z6+d735ywI8QPlyr+c17h6p+q+z1sn+Q+Tq9BcJLNP1imQ/u/tvz/bmXO1zzvZ6XeZSmbyPjpj5BiFG40hIjD3gBgTwIIADyyNNQXu6ihn0A95m/RwFuor9vJ/trmX+I6Gaq95D50oGX83V+/UmJSWCiBzxjwsArCIxAIO8uEAB55w/vCyHAuXshiSQMCGREAAGQUbJwtVwCnLuXm1siK5dA7pEhAHLPIP5DAAIQgAAEOhBAAHSAxioQgAAEQhLgWtKIacm/KwRA/jkkAghAAAJrBLiWtMaB/xsRQAA0wsRCEIAABCBQCoEUAyUlsEAAlJBFYoAABCAAgcYEGChZQ4UAWOPA/xCAAAQgAIGGBMpYDAFQRh6JAgIQgAAEINCKAAKgFS4WhgAEIACB2gmUEj8CoJRMEgcEIAABCCwmwJ1/W9ggALYgYQYEIAABCBRHINmdf+WQQQA0yCXCsQEkFoEABCAAgawIIAAapGs64Yj0aJAeFoEABCAwGoGSOkIAhM7mdNIjNBacgwAEIACB3gQQAL0R0gAEIAABCNRBoKwoEQBl5XMtGq4crHHgfwhAAAIQWEgAAbAQTcYfcOUg4+ThOgQgEJVAaX4hAErLKPFAAAIQgAAEGhBAADSAxCIQgAAEIFA7gfLiRwCUl1MiggAEuhE4TaudLDtBdpzsJ7Ifyb4vO0b2Xdl3Npn/9vwfaJ6XPV71L2Qnyk6VZVW4dSirdCVxFgGQBCONQAACmRDwHTI+QP9U/vpg/mXVn5MdLXuH7BDZ82VPkz1O9mjZw2UPkd1f9jeye8tc763a8/354zX9dNnzZK+SHSY7SvZpmfv4luofyiwQfq96xNLs0G4wIzqVXVclOowAKDGrxAQBCKwT8MH2WP3xTdlnZf8se6VsP5kP4jdXfV3ZrWX3lfmg/yLVr5O9XfZumQ/kH1b9HzK38Zlt9cdUe/6Rqt8ms3h4ieqnyB4ku73sBrK/lN1D9ncyC4Q3qfa6X1XtEQSPOAx4/B2waQVAiUOgmdTb8BcBsMGCKQhAoAwCv1QYHp7/vOrDZT4g30X19WR3kz1V9haZD+Y+I9fkoOXXav1LMosPC4SHavpmslvIPG3B8X5NWxD4coJHKPQnJQ6BPDxpK/UQAHnkFS8hAIHlBH6lj33Q/xfVPsveS/XuMp+Jv0H112XRiu8z+JCc8iWHO6veQ7aP7NWyj8scj+PSJAUC6QkgANIz7dOibxz6mhr4CjYzgzHOzoS6VfmNlvbZnP2r3f5HLP4gm6qcoo59k56H5l+m6TvKbifzGbWv62syYFk8TnuSvLUgeLLqm8ruKnupzPE5zt9qmjIBgVK7RADEyqxvTLqOXLo6NruGGPgarKpQxWdm15JH5Gh2Zo6mGK72nfrfUw7eKvMNeb7G/ixNW5CpCl6aj9N+UZE8W+b47qna9yVYdEUUxnKPkhsBBEC8jC0+P4jn65AeReWw85BB0/ZSAr6W7oP8a7TUnjIP71uQabL48klF6CcSbqjaIwQfVe2bG6ccgZELI5TJ9wQjxDhRFwiAicAv6ZbNfQ2OOdjW/orz/9miuBIRzkBsfMbvx+gOVPs3lvmRO9/Vr8nqikdcXquo/fSCH0H8V03/TFauEGg+YiIMlDYEEABtaLEsBGazMMfdCvaLfoTPL+E5eDabeRj8ANXcFCcI28oRqv2o4f1U+1FFLg0IROpScnsIgJKzS2xDEAgjAIYILlCbfjbez+DfUj49QebhblWUOQT85INvgPSIgC8V+FLJnMWYBYHtCSAAtucx2F+rjhqrPh/MMRpuS4DvTFti7Zb/nRb3kzB+u55v8Pu2/qY0I/AeLXYr2f4yXzLxU0WapHQnUPaa7MxGyu+q4dpVn4/kJt2sJoBWW82o6xIe3j9UK/sROL+WV5OUlgQsoF6udW4r89sJzVSTFAhsJYAA2MqEORBYRsDfGZ4EWEao/WfWv77W/zCt+giZb2pTRelBwC8ReoDW92WBb6j2Dx2porQhUPqy3pmVHmMl8XFiOlKiDTrMkwAjxTxkN77Rz4/y+bG+iO99GDL2Mdp+lzrxaMA/qfbogCoKBNYIIADWOBTwv0+iCggjfggWAIwApMmT3+TnH9Dx2/sivqo3TZTTt+LRFT8p8ES54tcPq6KsJlD+EhsCwLu18uMlQgj0JeDvzMoRAL5OKzH7lcp+e59/fY9X3K7E1XsBXwLwryDeXS35R4c4YxCI2r+n3pkJgwqbgyBQILCSgPcZK0cA+Dot5Xi8Pn2gzD+C4wOTJikjEfiE+vG7A/wCodM1XXVZ9j2tAcyGAOgdrfeLvRsJ10CZUYXDnJND3iRWCoCcAhrZ15+oP5+F+pE1TVImIHCM+ryP7E0yBJgg1FoSCoAytVSZUdW6uSeJ2wIg4fcmiU+5NOKD/z3krG/6U0WZkIDfGvhI9e9fTmQ3JxDblzr+YkdWR56JMh0Bf2dW3gOQrrtiWvqhIrmDzG+qU0UJQMD3XjxHfjxDxkiAINRWvDOrLWbihUBfAh4F6NtGTev/XMH652w/r5oSi4BFgEcBnhLLrWm9qaV3BEAtma4iztGOy6N1VEDa/F56H/z/s4BYSg3Bj2O+WsE9U0apiAACoKJklx/qKJcyffC3lY+zb4Q7zfwu+r3VzL/LRkmO+qF0I+CRgBdr1RfIKi/1hI8AqCfXRAqBcQmcMfOw8hHqNO+Dfz1y7yTl6kDZG2WUCgggACpIMiEmJ1DPIaE7ujdoVQ8rexRAkxmXvOVLW/D+Geb9tNKHZFWWmoJGANSUbWJNQcAHf743y0l+VB8/WrbDu+eNTnMp0Qn4RU3+USb/iFB0X/GvBwF2ZD3gsWq1BDiSLU79T/XRg2UnynYodZ1K7xB8bn9+Rw7vIztZVlGpK1QEQF35Jto0BOoUAKuj9qtlHyTEftOcKkrmBD4r//2yIFWUfAis/qKux4IAWCcxSN08EYN0T6NDEHBSbUO0HbvN1Sfwz1MAR8v+IKPkT8A/1fzPCuP1sipKGUGu/qKux4kAWCcxSN08EYN0T6MQGI/AF9SV7yDP/6Y/BUI5i8CvNOW3BX5LNaUwAgiAwhJKOKMQqHMEYD5as/BB//SI19EAABAASURBVCH6eM51f82l5E7g+wpgX1nhpb7wEAD15ZyI+xHwAY/vzQZD/y7CU/Xnl2UMeQlCgcV59f0AfmVwgeHVGxI7snpzT+QQSEHg42rkIJlHAVRRCiXg0Z1XKDY/HaCqvFJjRAiAGrNOzH0IMAKwQe+8mvQjfzs876+5lBIJHKegniijFEIAAVBIIgkDAhMQOL/69HP/fvxPk5TCCXiU5yOK8T2ywkqd4SAA6sw7UXcnwAjABrsfatLXh1WNVYx/rL7oZw6BX2jes2SIPkHIvSAAcs8g/k9BgKPQFNTP7HNkvXFmn/y3A4Hv6m//zoOqBCXAtylBFFk2gQDIMm04DQEIQGAyAr9Rz6+S+cZAVT0Lmq4nwO6rIwC6s2PNeglwzlJv7ol8jcCPVb1AVkCpN4S6BAC77bRbep08HbUtLUtay5hAlZuDfyTojUraL2UDlyr5Dsx0rfm6BABDTWtZT/V/vTzZI6Xahopop9ovgg/+Bw+fwmH5Du9/3B7qEgBx84BneRFAAOSVL7wdhsBJatY/FMR7IAQix4IAyDFr+DwlAR/8bVP6QN8QiELgeDnyOlmmpW63EQB155/ouxFAAHTjxlrlEfATAYeWF1YdESEA6sgzUaYj4IM/35t0PGmpNQFvgq1XGnKFY9T4h2TZldodZkdW+xZA/F0IcFdSF2qsk4hAuM3PowBcBkiU3TGbQQCMSZu+SiEQ7hSsFLDEkSUB/0bAR+W5Xw2tKpeCnwgAtgEItCcQ7hSsfQisAYGkBPxegLcnbZHGBieAABgcMR1AAAIQKJ7AbxVhVgJA/lZfEADVbwIAgAAEINCbgEfF/CNBX+rdEg2MRgABMBpqOoIABCBQNAFfBnhnHhHipQkgAEwBg0BzAj7TsTVfgyUhUAcBvxHw/XWEWkaUCIAy8kgUEIAABCIQ+Imc+IosdMG5NQIIgDUO/A+BpgT8CKCt6fIsl57AedXk9WR/I3uK7BDZW2Tvkx0lO1L2Dtk/yl4le7rMy15L9a4yynAEfDPgB4drnpZTEshTALD7TbkN0FY7Ah7+t7Vbi6X7ENhFK/+1zAfzL6j2WeYnVb9Z9mzZPrJ7y7zMbVXvKbu7bG/Zw2X7y7zsZ1SfIPua7CDZHWTnk1HSEfBlgA+ka26IlmhznUCeAoDd73r+qCFQMoFbK7i3yX4ge4/MB/Nrqj63bOdtdjbV3o8tMn9u8/Jn17LnkF1Ftq/s3TK37foWmvZyqig9CJyudS2wfq6aEpyAvzTBXcQ9CECgIgI+23+U4v267AjZPWS7yXzw9gE6xfif23BbbtMjAHdW+36X/edVP0hmgaGK0pGARwE+3nHdwVejgw0CCIANFkxBAALTEfBB+WHq/quyl8quLDunzAdqVYMW7wfdzzXUy+tlH5H5UoIqSgcCv9c6H5NRghPwhj/zNy+4n7gHAQiUS+CGCu1TspfLLivzmfkUu6X1PneXDx59eIPqS8oo7QgEFgDtAil96TMFAJfU26Z5fT/Rdj2WhwAEdiDwYv3tg+0eqn3GH+HLZR8sQnwToe8PuJF8oywkYFxbPvS9FT/eMpcZoQicKQBCeZSFM0imLNKEk5sIzN1Jb/p89MlLq8ejZb7efyHV4RyUTy5+3PBdmrivjDKXwNz94Sla1E9dqIpT8GR7AgiA7XnwFwSaEJi7x2uy4nTLhHLZB9V/EQvfee+zfk2GLheXd34E8YGqKc0InKbFPiejBCaAAAicHFyDQIEE/Ly+H+nzo3hRz/rnYb+AZvrmxPurpqwmcKoWCSYA5BFlOwIIgO1w8AcEUhLI6fiWMu6FbT1An/ggegnVOZYLyukDZXeTUZYT+IM+5pcBBSFyQQBEzg6+ZU4g1LD71Cz9Kt4XyomLynIu9v/xCsBPCqiiLCHgXwf85pLPR/2IzrYSWCIAOHvZios5EIBABwI31zovkvngqSr7cgNF4JsXcx3JkPujFN8H4Pc6jNIZnbQnsEQAcPbSHidrQAACOxC4vP72j/WUdrD0vQB+S6HCoywg4MsAfi3wgo/HnE1f8wgsEQDzFmceBCAgAqhjQWhYDtVyFgGqiioeIr2fIuIdAYKwoPQSAAa8oF1mJyKwgwAAeSKuNAMBCMxmfnTuugKxw35Gc8oo11YYviGQ3w4QiDmllwBIqbLn+MYsEdjhiwlyMaFAAAL9CdxRTdxL5h/3UVVs2UuR+X0Gqig7EPAB5YeaZyGgihKNwA4CIJp7+AMBCGRIYFf5/DyZf8VPVdHF9zbcShGeR0bZSsDvA/Brgbd+MtocOlpEAAGwiAzzITCfgM9q5n/C3HUCB2jiCrJayu0U6F/KKFsJnK5Z35NRAhJAAARMCi6FJsCNMsvTczV97Gf+c3jFr1xNUq6oVvyoo39SWJPTlYAbp4f/JxUA02Ujfs8IgPg5wkMI5ETgOXK2hqF/hblduaH++gvZpCXg8JRHAI6ZFAqdLySAAFiIhg/SEQh4XpIuOFraIHB1Td5ENvmZsHwYu/hph8kFwNhBN+jPAuD7DZYbaBGaXUYAAbCMDp8lIhDwvKR7ZEUF0x3D3DX9itzzzf2k/JnnUIh+PXCt8Sv8ucUC4KdzP1kwk9OFBWAGmI0AGAAqTUKgQgKXUsy+GW5n1bUWvxfgGrUGvyBuC4BjF3w2d3ZKhT23A2aeRQABcBYKJiAAgR4E/lbrXkBWc/ENkFeuGcCc2H08P27OfGYFIIAAmJsEBqHmYmHmOgHv1NanqWczn/X7hTgeBq+Zh196ZAHADmT7reAk/emRAFVjFvpaReCPVi1Q5+fs3+vMe+OoC9rBJwnl9iL3xzLKbHYVQajpHQgKd2Xxo4DHr1wqyQJJtucknuTQCAIghyzhIwQGI5BE7Pra/9kHczGvhj0C4PcC5OX1sN56Izth2C62ts6c1QQQAKsZsQQEILCcwE31MQJAEFQuLfMNkaoo2whYAPx62/TAlbsauIvwzTcfBUEAhE8mDgYkwF5mIyn+JbyL68/mex0tXHDxGxD/tOD4uoTm78uJXVbsvk7Naxp3s/gRAM04sRQEIDCfgK95+ybA+Z/WOdc/EFT7ExGbM+8jEgJgM5Eg0wiAIInADQhkSuCq8pv9iCBsKhYAtk2zqp60AOh5CaDdAFPVtFsEzxe3BSwWhQAEthC4kuYk349kvru/sJhcREZZI2AB0HMEwE2sNcb/6Qgk/+Kmc42WIBCWAHujjdRcTJPJ3/2fOeDdxITHIgVhU/n9pumBJ2m+KQEEQFNSLAcBCMwj4ANd5ifs88LqNe9CWtumiiIC1nOnqaYEI4AACJYQ3IFAZgQ83I0A2D5p59KfFkaqKNsIjCYAtvVH1YAAAqABJBaBQB8ChR8dfaZbeIidsn/BTmuVu9KpZ4bGlnImhij/IQCiZKIGPyr98nv8s+D0+j0AlWZ2aVbNpfbfRlgH5K/A2giAp9bnDlLTaBsCCIA2tFi2HwG+/P34xVybNwDOz8uumm0RoIoiAv49AFWUSAQQAJGygS85ELCMseXg6xg+IgDmU/bB3zb/0/rmjvKdqQ9rv4gRAP34sXZ9BDzcbasv8vkRIwDmc/HB3zb/U+ZCoC+BBHshBEDfJLA+BKITSLCjWBIi+5D5cHbRbJsqyjgEKuslwZgKX97KthnC7U3AXztb74ZGayAvb0fDMnBHfjmSbeBuaB4C3QlMJwCGPSvpToQ1IQCBQQlU8tX3wZ8fSRp0S9q+cf5qT2A6AcBZSftssQYECiBQyVffB3+LgAIyRgilEphOAJRKlLggAIEBCWQzfuCDv0XAgCxoeoMAU10IIAC6UGOd2glMcBKbzYFv4G1jAvTdIvK+1dZt7WRrsd0kQ1lgQwE20AKpEhIEkhPI5sCXPHIa7EOgju2mD6Ga10UA1Jz9gLFzvhIwKbgUlgDfl2CpySwhCIBg20/t7nC+UvsWQPxtCPB9Ma1AlllCEACBth1cgQAEUhPI7JQsdfi0B4ElBBAAS+DwEQQgkDuBzE7Jcsc9gf902Z0AAqA7O9aEAAQgAAEIZEsAAZBt6nAcAhCAQO0EiL8PAQRAH3qsCwEIpCPA5fp0LGkJAg0IIAAaQGIRCEBgBAJcrh8BclldEE0/AgiAfvwmWptTpYnA0y0EIACBYgggALJMJadKWaYNpyEAgYQEaKovAQRAX4KsDwEIQAACLQgwgtkC1qCLIgAGxUvjhRJgCKbQxBLWGATSfH3G8LT0PhAApWeY+CBQGwFOMGvLOPF2JIAA6AiO1aol4NMXW7UAwgdOdsKnqL+DtJCCAAIgBUXaqI0Ah5jaMk68ECiQAAKgwKQS0uAEEACDI6YDCCwmwCdpCCAA0nCklXoI+OBvqydiIoUABAIRSHeTCwIgUFpxBQIQgAAEVhGo/fN05x8IgNq3JeLvQiDdN7BL76wDAQhAIAEBBEACiDQxAIF0o1ypnfPB35a6XdqDAAQaEGCRdAQQAOlY0lJKAoMfYnspjMG9S4mStiDQjUCv70i3LllrVAIIgFFx01kcAhzD4+RieE84lHVhHPE70iUO1llEAAGwiAzzIbCYAHvGxWxCfkLCQqYFpyYmgACYOAF0nx0BjiXZpQyHSyFAHGkJIADS8qQ1CEAAAhCAQBYEEABZpAkngxE4PZg/uAOBCggQYmoCCIDURGmvBgJcBqghy8QIgcIJIAAiJJhblCNkoakPPvifMSNnTXmxHASSEAjdSKb7AwRAhK3qjAhONPUh0y29aXjNljtjllXOmgUVbik2tXApwaEFBDLdHyAAFuRz82z2Q5tpZLqlbw6B6TwIsKnlkadRvKSTIQggABpQZT/UABKLQAACEIBAVgQQAFmlC2cDELAetAVwBRcgUAcBohyGAAJgGK60CgEIQAACEAhNAAEQOj04F5QAIwBBE4NbJRIgpqEIIACGIku7JRPgRUAlZ5fYIFAJAQRAJYkmzGQEOPtPhpKGILCaAEsMRwABMBxbWoYABCAAAQiEJTCeAOBh+rAbQXTHAm46jAJE32jwrxAChDEkgfEEALvMIfNYdNvBNh27YyuaOcFBAALlExhPAJTPkgjrIYAAqCfXRDohAboelgACYFi+tF4mAQRAmXklqlIJBLyOGAE1AiBCFvAhNwIIgNwyhr8ZEkjoMt/YuTARAHOxMBMCEIAABCBQNgEEQNn5Jbr0BLadSzCmmB4tLUJggwBTwxNAAAzPmB7KIyARoNI5LsRDZ3SsCAEIJCOAAEiGkoYqItDn6C9MPVdXCxQIlE2A6MYggAAYgzJ9lETAR29bSTERCwQgUCEBBECFSSfk3gR6CYBUFwBStdObBg1AIDEBmhuHAAJgHM70AoGzCPRSD2e1Mpv1bgcFsYkmkxCojwACoL6cE/EOBFoeB33cte3QSoZ/lhFFhuBxeTkBPh2LAAJgLNL0E5ZAh+Ngh1WmDr+lzJnaXfqHAAQGJ4AAGBwxHUAgAoEMNUsEbPiwmMBAmnJxh3ySmgCJ43mMAAAO70lEQVQCIDVR2quBAEfTGrJMjMsJ8C1YzieDTxEAGSQJF8MRYNcXLiU4VAYBohiTQPUCgFGsMTe3Ivrywd9WRDAEAQEI1EugegHAnrzejZ/IIQCBWATwZlwC1QuAcXHTWyEE0I2FJJIwIFAzAQRAzdkn9i4EfPC3dVmXdSAAgYUE+GBsAgiAsYnTXwkEEAAlZJEYIFA5AQRA5RsA4XcigADohI2VILCYAJ+MTwABMD7zlj3ynEJLYEMvzsF/aMK0P4cA+4E5UJjVkwACoCfA4VfneDM8Y3qAQHQCpe8HovMv0z8EQJl5JaphCbA3HpYvrUMAAiMQQACMADm/LhhuXJEzBMAKQHwMgTYEWi3L7qkVrmULIwCW0an2M45vS1JvOLYli/ARBCAwGAG+fcnQIgCSoaShigiwC6oo2XFCLfXUNw7h2jxBANSWceJNQQABkIIibbQkwGbXEhiLryCAAFgBiI8hAAEIQGA4ArQ8HQEEwHTs6TlPAj4Ns+XpPV5DAAJLCdR0oWUiAVAT4qXbGh/mSWCJAGDbzjOleD0NgXi9Lvlyx3O2p0cTCYCaEPfMEKtnRoBtO7OE4S4EqiUwkQColjeBl0GAo3wZeSSKiQnQ/bQEEADT8qf3/Ahw8M8vZ3gMgU4ESr+ghwDotFmwEgQgAAEI9CMQf+3S1T4CIP42iIcQgAAEIACB5AQQAMmR0mDhBEo/KSg8fYQXhQB+TE8AATB9DvAAAhCAAAQgMDoBBMDoyOkQAhCAQO0EiD8CAQRAhCzgQ04EuASQU7bwFQIQWEgAAbAQDR9AAAIQKI9AhEfbyqOaZ0QIgDzzhtcQgAAEOhFgCKsTtiJXQgAUmVaCggAE4hDgnHv7XPBXFAIIgCiZwA8IQKBQApxzF5rY7MNCAGSfQgIYmUB5e3NOUEfehOrurojoC/nOIACK2BoJAgI9CJQnaXrAYFUINCBQyHcGAdAg1ywCAQhAAAIpCNBGJAIIgEjZwJccCBSi/XNAHdHHQsZ+I6LFp9EJIABGR06HEIBAvgTQf31yx7qxCCAAYuUDbyBQJwFOrOvMO1FPSgABMCl+Os+QAKeAQyQNqkNQDdYm7kQjgACIlhH8gQAEIAABCIxAAAEwAmS6gAAEIFA7AeKPRwABEC8n2XrEZdxsU4fjEIBAhQQQABUmfaiQuYw7FFnahUDuBPA/IgEEQMSs4FNkAms6h+GOyDnCNwhAoAEBBEADSCwCgS0E1mTAltnMgAAEthJgTkwCCICYecErCPQmwCBFb4Q0AIGiCSAAik5vouA4kiQCOW4zDFKMy7um3trtEmoik1esCIC88jWNtxxJNnOHxmYaTFdJgC9BGWlHAJSRR6IYjwD7vvFY01MBBAghLgEEQNzc4BkEIAABCEBgMAIIgMHQ0vBcAvlfPGQEYG5imQmBeQSYF5kAAiBydkr0Lf/DZ/4RlLhdERMEINCaAAKgNTJWgAAEIACBJgRYJjYBBEDs/OBdPAKMAMTLCR5BAAIdCCAAOkAbeBXnxFfKXddqRuzYzcHTEc3+1W4R8xLJJ28f9sd1hTZzzP4Or9dmgQUi4MQEcqd6V84lAreR7YnNbisGl5JFK7vJoZvIyNFsdmtx2FlG2Urg/Jp1PZkZ1byt3E4MvE+7gmpKMAIIgFgJ8cHl3XLpKNmRFdsHFfsRsr+SRSveqX9MTtWcn/XYPyQO55ZRthLwAe8Fmm1G67yqqhX7erzv1fT9ZZRgBBAAwRKCOxCAAAQgAIExCCAAxqBMHxCAQAUEfLm7gjAbhchCORBAAEyZJfYXU9KnbwgkJsADIomB0tzABBAAAwNe2jz7i6V4+BACEMiTAF7nQQABkEee8BICEIAABCCQlAACIClOGoMABMYkUPZVtImi693tmFtABX0NmA8EQAXbDyFCYEgCA+6fVrpd9lW0iaKbqNuVya51gQHzgQCodaMibggkIjDg/imRhzQzJgH6yocAAiCfXOEpBCBQDYEpx1WqgVx9oAiA6jcBAEAAAvEI5DquEo8kHi0mgABYzIZPIAABCLQjwIl7O14sPSkBBMCk+OkcAhAoikDlJ+5F5bKCYBAAFSSZECEAAQhAAAI7EkAA7EiEvyEAAQhAoAMBVsmNAAIgt4yt+8u1xnUS1BCAAAQg0IEAAqADtBCrcK0xRBpwAgIbBOpW5RscmMqFAAIgl0zhJwQgEJwAqjx4gsK4F0UqIgDCbBI4AgEIQCBXAvjdhkAUqYgAaJM1loUABDYIRDmN2fCIKQhAoAUBBEALWCzahQBHiS7UslgnymlMFrDKdpLo8iSAAMgzbxl5zVEio2ThKgQgUBEBBEBFySZUCEAAAukJ0GKuBLITAAwo57qpjed3322k7/rjRUpPEIAABLoTyE4AMKDcPdm1rNl3G+m7fi2ciRMCJoDlSyA7AZAvajyHAAQgYAKMMZkCNj0BBMD0OcADCECgKgIljTFVlbjigkUAFJdSAoLACAQ4iR0BMl1AYFgCCIBh+dI6BMokwElsmXltGRWL500AAZB3/vAeAhCAAAQg0IkAAqATNlaCAAQgUDsB4s+dAAIg9wziPwSKJcCNBsWmlsBCEEAAhEgDTkAAAlsJcKPBViZx5uBJ/gQQAPnnkAggAAEIQAACrQkgAFojYwUIQAACtRMg/hIIIABKyCIxQAACEIAABFoSQAC0BMbi4xDg9q9xONfdC1tZ1/yzXhkEEABl5LG4KLj9q7iUBgyIrSxgUnBpRAIIgBFh0xUEIACB/AkQQSkEEAClZJI4IAABCEAAAi0IIABawGJRCEAAArUTIP5kBCa/BjW1ADhdKH8no0AAAhCYnAC3BU6eglocODlCoFMLgNMEIQQI+UGBAAQqJzD5KVl4/jiYiECI497UAuBUwTxJRoEABCAAAQjUQuD3EQKdWgB4+P+4CCDwAQIQgAAElhPg0yQEfNL72yQtLWyk2cWsqQXAifL/GBkFAhCAAAQgUB6Brcfi7ypIiwBVQ5VmF7OmFgBWQYYxFAXahQAEIACBJARopBOBrcdin/RyD8A2mMeqthBQRYEABCAAAQgUTeCriu6XssnL1CMABvAz/fd5GQUCEIAABIISwK1kBD6rlk6QTV4iCIDjRcFAVFEgAAEIQAACYxPYeqF+IA9+rnZ9CUDV9CWCADCQT02PAg/mEhjtezG3d2ZCAAIhCJTuxNYL9QNF/FG168veqqYvEQSAKXxT/31ZRolGYLTvRbTA8QcCKwggjlcA4uM5BI7QvB/LQpQoAuD7ovFeGQUC8wmws53PhbnTEahIHE8Huaief6RofKLrN+BqcvoSRQD8Sij+TfZrGQUCWwmws93KhDkQgEBOBA6Xs6Eee48iAMRl9jX9d5gsYeG0MSFMmoIABKokQNAJCPixv/epHdeqYpRIAsCPA75HWBK+E4DTRvEsvCDyCk8w4UGgBAKHKgif5KqKUyIJAFPx+wAO8oSMo7cgUFYRYDNZRYjPExKoUG8mpFdrU37s7x0KPtTZv/yZRRMABvQ2OfYVGV81QaBAAAKBCKA3AyUjG1cOlKdflIUr0QSAAfkuyRd5AoMABCAAgSkJ0HdPAu/X+h+QnSLrVwY4JY4oAPyIhKEhAvptLqwNAQhAAALTEfDj7T6Oue7vxQCjTxEFgEH5UsDrNHGUzGWA0N0sBgEIQAACiwgwvzOBP2jNp8n+Uxa2RBUABvYt/fcsmW8M9OAHIkAwKBCAAAQgEJ7AU+Whn2qzENBkzBJZAJjYZ/TfE2TrNwUiAgSDAgEIQGB4AvTQkcBztd4hspNkoUt0AWB4/vEEi4Cv6g9GAgSBAgEIQAACIQkcIK9eKfNlbFWxSw4CwGf9/yqMj5R9TGYRoIoCAQhAAAJDEaDdRgR8fPKCHup/oiZeIjtelkXJQQAYpCH74P8Y/fFWGQUCEIAABCAwNQGfkP6fnNhH5pfYnaA6m5KLAFgH6pcpPFl/WGn9QjUFAhCAAASSE6DBhgTeq+V88H+L6vDX/OXjdiU3AWDn/UzlKzRxP5nhq6JAAAIQgAAERiNwrHryY35/r/ojMl8CUJVXyVEAmPAps9lOfkeAbw7829ls5qcEVFEgAAEIQKAvAdZfSMA/Vuc7/H0C+jIt9R1ZtiVXASDgvi1g9m1NvEb2YNljZf8lo0AAAhCAAARSEvi5GvsH2V6yZ8g+LDtZlnXJWACcxd2vDvb7Al6tOfvK7i97rex7svnFt23M/4S5EIAABConQPibCHxK0x7qv5fq/WV+r/9xqosoJQiA9URYCHxJf/hmjGeqfoDMguBg1Z+UbTyXeebggeZQIAABCEAAAmsETlf1Ddm7ZD7o3021Hz/3o31Hazqbx/vka6NSkgDYHPBP9MfHZR4J8OuEH6FpD93cU/WjZS+Q+dLBG1W/XeabCbHZLBQDDdSE8mcWjA/+zNg+BtgmZ+W36Vf0Hq44fXzwS3v82l6fMN5Z8x4k20/2YpmX85Nnv9N0kaVUAbA5WR6u+bJm+JrNO1U74c9X7VECq7wnado3E/puTmw2C8NAAzVhfNE2gi+Btg3yEed7mmEuvL/34+S+lv9s+e8z/DerPkLmH+/x5eNTNF18qUEAzEvirzXTj3H8SPUxMt9M6Ls5sdkMBjBgG6h2G6ji++8X9/xA+30fA3xzXxUHe8W7pdQqALaAYAYEIAABCECgJgIIgJqyTawQgAAElhDgo7oIIADqyjfRQgACEIAABM4kgAA4EwP/QQACEKidAPHXRgABUFvGiRcCEIAABCAgAggAQehbdurbAOtDoEQCfDGyyirO1kcAAZAg52ckaIMmIFAcgaVfDNRBcfkmoOwIIACySxkOQ6AEAkvVQZ4BZq1p8kSO1/0IIAD68WNtCEAAAmsECtQ0a4Hxf6kEEAClZpa4IAABCDQkwGJ1EkAA1Jl3ooYABCAAgcoJIAAq3wAIHwKhCXBdfYT00EWtBBAAtWaeuCGQAwGuq+eQJXzMlAACINPE4XYUApyiRskEfnQjwFr1EkAA1Jt7Ik9CgFPUJBhpBAIQGJ0AAmB05HQIAQhAIAoB/KiZAAKg5uwTOwQgAAEIVEsAAVBt6gl8TALcKTAmbfpqSoDl6ibw/wAAAP//cH3DvAAAAAZJREFUAwD4rOaY0yK+PgAAAABJRU5ErkJggg=="

            # Ancho del icono en píxeles
            icon_width = 28

            # HTML para mostrar el texto y el icono
            link_html = f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-top: 8px;">
                <span style="font-size: 0.95rem;">Sígueme en:</span>
                <a href="{linkedin_url}" target="_blank" title="Mi perfil de LinkedIn">
                    <img src="{linkedin_icon_base64}" alt="LinkedIn Logo" width="{icon_width}" height="{icon_width}" style="vertical-align: middle;">
                </a>
            </div>
            """

            # Usar st.markdown para renderizar el HTML
            st.markdown(link_html, unsafe_allow_html=True)
            st.empty()
            st.markdown("---")
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


