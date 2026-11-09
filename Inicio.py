"""
GestoBeat — Miguel Ruiz
Proyecto final · Creación de Interfaces Multimodales (EAFIT 2026-2)

Un instrumento musical sin instrumento: cada gesto de la mano (Teachable Machine), cada toque
en el tablero o cada palabra dicha suena como una nota afinada (Tone.js), y un ESP32 en Wokwi
enciende el LED de la nota y la toca en su buzzer (MQTT).

Todo lo que necesita tiempo real (cámara, modelo, sonido, voz y MQTT) corre en el navegador,
dentro del componente de la carpeta `componente/`, para que la música no se corte cuando
Streamlit vuelve a ejecutar el script.
"""

from collections import Counter
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from comun import configurar_pagina, encabezado, info_items

configurar_pagina("GestoBeat", "🎵")

_gestobeat = components.declare_component("gestobeat", path=str(Path(__file__).parent / "componente"))

COLORES = {"Do": "#e85d4a", "Re": "#f2994a", "Mi": "#f2cc8f", "Sol": "#7bd88f", "La": "#6fb3d2"}
ICONOS = {"gesto": "🖐️", "tablero": "🎹", "teclado": "⌨️", "voz": "🎙️"}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎵 GestoBeat")
    st.divider()
    st.markdown("### MODELO DE GESTOS")
    modelo_url = st.text_input(
        "Enlace de Teachable Machine:",
        placeholder="https://teachablemachine.withgoogle.com/models/…/",
        help="En Teachable Machine: Exportar modelo → Tensorflow.js → Subir (enlace compartible). "
             "Si lo dejas vacío, la app busca el modelo en la carpeta componente/modelo del repositorio.",
    )
    umbral = st.slider("Confianza mínima", 0.5, 0.99, 0.80, 0.01,
                       help="La nota solo suena si el modelo está así de seguro del gesto.")
    st.divider()
    st.markdown("### SONIDO")
    instrumento = st.selectbox("Instrumento inicial:", ["piano", "guitarra", "marimba"],
                               format_func=str.capitalize)
    st.divider()
    st.markdown("### CONEXIÓN MQTT")
    broker = st.text_input("Broker (websocket):", value="wss://broker.mqttdashboard.com:8884/mqtt",
                           help="El navegador se conecta por websocket seguro; el ESP32 de Wokwi usa el mismo "
                                "broker por el puerto 1883.")
    topico = st.text_input("Tópico:", value="gestobeat_miguelruiz",
                           help="Debe ser el mismo tópico al que se suscribe el ESP32 en Wokwi.")

# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
encabezado(
    "🎵 GestoBeat",
    "Tu mano es el instrumento: cada gesto suena como una nota afinada y el ESP32 la acompaña con luces",
    f"<b>●</b> {topico}",
)

estado = _gestobeat(modelo_url=modelo_url, umbral=umbral, instrumento=instrumento,
                    broker=broker, topico=topico, key="gestobeat", default=None)

# ─────────────────────────────────────────────
# RESUMEN DE LA SESIÓN (lo envía el componente)
# ─────────────────────────────────────────────
estado = estado or {}
por_nota = Counter(estado.get("por_nota", {}))
por_origen = Counter(estado.get("por_origen", {}))

st.divider()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Notas tocadas", estado.get("notas", 0))
m2.metric("Nota favorita", por_nota.most_common(1)[0][0] if por_nota else "—")
m3.metric("Mejor puntaje", estado.get("mejor_puntaje", 0))
m4.metric("Mensajes al ESP32", estado.get("mqtt_enviados", 0))

