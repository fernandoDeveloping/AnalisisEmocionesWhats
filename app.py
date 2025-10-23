import streamlit as st
import pandas as pd
import re
import io
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.corpus import stopwords
from collections import Counter
import string
import os

# --- Importaciones de Modelos de IA ---
# Importamos la función 'create_analyzer' que usaste
from pysentimiento import create_analyzer

# --- Configuración Inicial (Solo se ejecuta una vez) ---

# Deshabilitar logs de 'wandb'
os.environ["WANDB_DISABLED"] = "true"

# Descargar las 'stopwords' de NLTK (palabras de relleno)
@st.cache_data
def descargar_nltk_stopwords():
    """Descarga stopwords de NLTK si no están presentes."""
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        st.info("Descargando recursos de lenguaje (stopwords)...")
        nltk.download('stopwords')

descargar_nltk_stopwords()

# --- Funciones de Carga y Cache de Modelos de IA ---

@st.cache_resource
def cargar_modelo_emociones():
    """
    Carga y cachea el modelo de EMOCIONES.
    _resource se usa para objetos complejos (como modelos) que no deben ser serializados.
    """
    st.info("Cargando modelo de análisis de emociones (solo la primera vez)...")
    return create_analyzer(task="emotion", lang="es")

@st.cache_resource
def cargar_modelo_sentimientos():
    """
    Carga y cachea el modelo de SENTIMIENTOS (Pos/Neg/Neu).
    """
    st.info("Cargando modelo de análisis de sentimientos (solo la primera vez)...")
    return create_analyzer(task="sentiment", lang="es")

# --- Funciones de Procesamiento de Datos (Cacheadas) ---

@st.cache_data
def procesar_chat(uploaded_file):
    """
    Toma un archivo subido (zip o txt) y lo convierte en un DataFrame.
    Esta función se cachea. Si se sube el mismo archivo, no se reprocesa.
    """
    
    # 1. Leer el archivo desde memoria
    try:
        content_bytes = uploaded_file.getvalue()
        
        # Lógica para .zip
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(content_bytes), 'r') as zip_ref:
                for file_in_zip in zip_ref.namelist():
                    if file_in_zip.endswith('.txt') and not file_in_zip.startswith('__MACOSX'):
                        with zip_ref.open(file_in_zip) as txt_file:
                            content_bytes = txt_file.read()
                            break # Usar el primer .txt encontrado
        
        # Decodificar y separar en líneas
        # Usamos .splitlines() para manejar saltos de línea
        content_str = content_bytes.decode('utf-8')
        lines = content_str.splitlines()

    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame(columns=['Timestamp', 'Autor', 'Mensaje'])

    # 2. Lógica de Parseo (Tu código original)
    patron_inicio = re.compile(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?:[\s\u202f]*(?:a\.[\s\u202f]*m\.|p\.[\s\u202f]*m\.))?)\s*-\s*'
    )
    datos = []
    mensaje_actual_buffer = None

    for linea in lines:
        match = patron_inicio.match(linea)
        if match:
            if mensaje_actual_buffer:
                datos.append(mensaje_actual_buffer)
            
            timestamp_str = match.group(1)
            resto_linea = linea[match.end():].strip()
            partes_autor_msg = resto_linea.split(':', 1)
            
            if len(partes_autor_msg) == 2:
                mensaje_actual_buffer = {
                    "Timestamp": timestamp_str,
                    "Autor": partes_autor_msg[0],
                    "Mensaje": partes_autor_msg[1].strip()
                }
            else:
                mensaje_actual_buffer = None
        elif mensaje_actual_buffer:
            mensaje_actual_buffer["Mensaje"] += " " + linea.strip()

    if mensaje_actual_buffer:
        datos.append(mensaje_actual_buffer)

    if not datos:
        return pd.DataFrame(columns=['Timestamp', 'Autor', 'Mensaje'])

    # 3. Crear y Limpiar DataFrame
    df = pd.DataFrame(datos)
    df['Timestamp'] = df['Timestamp'].str.replace(r'a\.[\s\u202f]*m\.', 'AM', regex=True)
    df['Timestamp'] = df['Timestamp'].str.replace(r'p\.[\s\u202f]*m\.', 'PM', regex=True)
    df['Timestamp'] = df['Timestamp'].str.replace('\u202f', ' ', regex=False) 

    # Conversión de fecha robusta
    formats_to_try = [
        '%d/%m/%Y, %I:%M %p',
        '%d/%m/%Y, %H:%M',
        '%d/%m/%y, %I:%M %p',
        '%d/%m/%y, %H:%M'
    ]
    for fmt in formats_to_try:
        try:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], format=fmt)
            break
        except ValueError:
            continue
            
    df = df[~df['Mensaje'].str.contains(r"<Multimedia omitido>|Se eliminó este mensaje|ubicación: http", na=False, case=False, regex=True)]
    df['Mensaje'] = df['Mensaje'].str.strip()
    df = df[df['Mensaje'].str.len() > 0]
    
    return df

