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