if por_nota:
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    a, b = st.columns([1.1, 1], gap="large")
    with a:
        with st.container(key="card_notas"):
            st.markdown("### 🎼 Notas de la sesión")
            maximo = max(por_nota.values())
            st.markdown("".join(
                f'<div class="freq-row"><span class="rank-tag" style="color:{COLORES[n]}">{n}</span>'
                f'<div style="flex:1; height:8px; background:#14303d; border-radius:4px; overflow:hidden;">'
                f'<div style="width:{por_nota.get(n, 0) / maximo * 100:.0f}%; height:100%; background:{COLORES[n]};"></div></div>'
                f'<span class="txt" style="min-width:34px; text-align:right;">{por_nota.get(n, 0)}</span></div>'
                for n in COLORES
            ), unsafe_allow_html=True)
            st.markdown("".join(f'<span class="uso-tag">{ICONOS.get(o, "•")} {o} · {c}</span>'
                                for o, c in por_origen.most_common()), unsafe_allow_html=True)
    with b:
        with st.container(key="card_ultimas"):
            st.markdown("### 🕘 Últimas notas")
            st.markdown("".join(
                f'<div class="freq-row"><span class="ic-row">{ICONOS.get(u["origen"], "•")}</span>'
                f'<div class="txt"><b style="color:{COLORES.get(u["nota"], "#f2cc8f")}">{u["nota"]}</b>'
                f'<small>{u["hora"]} · {u["instrumento"]} · {u["origen"]}</small></div></div>'
                for u in estado.get("ultimas", [])[:6]
            ), unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
with st.expander("¿Cómo funciona GestoBeat?"):
    info_items([
        ("🖐️", "1 · Gestos (Teachable Machine)", "La cámara ve tu mano unas 7 veces por segundo y el modelo reconoce "
                                                "el gesto: ✋ Do, ✊ Re, ☝️ Mi, ✌️ Sol, 👍 La."),
        ("🎹", "2 · Tablero, teclado o voz", "Si no hay cámara, tocas las franjas, usas las teclas 1–5 o dices la nota."),
        ("🎵", "3 · Sonido (Tone.js)", "Las notas son de la escala pentatónica, así que todo lo que toques suena afinado."),
        ("🎙️", "4 · Comandos de voz", "«piano», «guitarra», «marimba», «juego», «libre», «escuchar», «siguiente»."),
        ("📡", "5 · MQTT → ESP32 en Wokwi", f'Cada nota se publica como {{"nota": "Mi", "instrumento": "piano"}} '
                                           f"en el tópico {topico}; el ESP32 enciende su LED y la toca en el buzzer."),
    ])

with st.expander("¿Cómo entreno mi modelo de gestos?"):
    st.markdown("""
1. Entra a **teachablemachine.withgoogle.com** → *Proyecto de imagen* → *Modelo de imagen estándar*.
2. Crea **6 clases** con estos nombres exactos: `Do`, `Re`, `Mi`, `Sol`, `La` y `Nada`.
3. En cada clase graba con la webcam unas **150 fotos** del gesto (✋ mano abierta, ✊ puño, ☝️ un dedo,
   ✌️ dos dedos, 👍 pulgar arriba). En `Nada`, graba tu cara y el fondo **sin mano**. Mueve un poco la mano,
   cambia la distancia y, si puedes, pídele a otra persona que grabe también.
4. Clic en **Entrenar modelo** y prueba en la vista previa.
5. **Exportar modelo** → pestaña *Tensorflow.js* → **Subir mi modelo** → copia el enlace compartible.
6. Pégalo en el panel lateral, en *Enlace de Teachable Machine*. Las barras de cada clase aparecen solas.
""")

with st.expander("¿Cómo conecto el ESP32 en Wokwi?"):
    st.markdown(f"""
1. Abre **wokwi.com** → *New Project* → *ESP32*.
2. Copia `wokwi/sketch.ino`, `wokwi/diagram.json` y `wokwi/libraries.txt` del repositorio en las pestañas del mismo nombre.
3. Dale ▶ y espera a que el monitor serie diga **MQTT conectado**.
4. Toca cualquier nota aquí: se enciende su LED y suena el buzzer. El tópico debe ser `{topico}`.
""")
