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
import numpy as np # Importar numpy para los gradientes

# --- FUNCIÓN AUXILIAR ---
# (Es mejor tener esta lógica fuera de la función principal)

def _limpiar_y_contar_palabras(lista_mensajes, stop_words_es):
    """
    Limpia una lista de mensajes y devuelve un set con las 25 palabras más comunes.
    """
    if not lista_mensajes:
        return set()
        
    texto_completo = ' '.join(lista_mensajes).lower()
    # Eliminar URLs
    texto_completo = re.sub(r'http\S+', '', texto_completo)
    # Eliminar menciones y hashtags (común en otros chats)
    texto_completo = re.sub(r'@\w+|#\w+', '', texto_completo)
    
    # Eliminar puntuación
    translator = str.maketrans('', '', string.punctuation + '¿¡“”')
    texto_sin_punc = texto_completo.translate(translator)
    
    palabras = texto_sin_punc.split()
    
    # Filtrar stopwords, números y palabras cortas
    palabras_filtradas = [
        p for p in palabras 
        if p not in stop_words_es and not p.isdigit() and len(p) > 2
    ]
    
    # Devolver las 25 palabras más comunes como un conjunto
    if not palabras_filtradas:
        return set()
        
    return set([p[0] for p in Counter(palabras_filtradas).most_common(25)])


# --- FUNCIÓN PRINCIPAL MEJORADA ---

