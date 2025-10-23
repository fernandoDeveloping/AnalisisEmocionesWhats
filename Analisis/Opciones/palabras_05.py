import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.corpus import stopwords
from collections import Counter
import string
import emoji # Necesitarás: pip install emoji
from wordcloud import WordCloud # Necesitarás: pip install wordcloud

# Descargar stopwords de NLTK (solo la primera vez)
# Usamos un cache de recursos para esto
@st.cache_resource
def descargar_stopwords():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

# Función para configurar el estilo de los gráficos
def configurar_grafico_palabras():
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rc('figure', figsize=(10, 6))
    plt.rc('font', size=12)
    plt.rc('axes', titlesize=16, labelsize=14)
    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)

@st.cache_data
def analizar_palabras_y_emojis(_df_chat):
    """
    Opción 5: Analiza las palabras y emojis más comunes.
    """
    st.subheader("Palabras y Emojis Más Usados 🗣️")
    
    # Asegurar que los stopwords estén descargados
    descargar_stopwords()

    if _df_chat.empty:
        st.warning("No hay datos de chat para analizar.")
        return

    # Combinar todos los mensajes en un solo texto
    texto_completo = ' '.join(_df_chat['Mensaje']).lower()

    # --- 1. Análisis de Palabras ---
    st.markdown("#### Palabras Más Comunes (excluyendo artículos y conectores)")

    # Definir stopwords en español y añadir palabras comunes de chat
    stop_words_es = set(stopwords.words('spanish'))
    stop_words_chat = {
        'que', 'qué', 'con', 'para', 'pero', 'por', 'del', 'los', 'las', 'como', 'cómo',
        '<multimedia', 'omitido>', 'audio', 'jaja', 'jajaja', 'sticker', 'ok', 
        'vale', 'si', 'no', 'ya', 'así', 'va', 'dos', 'ser', 'es', 'está', 'https',
        'http', 'www', 'com', 'message', 'deleted'
    }
    stop_words_total = stop_words_es.union(stop_words_chat)

    # Limpiar el texto de puntuación
    texto_limpio = texto_completo.translate(str.maketrans('', '', string.punctuation + '¿¡'))
    
    # Filtrar palabras
    palabras_filtradas = [
        p for p in texto_limpio.split() 
        if p not in stop_words_total and len(p) > 2 and not p.isdigit()
    ]
    
    if not palabras_filtradas:
        st.info("No se encontraron palabras significativas para analizar.")
        return

    # Generar Nube de Palabras
    st.markdown("##### Nube de Palabras")
    try:
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white', 
            colormap='viridis',
            stopwords=stop_words_total
        ).generate(' '.join(palabras_filtradas))

        fig_wc, ax = plt.subplots(figsize=(12, 6))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig_wc)
    except Exception as e:
        st.error(f"Error al generar la nube de palabras: {e}")
        # Mostrar un gráfico de barras como alternativa
        st.markdown("##### Top 20 Palabras (Gráfico Alternativo)")
        conteo_palabras = Counter(palabras_filtradas).most_common(20)
        df_palabras = pd.DataFrame(conteo_palabras, columns=['Palabra', 'Frecuencia'])
        configurar_grafico_palabras()
        fig_bar, ax_bar = plt.subplots()
        sns.barplot(data=df_palabras, y='Palabra', x='Frecuencia', ax=ax_bar, palette='viridis')
        st.pyplot(fig_bar)


    # --- 2. Análisis de Emojis ---
    st.markdown("#### Emojis Más Usados")
    
    emojis_encontrados = []
    for char in texto_completo:
        if emoji.is_emoji(char):
            emojis_encontrados.append(char)
            
    if not emojis_encontrados:
        st.info("No se encontraron emojis en esta conversación.")
        return

    # Contar y mostrar los emojis
    conteo_emojis = Counter(emojis_encontrados).most_common(15)
    df_emojis = pd.DataFrame(conteo_emojis, columns=['Emoji', 'Frecuencia'])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("##### Conteo de Emojis")
        # st.dataframe es excelente para mostrar emojis
        st.dataframe(df_emojis, use_container_width=True)
    
    with col2:
        st.markdown("##### Gráfico de Emojis")
        # st.bar_chart maneja bien los índices de texto (emojis)
        df_chart_emojis = df_emojis.set_index('Emoji')
        st.bar_chart(df_chart_emojis)
