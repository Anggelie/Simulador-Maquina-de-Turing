"""Interfaz Streamlit para el simulador determinista de una cinta.

Las transiciones se ejecutan exclusivamente en simulador_mt.py.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import streamlit as st

from simulador_mt import cargar_maquina, simular


BASE = Path(__file__).resolve().parent
EJEMPLOS = {
    "Aceptación (000)": (BASE / "ejemplos" / "aceptacion.txt", "salida_aceptacion.txt"),
    "Rechazo (001)": (BASE / "ejemplos" / "rechazo.txt", "salida_rechazo.txt"),
    "Ciclo (cadena vacía)": (BASE / "ejemplos" / "ciclo.txt", "salida_ciclo.txt"),
}

st.set_page_config(page_title="Simulador de Máquina de Turing", page_icon="🔤", layout="wide")
st.title("Simulador de Máquina de Turing")
st.write("Máquina determinista de una cinta · Teoría de la Computación")
# Oculta los controles de Streamlit y los enlaces automáticos de los encabezados.
st.markdown(
    """
    <style>
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stMainMenu"],
    #MainMenu,
    [data-testid="stHeaderActionElements"],
    [data-testid="stHeaderActionElements"] *,
    h1 a, h2 a, h3 a, h4 a {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuración")
    opcion = st.radio("Caso que deseas ejecutar", [*EJEMPLOS, "Cargar archivo propio"])
    st.markdown("**Archivo de texto**")
    subido = st.file_uploader(
        "Seleccionar especificación (.txt)",
        type=["txt"],
        help="Elige 'Cargar archivo propio' para ejecutar este archivo.",
    )
    limite = st.number_input(
        "Máximo de transiciones", min_value=1, max_value=10000, value=20, step=1
    )
    st.button("Volver a ejecutar", type="primary", use_container_width=True)

if opcion in EJEMPLOS:
    archivo_entrada, nombre_salida = EJEMPLOS[opcion]
    st.info(f"Ejemplo seleccionado: {opcion}")
else:
    archivo_entrada = None
    nombre_salida = "salida_personalizada.txt"
    if subido is not None:
        st.info(f"Archivo seleccionado: {subido.name}")
    else:
        st.info("Carga un archivo .txt desde el panel izquierdo para ejecutar tu máquina.")

izquierda, derecha = st.columns([1, 1], gap="large")

with izquierda:
    st.subheader("Diagrama de estados")
    diagrama = BASE / "diagramas" / "maquina_turing.dot"
    if diagrama.is_file():
        st.graphviz_chart(diagrama.read_text(encoding="utf-8"), use_container_width=True)
    st.caption("Este diagrama representa los tres ejemplos incluidos. Un archivo propio puede definir otra máquina.")

with derecha:
    st.subheader("Modelo formal")
    st.latex(r"M=(Q,\Sigma,\Gamma,\delta,q_0,B,q_{acepta},q_{rechaza})")
    st.latex(r"\delta(q,a)=(q',b,D),\quad D\in\{L,R\}")
    st.markdown("**Configuraciones:** αqβ (el estado aparece antes del símbolo leído).")
    st.markdown("**Blanco:** `B` · **Movimientos:** `L` y `R`.")

# Se ejecuta con la selección actual en cada cambio de caso o archivo.
# Así nunca permanece visible un resultado de otra entrada.
if archivo_entrada is not None or (opcion == "Cargar archivo propio" and subido is not None):
    temporal = None
    try:
        if opcion == "Cargar archivo propio":
            # El archivo temporal contiene la especificación, no es una cinta adicional.
            with NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as archivo:
                archivo.write(subido.getvalue())
                temporal = Path(archivo.name)
            archivo_entrada = temporal

        campos, transiciones = cargar_maquina(archivo_entrada)
        destino = BASE / "salidas" / nombre_salida
        resultado = simular(archivo_entrada, destino, int(limite))
        contenido = destino.read_text(encoding="utf-8")

        st.divider()
        st.subheader("Resultado de la ejecución")
        if resultado == "ACEPTADA":
            st.success("Cadena aceptada")
        elif resultado == "RECHAZADA":
            st.error("Cadena rechazada")
        else:
            st.warning(resultado)
            if opcion == "Ciclo (cadena vacía)":
                st.caption(
                    "En este ejemplo, las transiciones qida y qvuelta "
                    "repiten la configuración. El límite de pasos "
                    "por sí solo no demuestra un ciclo infinito."
                )

        a, b, c = st.columns(3)
        a.metric("Cadena", campos["entrada"] or "ε")
        b.metric("Estados", len(campos["Q"].split(",")))
        c.metric("Transiciones", len(transiciones))
        st.subheader("Configuraciones αqβ")
        st.code(contenido, language=None)
        st.download_button(
            "Descargar configuraciones (.txt)",
            data=contenido.encode("utf-8"),
            file_name=nombre_salida,
            mime="text/plain",
        )
        st.caption(f"Archivo guardado en salidas/{nombre_salida}")
    except (OSError, UnicodeError, ValueError) as error:
        st.error(f"No se pudo ejecutar la máquina: {error}")
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
