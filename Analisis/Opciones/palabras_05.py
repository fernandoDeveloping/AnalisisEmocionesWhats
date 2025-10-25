import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
from nltk.corpus import stopwords
from collections import Counter
import string
import emoji # ¡Importante! Asegúrate de que esta línea esté activa
from wordcloud import WordCloud 

# Descargar stopwords de NLTK (solo la primera vez)
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
    Opción 5: Analiza las palabras y emojis más comunes (global y por contacto).
    """
    st.subheader("Palabras y Emojis Más Usados 🗣️")
    
    # Asegurar que los stopwords estén descargados
    descargar_stopwords()

    if _df_chat.empty:
        st.warning("No hay datos de chat para analizar.")
        return

    # Combinar todos los mensajes en un solo texto (para análisis global)
    texto_completo = ' '.join(_df_chat['Mensaje']).lower()

    # --- 1. Análisis de Palabras (Global) ---
    st.markdown("#### Palabras Más Comunes (excluyendo artículos y conectores)")

    # (Tu código de stopwords y limpieza... se mantiene igual)
    stop_words_es = set(stopwords.words('spanish'))
    stop_words_chat = {
        'que', 'qué', 'con', 'para', 'pero', 'por', 'del', 'los', 'las', 'como', 'cómo',
        '<multimedia', 'omitido>', 'audio', 'jaja', 'jajaja', 'sticker', 'ok', 
        'vale', 'si', 'no', 'ya', 'así', 'va', 'dos', 'ser', 'es', 'está', 'https',
        'http', 'www', 'com', 'message', 'deleted'
    }
    stop_words_total = stop_words_es.union(stop_words_chat)
    texto_limpio = texto_completo.translate(str.maketrans('', '', string.punctuation + '¿¡'))
    palabras_filtradas = [
        p for p in texto_limpio.split() 
        if p not in stop_words_total and len(p) > 2 and not p.isdigit()
    ]
    
    if not palabras_filtradas:
        st.info("No se encontraron palabras significativas para analizar.")
        # No retornamos aquí, aún puede haber emojis
    else:
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


    # --- 2. Análisis de Emojis (Global) ---
    st.markdown("--- \n #### Emojis Más Usados (Global)")
    
    # Usamos la misma lógica que tenías para el análisis global
    emojis_encontrados_global = []
    for char in texto_completo:
        if emoji.is_emoji(char):
            emojis_encontrados_global.append(char)
            
    if not emojis_encontrados_global:
        st.info("No se encontraron emojis en esta conversación.")
        return # Si no hay emojis en total, no podemos analizar por contacto

    # Contar y mostrar los emojis globales
    conteo_emojis_global = Counter(emojis_encontrados_global).most_common(15)
    df_emojis_global = pd.DataFrame(conteo_emojis_global, columns=['Emoji', 'Frecuencia'])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("##### Conteo Global de Emojis")
        st.dataframe(df_emojis_global, use_container_width=True)
    
    with col2:
        st.markdown("##### Gráfico Global de Emojis")
        df_chart_emojis = df_emojis_global.set_index('Emoji')
        st.bar_chart(df_chart_emojis)

    # --- 3. ANÁLISIS POR CONTACTO (NUEVO) ---
    st.markdown("--- \n #### Análisis de Emojis por Contacto")

    autores = _df_chat['Autor'].unique()
    resultados_autores = []

    for autor in autores:
        # 1. Filtrar mensajes del autor
        df_autor = _df_chat[_df_chat['Autor'] == autor]
        
        # 2. Unir todos sus mensajes
        texto_autor = ' '.join(df_autor['Mensaje'])
        
        # 3. Encontrar todos los emojis de ESE autor
        emojis_autor = []
        for char in texto_autor:
            if emoji.is_emoji(char):
                emojis_autor.append(char)
        
        total_emojis = len(emojis_autor)
        
        # 4. Encontrar el emoji favorito
        if total_emojis == 0:
            emoji_favorito = "N/A"
            conteo_favorito = 0
        else:
            conteo = Counter(emojis_autor).most_common(1)
            emoji_favorito = conteo[0][0]
            conteo_favorito = conteo[0][1]
            
        # 5. Guardar resultados
        resultados_autores.append({
            'Autor': autor,
            'Total Emojis': total_emojis,
            'Emoji Favorito': emoji_favorito,
            'Veces Usado': conteo_favorito
        })

    # Convertir a DataFrame para mostrarlo
    df_autores = pd.DataFrame(resultados_autores)
    
    # Ordenar para ver quién usó más emojis en total
    df_autores = df_autores.sort_values(by='Total Emojis', ascending=False)
    
    # --- Mostrar Resultados por Contacto ---
    
    # 1. "Quién usa más emojis"
    autor_top = df_autores.iloc[0]
    st.metric(
        label=f"👑 Rey/Reina de los Emojis",
        value=autor_top['Autor'],
        help=f"{autor_top['Autor']} usó {autor_top['Total Emojis']} emojis en total."
    )
    
    # 2. "Cuál es el emoji que más usa por contacto"
    st.markdown("##### Resumen de Emojis por Contacto")
    st.dataframe(
        df_autores.set_index('Autor'),
        use_container_width=True
    )