"""
GestoBeat — Miguel Ruiz
Proyecto final · Creación de Interfaces Multimodales (EAFIT 2026-2)

Un instrumento musical sin instrumento: cada gesto de la mano (Teachable Machine), cada toque
en las barras o cada palabra dicha suena como una nota afinada (Tone.js), y un ESP32 en Wokwi
enciende el LED de la nota y la toca en su buzzer (MQTT).

Todo lo que necesita tiempo real (cámara, modelo, sonido, voz y MQTT) corre en el navegador,
dentro del componente de la carpeta `componente/`, para que la música no se corte cuando
Streamlit vuelve a ejecutar el script.
"""

from collections import Counter
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from estilo import NOTAS, aplicar, marca

st.set_page_config(page_title="GestoBeat", page_icon="🎵", layout="wide", initial_sidebar_state="collapsed")
aplicar()

_gestobeat = components.declare_component("gestobeat", path=str(Path(__file__).parent / "componente"))

ORIGEN = {"gesto": "con gestos", "tablero": "en las barras", "teclado": "con el teclado", "voz": "con la voz"}

# ─────────────────────────────────────────────
# AJUSTES (panel lateral)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Modelo de gestos")
    modelo_url = st.text_input(
        "Enlace de Teachable Machine",
        value="https://teachablemachine.withgoogle.com/models/0SuhMwLNA/",
        placeholder="https://teachablemachine.withgoogle.com/models/…/",
        help="En Teachable Machine: Exportar modelo → Tensorflow.js → Subir mi modelo. "
             "Si lo dejas vacío, la app busca el modelo en la carpeta componente/modelo del repositorio.",
    )
    umbral = st.slider("Seguridad para tocar la nota", 0.5, 0.99, 0.80, 0.01,
                       help="La nota solo suena si el modelo está así de seguro del gesto. "
                            "Súbela si suenan notas de más; bájala si cuesta que reconozca tus gestos.")
    st.divider()
    st.markdown("### Sonido")
    instrumento = st.selectbox("Instrumento al abrir", ["piano", "guitarra", "marimba"], format_func=str.capitalize)
    st.divider()
    st.markdown("### Conexión con el ESP32")
    broker = st.text_input("Broker MQTT (websocket)", value="wss://broker.hivemq.com:8884/mqtt",
                           help="El navegador entra por websocket seguro; el ESP32 de Wokwi usa el mismo broker por el puerto 1883.")
    topico = st.text_input("Tópico", value="gestobeat_miguelruiz",
                           help="Tiene que ser el mismo tópico al que se suscribe el ESP32 en Wokwi.")

# ─────────────────────────────────────────────
# INSTRUMENTO
# ─────────────────────────────────────────────
marca("Cada gesto de tu mano es una nota afinada. Toca libre o imita melodías, y mira cómo el ESP32 las acompaña con luces.")

estado = _gestobeat(modelo_url=modelo_url, umbral=umbral, instrumento=instrumento,
                    broker=broker, topico=topico, key="gestobeat", default=None) or {}

# ─────────────────────────────────────────────
# TU SESIÓN (lo envía el componente)
# ─────────────────────────────────────────────
por_nota = Counter(estado.get("por_nota", {}))
por_origen = Counter(estado.get("por_origen", {}))
total = estado.get("notas", 0)

