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




