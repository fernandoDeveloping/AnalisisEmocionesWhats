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
from Utils.Metodos import cargar_modelo_sentimientos


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