if total:
    favorita = por_nota.most_common(1)[0][0]
    forma = ORIGEN.get(por_origen.most_common(1)[0][0], "")
    frase = (f"Llevas <b>{total} {'nota' if total == 1 else 'notas'}</b>, casi todas {forma}. "
             f"La que más suena es <b style='color:{NOTAS[favorita]}'>{favorita}</b>.")
    if estado.get("mejor_puntaje"):
        completas = estado.get("completas", 0)
        frase += f" Tu mejor puntaje en el juego es <b>{estado['mejor_puntaje']}</b>"
        frase += (f", con {completas} {'melodía completa' if completas == 1 else 'melodías completas'}." if completas else ".")
    if estado.get("mqtt_enviados"):
        frase += f" El ESP32 recibió <b>{estado['mqtt_enviados']}</b> de ellas."
    maximo = max(por_nota.values())
    hist = "".join(
        f'<div><span style="height:{max(por_nota.get(n, 0) / maximo * 110, 6):.0f}px;background:{c}"></span>'
        f'<b style="color:{c}">{n}</b><small>{por_nota.get(n, 0)}</small></div>'
        for n, c in NOTAS.items()
    )
    filas = "".join(
        f'<div class="fila"><span class="pt" style="background:{NOTAS.get(u["nota"], "#fff")}">{u["nota"]}</span>'
        f'<span>{u["instrumento"].capitalize()}, {ORIGEN.get(u["origen"], u["origen"])}</span><span class="q">{u["hora"]}</span></div>'
        for u in estado.get("ultimas", [])[:6]
    )
    st.markdown(f"""
    <div class="sesion">
      <div><h2>Tu sesión</h2><div class="resumen">{frase}</div><div class="hist">{hist}</div></div>
      <div class="recientes"><h3>Lo último que sonó</h3>{filas}</div>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="sesion">
      <div><h2>Tu sesión</h2><p class="vacio-sesion">Cuando empieces a tocar, aquí vas a ver cuántas notas llevas, cuál suena más y tu mejor puntaje.</p></div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AYUDAS
# ─────────────────────────────────────────────
st.markdown('<h3 class="ayudas-titulo">Antes de tocar</h3>', unsafe_allow_html=True)

with st.expander("Cómo se toca"):
    st.markdown(f"""
- **Con gestos:** enciende la cámara y haz el gesto un instante. ✋ mano abierta es Do, ✊ puño es Re, ☝️ un dedo es Mi,
  ✌️ dos dedos es Sol y 👍 pulgar arriba es La. Para repetir la misma nota, baja la mano y vuelve a hacer el gesto.
- **Con las barras o el teclado:** toca las barras de colores o usa las teclas 1 a 5.
- **Con la voz:** activa la voz y di «piano», «guitarra» o «marimba» para cambiar el sonido; «juego», «escuchar» u
  «otra melodía» para el juego, o las notas, como «do mi sol».
- **Imita la melodía:** escucha la melodía en el pentagrama y repítela nota por nota. Cada acierto suma puntos y la racha da más.
- Cada nota se publica como `{{"nota": "Mi", "instrumento": "piano"}}` en el tópico `{topico}`.
""")

with st.expander("Entrenar el modelo de gestos en Teachable Machine"):
    st.markdown("""
1. Entra a **teachablemachine.withgoogle.com**, elige *Proyecto de imagen* y luego *Modelo de imagen estándar*.
2. Crea seis clases con estos nombres: `Do`, `Re`, `Mi`, `Sol`, `La` y `Nada`.
3. Graba unas 150 fotos por clase con la webcam: ✋ mano abierta, ✊ puño, ☝️ un dedo, ✌️ dos dedos y 👍 pulgar arriba.
   En `Nada` graba tu cara y el fondo sin la mano. Cambia un poco la distancia y el ángulo mientras grabas.
4. Entrena el modelo y pruébalo en la vista previa.
5. Ve a *Exportar modelo*, pestaña *Tensorflow.js*, y elige *Subir mi modelo*. Copia el enlace.
6. Abre los Ajustes de esta app (la flecha arriba a la izquierda) y pega el enlace en *Enlace de Teachable Machine*.
""")

with st.expander("Conectar el ESP32 en Wokwi"):
    st.markdown(f"""
1. En **wokwi.com** crea un proyecto nuevo de ESP32.
2. Copia `sketch.ino`, `diagram.json` y `libraries.txt` de la carpeta `wokwi` del repositorio en las pestañas del mismo nombre.
3. Dale play y espera a que el monitor serie diga *MQTT conectado*.
4. Toca cualquier nota aquí: se enciende su LED y suena el buzzer. El tópico tiene que ser `{topico}`.
""")

st.markdown('<p class="pie">GestoBeat es el proyecto final de Miguel Ruiz para Creación de Interfaces Multimodales, EAFIT 2026-2.</p>',
            unsafe_allow_html=True)
