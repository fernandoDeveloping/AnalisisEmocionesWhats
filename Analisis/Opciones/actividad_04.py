import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Función para configurar el estilo de los gráficos
def configurar_grafico():
    plt.style.use('seaborn-v0_8-darkgrid')
    plt.rc('figure', figsize=(10, 5))
    plt.rc('font', size=12)
    plt.rc('axes', titlesize=16, labelsize=14)
    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)

@st.cache_data
def analizar_actividad(_df_chat):
    """
    Opción 4: Analiza los patrones de actividad y horarios del chat.
    """
    st.subheader("Análisis de Actividad y Horarios 🕒")

    if _df_chat.empty:
        st.warning("No hay datos de chat para analizar.")
        return

    # --- NUEVA COMPROBACIÓN DEFENSIVA ---
    # Revisamos si la columna 'Timestamp' existe antes de intentar usarla.
    if 'Timestamp' not in _df_chat.columns:
        st.error(f"Error Crítico: No se encontró la columna 'Timestamp' en el DataFrame.")
        st.warning("El análisis de actividad no puede continuar porque depende de la Timestamp de los mensajes.")
        st.info(f"Columnas encontradas en tu DataFrame: {list(_df_chat.columns)}")
        st.write("---")
        st.write("**Sugerencia:** Revisa tu función `procesar_chat` (en `Analisis/Utils/aux_opciones.py`) y asegúrate de que esté extrayendo la Timestamp de cada mensaje y guardándola en una columna llamada `Timestamp`.")
        return # Detenemos la ejecución de esta función
    # --- FIN DE LA COMPROBACIÓN ---

    # Si la comprobación pasa, continuamos como antes.
    df_actividad = _df_chat.copy()
    
    try:
        # Asegurarnos de que 'Timestamp' es un objeto datetime
        df_actividad['Timestamp'] = pd.to_datetime(df_actividad['Timestamp'])
    except Exception as e:
        st.error(f"Error al convertir la columna 'Timestamp' a formato de Timestamp y hora: {e}")
        st.write("Asegúrate de que la columna 'Timestamp' contenga Timestamps válidas (ej: '25/12/2023 14:30').")
        return

    # --- 1. Heatmap de Actividad (Día vs Hora) ---
    st.markdown("#### ¿Cuándo está más activa la conversación?")
    
    # Extraer características de tiempo
    df_actividad['Hora'] = df_actividad['Timestamp'].dt.hour
    df_actividad['DiaSemanaNum'] = df_actividad['Timestamp'].dt.dayofweek
    dias_semana_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    # Crear la tabla pivote
    df_heatmap = df_actividad.groupby(['Hora', 'DiaSemanaNum']).size().unstack(fill_value=0)
    
    # Asegurar que todas las horas (0-23) y días (0-6) estén presentes
    df_heatmap = df_heatmap.reindex(index=range(24), fill_value=0)
    df_heatmap = df_heatmap.reindex(columns=range(7), fill_value=0)
    
    # Asignar nombres correctos a las columnas
    df_heatmap.columns = [dias_semana_es[i] for i in df_heatmap.columns]
    
    configurar_grafico()
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        df_heatmap, 
        cmap="Reds", 
        linewidths=.5, 
        annot=True, 
        fmt="d", 
        ax=ax,
        cbar_kws={'label': 'Número de Mensajes'}
    )
    ax.set_title('Mapa de Calor de Actividad (Hora vs. Día de la Semana)')
    ax.set_xlabel('Día de la Semana')
    ax.set_ylabel('Hora del Día')
    st.pyplot(fig)

    # --- 2. Gráficos de Barras (Hora y Día) ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Mensajes por Hora")
        configurar_grafico()
        # Aseguramos que todas las horas estén presentes para un gráfico completo
        conteo_horas = df_actividad['Hora'].value_counts().reindex(index=range(24), fill_value=0)
        
        fig_hora, ax_hora = plt.subplots()
        sns.barplot(
            x=conteo_horas.index, 
            y=conteo_horas.values,
            ax=ax_hora,
            palette="plasma"
        )
        ax_hora.set_xlabel('Hora del Día')
        ax_hora.set_ylabel('Total de Mensajes')
        st.pyplot(fig_hora)

    with col2:
        st.markdown("#### Mensajes por Día de la Semana")
        configurar_grafico()
        # Ordenar por el número del día de la semana
        conteo_dias = df_actividad.groupby('DiaSemanaNum').size()
        conteo_dias = conteo_dias.reindex(index=range(7), fill_value=0)
        
        fig_dia, ax_dia = plt.subplots()
        sns.barplot(
            x=[dias_semana_es[i] for i in conteo_dias.index], 
            y=conteo_dias.values,
            ax=ax_dia,
            palette="viridis"
        )
        ax_dia.set_xlabel('Día de la Semana')
        ax_dia.set_ylabel('Total de Mensajes')
        plt.xticks(rotation=45)
        st.pyplot(fig_dia)

    # --- 3. Actividad a lo Largo del Tiempo (Gráfico de Línea) ---
    st.markdown("#### Actividad a lo Largo del Tiempo")
    configurar_grafico()
    
    # Agrupar mensajes por día
    df_linea = df_actividad.set_index('Timestamp').resample('D').size()
    
    fig_linea, ax_linea = plt.subplots(figsize=(12, 4))
    df_linea.plot(ax=ax_linea, color='royalblue', lw=2)
    ax_linea.set_title('Volumen de Mensajes por Día')
    ax_linea.set_xlabel('Timestamp')
    ax_linea.set_ylabel('Número de Mensajes')
    st.pyplot(fig_linea)