# --- Funciones de Análisis (Opciones del Menú) ---

@st.cache_data
def mostrar_analisis_conversacion(_df_chat):
    """
    Opción 1: Muestra mensajes por autor y genera un gráfico.
    El _df_chat es un parámetro "hashable" para la caché.
    """
    st.subheader("Análisis de Autores")
    
    if _df_chat.empty:
        st.warning("El chat está vacío o no contiene mensajes válidos.")
        return

    # Estadística básica
    mensajes_por_autor = _df_chat['Autor'].value_counts()
    st.write("Total de Mensajes por Autor:")
    st.dataframe(mensajes_por_autor)

    # Gráfico simple
    st.write("--- Gráfico de mensajes por autor ---")
    fig, ax = plt.subplots(figsize=(10, max(6, len(mensajes_por_autor) * 0.5)))
    sns.countplot(y=_df_chat['Autor'], order=mensajes_por_autor.index, palette="viridis", ax=ax)
    ax.set_title('Número de Mensajes por Autor')
    ax.set_xlabel('Cantidad de Mensajes')
    ax.set_ylabel('Autor')
    plt.tight_layout()
    st.pyplot(fig) # Usamos st.pyplot() en lugar de plt.show()

@st.cache_data
def analizar_emociones(_df_chat):
    """
    Opción 2: Procesa el chat, analiza las emociones y genera un gráfico.
    """
    st.subheader("Análisis de Emociones")

    if _df_chat.empty:
        st.warning("No se encontraron mensajes válidos para analizar.")
        return

    st.write(f"Se analizarán {len(_df_chat)} mensajes...")

    # Cargar el modelo (lo tomará de la caché si ya existe)
    emotion_analyzer = cargar_modelo_emociones()

    # Predecir las emociones
    resultados = emotion_analyzer.predict(_df_chat['Mensaje'].tolist())
    emociones_predichas = [r.output for r in resultados]
    
    conteo_emociones = pd.Series(emociones_predichas).value_counts()

    # Filtrar por las 5 emociones deseadas
    emociones_deseadas = ['joy', 'sadness', 'anger', 'fear', 'surprise']
    conteo_filtrado = conteo_emociones.reindex(emociones_deseadas, fill_value=0)

    traducciones = {
        'joy': 'Alegría 😊',
        'sadness': 'Tristeza 😢',
        'anger': 'Enojo 😠',
        'fear': 'Miedo 😱',
        'surprise': 'Sorpresa 😮'
    }
    conteo_grafico = conteo_filtrado.rename(index=traducciones)
    colores = ['#FFD700', '#4169E1', '#DC143C', '#8A2BE2', '#FF8C00']

    # Generar el gráfico
    st.write("--- Gráfico de distribución de emociones ---")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=conteo_grafico.index, y=conteo_grafico.values, palette=colores, ax=ax)
    ax.set_title('Distribución de 5 Emociones en el Chat', fontsize=16)
    ax.set_xlabel('Emoción', fontsize=12)
    ax.set_ylabel('Cantidad de Mensajes', fontsize=12)
    st.pyplot(fig)

