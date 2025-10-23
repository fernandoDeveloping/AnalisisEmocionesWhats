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
from Utils.Metodos import cargar_modelo_emociones


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