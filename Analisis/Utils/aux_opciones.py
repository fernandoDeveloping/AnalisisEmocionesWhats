import pandas as pd
import re
import io
import zipfile
import unicodedata
import streamlit as st

def limpieza_estricta_texto(texto):
    """
    Limpia texto: minúsculas, sin tildes (opcional), conserva emojis y caracteres Unicode visibles.
    """
    if not isinstance(texto, str):
        return ""
    texto = texto.lower()
    # Normaliza tildes (mantiene emojis y otros símbolos Unicode intactos)
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn' or not c.isascii())
    # Limpia caracteres de control, pero mantiene emojis, signos, puntuación normal y emojis Unicode
    texto = re.sub(r'[\x00-\x1f\x7f-\x9f]+', '', texto)  # elimina caracteres invisibles
    texto = re.sub(r'\s{2,}', ' ', texto).strip()  # normaliza espacios múltiples
    
    return texto



def procesar_chat(uploaded_file):
    """Lee y parsea un chat de WhatsApp (.txt o .zip) adaptándose a distintos formatos."""
    try:
        content_bytes = uploaded_file.getvalue()
        if uploaded_file.name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(content_bytes), 'r') as zip_ref:
                txt_files = [f for f in zip_ref.infolist()
                             if f.filename.endswith('.txt') and not f.is_dir()]
                if not txt_files:
                    st.error("El ZIP no contiene archivos .txt válidos.")
                    return pd.DataFrame(columns=['Timestamp', 'Autor', 'Mensaje'])
                txt_files.sort(key=lambda f: f.file_size, reverse=True)
                with zip_ref.open(txt_files[0].filename) as txt_file:
                    content_bytes = txt_file.read()

        try:
            content_str = content_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            content_str = content_bytes.decode('latin-1')

        lines = content_str.splitlines()
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame(columns=['Timestamp', 'Autor', 'Mensaje'])

    # ---- Limpieza inicial ----
    RE_CONTROL = re.compile(r'[\x00-\x1f\x7f-\x9f\u200e\u200f\ufeff\u202f\xa0]+')

    # ---- 4 posibles formatos de timestamp ----
    patrones_fallback = [
        # 1️⃣ "21/9/25, 06:50 - Autor: Mensaje"
        re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?:\s*(?:[ap]\.?m\.?))?)\s*-\s*([^:]+):\s*(.*)', re.IGNORECASE),
        # 2️⃣ "21/9/25 06:50 - Autor: Mensaje" (sin coma)
        re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}(?:\s*(?:[ap]\.?m\.?))?)\s*-\s*([^:]+):\s*(.*)', re.IGNORECASE),
        # 3️⃣ "25/4/2025, 1:35 p. m. - Autor: Mensaje" (con puntos y espacios)
        re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[ap]\.\s*m\.)\s*-\s*([^:]+):\s*(.*)', re.IGNORECASE),
        # 4️⃣ Formato alternativo iOS (por si acaso)
        re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4},?\s*\d{1,2}:\d{2}(?:\s*(?:[ap]\.?m\.?))?)\]\s*([^:]+):\s*(.*)', re.IGNORECASE),
    ]

    # ---- Intento progresivo con fallback ----
    datos, mensaje_buffer = [], []
    timestamp_actual, autor_actual = None, None
    patron_usado = None

    for patron in patrones_fallback:
        datos.clear()
        mensaje_buffer.clear()
        timestamp_actual = autor_actual = None

        for linea in lines:
            linea = RE_CONTROL.sub('', linea).strip()
            if not linea:
                continue

            match = patron.match(linea)
            if match:
                if autor_actual and timestamp_actual and mensaje_buffer:
                    datos.append({
                        "Timestamp_str": timestamp_actual,
                        "Autor": autor_actual,
                        "Mensaje": " ".join(mensaje_buffer)
                    })
                timestamp_actual = match.group(1).strip()
                autor_actual = match.group(2).strip()
                mensaje_buffer = [match.group(3).strip()] if match.group(3).strip() else []
            elif timestamp_actual and autor_actual:
                mensaje_buffer.append(linea)

        if autor_actual and timestamp_actual and mensaje_buffer:
            datos.append({
                "Timestamp_str": timestamp_actual,
                "Autor": autor_actual,
                "Mensaje": " ".join(mensaje_buffer)
            })

        if len(datos) > 5:  # umbral mínimo para considerar válido
            patron_usado = patron
            break

    if not datos:
        st.error("No se reconocieron mensajes con ninguno de los patrones posibles.")
        st.code('\n'.join(lines[:10]))
        return pd.DataFrame(columns=['Timestamp', 'Autor', 'Mensaje'])

    st.info(f"✔️ Se detectó el formato del chat automáticamente ({len(datos)} mensajes).")

    # ---- Limpieza y normalización ----
    df = pd.DataFrame(datos)
    df['Timestamp_norm'] = df['Timestamp_str'].str.lower()
    df['Timestamp_norm'] = df['Timestamp_norm'].str.replace(r'\s*([ap])\.?\s*m\.?', r'\1m', regex=True)
    df['Timestamp_norm'] = df['Timestamp_norm'].str.replace(r'\s+', ' ', regex=True).str.strip()

    formatos = [
        '%d/%m/%Y, %I:%M%p', '%d/%m/%Y %I:%M%p', '%d/%m/%y, %I:%M%p', '%d/%m/%y %I:%M%p',
        '%d/%m/%Y, %H:%M', '%d/%m/%Y %H:%M', '%d/%m/%y, %H:%M', '%d/%m/%y %H:%M'
    ]
    df['Timestamp'] = pd.NaT
    for fmt in formatos:
        mask = df['Timestamp'].isna()
        if not mask.any(): break
        converted = pd.to_datetime(df.loc[mask, 'Timestamp_norm'], format=fmt, errors='coerce')
        df.loc[mask, 'Timestamp'] = df.loc[mask, 'Timestamp'].fillna(converted)

    df = df.dropna(subset=['Timestamp'])
    df = df.drop(columns=['Timestamp_str', 'Timestamp_norm'])

    # ---- Limpieza de texto ----
    df['Autor'] = df['Autor'].apply(limpieza_estricta_texto)
    df['Mensaje'] = df['Mensaje'].apply(limpieza_estricta_texto)

    filtro_sistema = (
        r"<multimedia omitido>|se eliminó este mensaje|ubicación: http|video omitido|imagen omitida|"
        r"gif omitido|sticker omitido|audio omitido|llamada perdida|videollamada perdida|"
        r"cambió tu código de seguridad|creó el grupo|añadió a|saliste del grupo|"
        r"cambió el ícono de este grupo|cambió el asunto|te añadió| multimedia omitido"
    )
    df = df[~df['Mensaje'].str.contains(filtro_sistema, na=False, regex=True)]

    df = df[df['Mensaje'].str.len() > 0]
    df = df[df['Autor'].str.len() > 0]

    if df.empty:
        st.warning("El DataFrame quedó vacío tras la limpieza final.")
        return pd.DataFrame(columns=['Timestamp', 'Autor', 'Mensaje'])

    st.success(f"¡Chat procesado correctamente! ({len(df)} mensajes válidos).")
    return df[['Timestamp', 'Autor', 'Mensaje']]