@st.cache_data
def analizar_compatibilidad(_df_chat):
    """
    Opción 3: Analiza la compatibilidad entre los dos principales autores.
    """
    st.subheader("Análisis de Compatibilidad")

    if _df_chat.empty:
        st.warning("No se encontraron mensajes válidos para analizar.")
        return

    autores_counts = _df_chat['Autor'].value_counts()
    if len(autores_counts) < 2:
        st.error(f"Se necesitan al menos 2 autores para un análisis de compatibilidad.")
        return
        
    autor_1 = autores_counts.index[0]
    autor_2 = autores_counts.index[1]
    
    st.write(f"Analizando compatibilidad entre: **{autor_1}** y **{autor_2}**...")

    df_autor_1 = _df_chat[_df_chat['Autor'] == autor_1]
    df_autor_2 = _df_chat[_df_chat['Autor'] == autor_2]
    count_1 = len(df_autor_1)
    count_2 = len(df_autor_2)

    # Cargar modelo (de la caché) y stopwords
    sentiment_analyzer = cargar_modelo_sentimientos()
    stop_words_es = set(stopwords.words('spanish'))

    # --- MÉTRICA 1: Vibra Positiva ---
    resultados_sent = sentiment_analyzer.predict(_df_chat['Mensaje'].tolist())
    sentimientos = [r.output for r in resultados_sent]
    conteo_sent = pd.Series(sentimientos).value_counts(normalize=True)
    vibra_positiva = conteo_sent.get('POS', 0) * 100

    # --- MÉTRICA 2: Balance de Charla ---
    balance_charla = (min(count_1, count_2) / max(count_1, count_2)) * 100

    # --- MÉTRICA 3: Sincronía Emocional ---
    sent_1 = sentiment_analyzer.predict(df_autor_1['Mensaje'].tolist())
    sent_2 = sentiment_analyzer.predict(df_autor_2['Mensaje'].tolist())
    prop_pos_1 = [r.output for r in sent_1].count('POS') / count_1 if count_1 > 0 else 0
    prop_pos_2 = [r.output for r in sent_2].count('POS') / count_2 if count_2 > 0 else 0
    
    if max(prop_pos_1, prop_pos_2) == 0:
        sincronia_emocional = 100.0
    else:
        sincronia_emocional = (min(prop_pos_1, prop_pos_2) / max(prop_pos_1, prop_pos_2)) * 100

    # --- MÉTRICA 4: Intereses Comunes ---
    def limpiar_y_contar(lista_mensajes):
        texto_completo = ' '.join(lista_mensajes).lower()
        texto_sin_punc = texto_completo.translate(str.maketrans('', '', string.punctuation + '¿¡'))
        palabras = texto_sin_punc.split()
        palabras_filtradas = [
            p for p in palabras 
            if p not in stop_words_es and not p.isdigit() and len(p) > 2
        ]
        return set([p[0] for p in Counter(palabras_filtradas).most_common(25)])

    top_palabras_1 = limpiar_y_contar(df_autor_1['Mensaje'])
    top_palabras_2 = limpiar_y_contar(df_autor_2['Mensaje'])

    interseccion = top_palabras_1.intersection(top_palabras_2)
    union = top_palabras_1.union(top_palabras_2)
    
    intereses_comunes = (len(interseccion) / len(union)) * 100 if len(union) > 0 else 0

    # --- Graficar ---
    st.write("--- Medidor de Compatibilidad ---")
    data = {
        'Métrica': [
            'Intereses Comunes 🗣️', 
            'Sincronía Emocional 😊', 
            'Balance de Charla ⚖️', 
            'Vibra Positiva General 💖'
        ],
        'Puntaje (%)': [
            intereses_comunes, 
            sincronia_emocional, 
            balance_charla, 
            vibra_positiva
        ]
    }
    df_compat = pd.DataFrame(data).set_index('Métrica').sort_values('Puntaje (%)', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    # Usamos 'color' para el tono rosado
    df_compat['Puntaje (%)'].plot(kind='barh', ax=ax, color='#FFB6C1', xlim=(0, 100))
    ax.set_title(f'Compatibilidad entre "{autor_1}" y "{autor_2}"', fontsize=16)
    ax.set_xlabel('Puntaje (0-100)', fontsize=12)
    ax.set_ylabel('')
    
    # Añadir etiquetas de valor
    for i, (index, row) in enumerate(df_compat.iterrows()):
        ax.text(
            row['Puntaje (%)'] + 1, 
            i, 
            f'{row["Puntaje (%)"]:.1f}%', 
            color='black', va='center'
        )
    
    st.pyplot(fig)

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