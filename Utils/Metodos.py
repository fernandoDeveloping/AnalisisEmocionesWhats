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
        nltk.download('stopwords')

descargar_nltk_stopwords()

# --- Funciones de Carga y Cache de Modelos de IA ---

@st.cache_resource
def cargar_modelo_emociones():
    """
    Carga y cachea el modelo de EMOCIONES.
    _resource se usa para objetos complejos (como modelos) que no deben ser serializados.
    """
    return create_analyzer(task="emotion", lang="es")

@st.cache_resource
def cargar_modelo_sentimientos():
    """
    Carga y cachea el modelo de SENTIMIENTOS (Pos/Neg/Neu).
    """
    return create_analyzer(task="sentiment", lang="es")

# --- Funciones de Procesamiento de Datos (Cacheadas) ---
