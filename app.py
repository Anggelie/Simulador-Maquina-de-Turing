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
st.caption("La interfaz utiliza el mismo simulador y las mismas validaciones que la terminal.")

with st.sidebar:
    st.header("Configuración")
    opcion = st.radio("Caso que deseas ejecutar", [*EJEMPLOS, "Cargar archivo propio"])
    subido = None
    if opcion == "Cargar archivo propio":
        subido = st.file_uploader("Especificación de la máquina (.txt)", type=["txt"])
    limite = st.number_input("Máximo de transiciones", min_value=1, max_value=10000, value=20, step=1)
    ejecutar = st.button("Ejecutar máquina", type="primary", use_container_width=True)

if opcion in EJEMPLOS:
    archivo_entrada, nombre_salida = EJEMPLOS[opcion]
    st.info(f"Ejemplo seleccionado: {opcion}")
else:
    archivo_entrada = None
    nombre_salida = "salida_personalizada.txt"
    st.info("Selecciona un archivo .txt con los componentes y las transiciones de la máquina.")

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

if ejecutar:
    temporal = None
    try:
        if opcion == "Cargar archivo propio":
            if subido is None:
                st.warning("Debes seleccionar un archivo .txt antes de ejecutar.")
                st.stop()
            # Archivo temporal para cargar la especificación; no es una segunda cinta.
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
            st.caption("El límite de pasos no demuestra un ciclo en general. Para la cadena vacía, las transiciones qida y qvuelta repiten la configuración.")

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

st.divider()
st.caption("La interfaz solo carga archivos y presenta resultados. La única cinta de trabajo pertenece al simulador.")