@st.cache_data
def analizar_nivel_amistad(_df_chat):
    """
    Opción 3: Analiza el nivel de amistad y la dinámica de un grupo (2 o más autores).
    """
    st.subheader("Análisis de Amistad del Grupo")

    if _df_chat.empty:
        st.warning("No se encontraron mensajes válidos para analizar.")
        return

    autores_counts = _df_chat['Autor'].value_counts()
    num_autores = len(autores_counts)

    if num_autores < 2:
        st.error(f"Se necesitan al menos 2 autores para un análisis de amistad. (Encontrados: {num_autores})")
        return
        
    autores_principales = autores_counts.index.tolist()
    st.write(f"Analizando la dinámica de **{num_autores}** participantes: *{', '.join(autores_principales)}*")

    # Cargar modelo (de la caché) y stopwords
    try:
        sentiment_analyzer = cargar_modelo_sentimientos()
        stop_words_es = set(stopwords.words('spanish'))
        # Añadir palabras comunes de chat que no aportan significado
        stop_words_es.update(['jaja', 'jajaja', 'jeje', 'jejeje', 'ok', 'vale', 'si', 'no', 'q', 'k', 'https'])
    except Exception as e:
        st.error(f"Error al cargar recursos de NLTK o el modelo de sentimientos: {e}")
        return

    # --- MÉTRICA 1: Vibra Positiva (Global) ---
    # Esta métrica mide el sentimiento general de toda la conversación
    try:
        resultados_sent = sentiment_analyzer.predict(_df_chat['Mensaje'].tolist())
        sentimientos = [r.output for r in resultados_sent]
        conteo_sent = pd.Series(sentimientos).value_counts(normalize=True)
        vibra_positiva = conteo_sent.get('POS', 0) * 100
    except Exception as e:
        st.warning(f"No se pudo calcular la vibra positiva: {e}")
        vibra_positiva = 0.0

    # --- Procesamiento por Autor (para métricas 2, 3 y 4) ---
    datos_autores = {}
    
    for autor in autores_principales:
        df_autor = _df_chat[_df_chat['Autor'] == autor]
        mensajes_autor = df_autor['Mensaje'].tolist()
        count_autor = len(mensajes_autor)
        
        if count_autor == 0:
            continue
            
        # Sentimiento por autor
        sent_autor = sentiment_analyzer.predict(mensajes_autor)
        sent_outputs = [r.output for r in sent_autor]
        prop_pos = sent_outputs.count('POS') / count_autor
        
        # Palabras clave por autor
        top_palabras = _limpiar_y_contar_palabras(mensajes_autor, stop_words_es)
        
        datos_autores[autor] = {
            'count': count_autor,
            'prop_positiva': prop_pos,
            'palabras_set': top_palabras
        }
    
    # Filtrar autores que no tengan datos (aunque value_counts debería prevenir esto)
    datos_autores_validos = [d for d in datos_autores.values() if d['count'] > 0]
    
    if len(datos_autores_validos) < 2:
        st.error("No hay suficientes datos de autores (con mensajes válidos) para comparar.")
        return

    # --- MÉTRICA 2: Balance de Participación ---
    # Compara al que más habla con el que menos habla.
    counts = [d['count'] for d in datos_autores_validos]
    balance_participacion = (min(counts) / max(counts)) * 100 if max(counts) > 0 else 0.0

    # --- MÉTRICA 3: Sincronía Emocional ---
    # Mide la desviación estándar de la positividad.
    # Una desviación baja (cercana a 0) es alta sincronía (todos sienten parecido).
    props_positivas = [d['prop_positiva'] for d in datos_autores_validos]
    std_dev_sent = np.std(props_positivas)
    # Convertimos la desviación (0=bueno, 1=malo) a un puntaje (100=bueno, 0=malo)
    sincronia_emocional = max(0.0, (1 - std_dev_sent) * 100.0)

    # --- MÉTRICA 4: Intereses Comunes ---
    # Mide el % de palabras clave que TODOS los autores comparten (Jaccard Index).
    lista_sets_palabras = [d['palabras_set'] for d in datos_autores_validos if d['palabras_set']]
    
    if not lista_sets_palabras or len(lista_sets_palabras) < num_autores:
        # Si alguien no dijo palabras clave, los intereses comunes (de todos) es 0
        intereses_comunes = 0.0
    else:
        interseccion = set.intersection(*lista_sets_palabras)
        union = set.union(*lista_sets_palabras)
        
        intereses_comunes = (len(interseccion) / len(union)) * 100 if len(union) > 0 else 0.0

    # --- CÁLCULO FINAL: Nivel de Amistad ---
    nivel_amistad_total = (
        vibra_positiva + balance_participacion + 
        sincronia_emocional + intereses_comunes
    ) / 4.0

    # --- Graficar (GRÁFICO 1: Barras de Amistad) ---
    st.write("--- Pilares de la Amistad del Grupo ---")
    data = {
        'Métrica': [
            'Intereses Comunes 🗣️', 
            'Sincronía Emocional 😊', 
            'Balance de Participación ⚖️', 
            'Vibra Positiva General 💖'
        ],
        'Puntaje (%)': [
            intereses_comunes, 
            sincronia_emocional, 
            balance_participacion, 
            vibra_positiva
        ]
    }
    df_metricas = pd.DataFrame(data).set_index('Métrica').sort_values('Puntaje (%)', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 5))
    df_metricas['Puntaje (%)'].plot(kind='barh', ax=ax, xlim=(0, 100), zorder=1)
    
    # --- Aplicar Gradiente (mismo código tuyo) ---
    cmap = plt.cm.get_cmap('Reds') 
    gradient_colors = cmap(np.linspace(0.4, 1.0, 256).reshape(1, -1))

    for bar in ax.patches:
        x0, y0 = bar.get_xy()
        width, height = bar.get_width(), bar.get_height()
        
        if width <= 0:
            continue
            
        ax.imshow(gradient_colors, 
                  extent=[x0, x0 + width, y0, y0 + height], 
                  aspect='auto', 
                  zorder=2)
    # --- Fin Gradiente ---

    ax.set_title(f'Análisis de Amistad del Grupo ({num_autores} participantes)', fontsize=16)
    ax.set_xlabel('Puntaje (0-100)', fontsize=12)
    ax.set_ylabel('')
    
    for i, (index, row) in enumerate(df_metricas.iterrows()):
        ax.text(
            row['Puntaje (%)'] + 1, 
            i, 
            f'{row["Puntaje (%)"]:.1f}%', 
            color='black', va='center',
            zorder=3
        )
    
    st.pyplot(fig)

    # --- Graficar (GRÁFICO 2: Medidor Nivel de Amistad) (MODIFICADO) ---
    st.write("--- Nivel de Amistad General ---")
    
    fig_gauge, ax_gauge = plt.subplots(figsize=(10, 2))
    
    # El valor a graficar es el promedio de las métricas
    gauge_value = nivel_amistad_total
    
    # Fondo de gradiente (Azul 'Frío' a Rojo 'Cálido')
    cmap_gauge = plt.cm.get_cmap('coolwarm')
    gauge_gradient = cmap_gauge(np.linspace(0, 1, 256).reshape(1, -1))
    
    ax_gauge.imshow(gauge_gradient, extent=[0, 100, -0.02, 0.02], aspect='auto')
    
    # El marcador (triángulo)
    ax_gauge.plot(gauge_value, 0, 'v', 
                  markersize=25, color='black', 
                  clip_on=False, zorder=10)
    ax_gauge.plot(gauge_value, 0, 'v', 
                  markersize=20, color='white', 
                  clip_on=False, zorder=11)
    
    # Etiquetas de texto
    if gauge_value > 75:
        tendencia = "Muy Fuerte 🔥"
    elif gauge_value > 50:
        tendencia = "Fuerte 😊"
    elif gauge_value > 25:
        tendencia = "Regular 🤝"
    else:
        tendencia = "Baja 🧊"
        
    ax_gauge.text(gauge_value, 0.1, f'Puntaje: {gauge_value:.0f}% ({tendencia})', 
                  ha='center', fontsize=12, weight='bold')
    
    ax_gauge.text(0, -0.1, 'Baja', ha='left', fontsize=12, weight='bold')
    ax_gauge.text(100, -0.1, 'Muy Fuerte', ha='right', fontsize=12, weight='bold')

    # Limpiar ejes
    ax_gauge.set_yticks([])
    ax_gauge.set_xticks([])
    ax_gauge.set_xlim(-5, 105) 
    ax_gauge.set_ylim(-0.2, 0.2)
    
    plt.box(False)
    
    st.pyplot(fig_gauge)