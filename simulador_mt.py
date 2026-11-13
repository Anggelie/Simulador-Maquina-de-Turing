"""Simulador de una máquina de Turing determinista de una cinta.

Notación de transición: delta=q_actual,leído,q_siguiente,escrito,L|R
Notación de configuración: alfa q beta (el cabezal lee el primer símbolo de beta).
"""

import argparse
from pathlib import Path

COMPONENTES = {"Q", "Sigma", "Gamma", "blanco", "inicial", "aceptacion", "rechazo", "entrada"}


def cargar_maquina(ruta):
    """Lee y valida la definición de la MT desde un archivo de texto."""
    campos = {}
    transiciones = {}
    for numero, original in enumerate(Path(ruta).read_text(encoding="utf-8-sig").splitlines(), 1):
        linea = original.strip()
        if not linea or linea.startswith("#"):
            continue
        if "=" not in linea:
            raise ValueError(f"Línea {numero}: falta '='.")
        clave, valor = (parte.strip() for parte in linea.split("=", 1))
        if clave == "delta":
            partes = [parte.strip() for parte in valor.split(",")]
            if len(partes) != 5 or any(not parte for parte in partes):
                raise ValueError(f"Línea {numero}: delta debe tener cinco componentes.")
            actual, leido, siguiente, escrito, movimiento = partes
            if (actual, leido) in transiciones:
                raise ValueError(f"Línea {numero}: transición repetida para ({actual}, {leido}).")
            transiciones[(actual, leido)] = (siguiente, escrito, movimiento)
        elif clave in COMPONENTES:
            if clave in campos:
                raise ValueError(f"Línea {numero}: componente '{clave}' repetido.")
            campos[clave] = valor
        else:
            raise ValueError(f"Línea {numero}: componente desconocido '{clave}'.")

    faltantes = COMPONENTES - campos.keys()
    if faltantes:
        raise ValueError("Faltan componentes: " + ", ".join(sorted(faltantes)))
    if not transiciones:
        raise ValueError("La función de transición no contiene reglas.")

    conjuntos = {}
    for nombre in ("Q", "Sigma", "Gamma"):
        elementos = [item.strip() for item in campos[nombre].split(",")] if campos[nombre] else []
        if not elementos or any(not e for e in elementos) or len(elementos) != len(set(elementos)):
            raise ValueError(f"Conjunto {nombre} vacío, inválido o con elementos repetidos.")
        conjuntos[nombre] = set(elementos)

    estados, entrada, cinta_alf = (conjuntos[n] for n in ("Q", "Sigma", "Gamma"))
    blanco = campos["blanco"]
    if any(len(simbolo) != 1 for simbolo in entrada | cinta_alf):
        raise ValueError("Cada símbolo de Sigma y Gamma debe ser un único carácter.")
    if any(simbolo.isspace() for simbolo in entrada | cinta_alf):
        raise ValueError("Los símbolos no pueden ser espacios en blanco.")
    if not entrada <= cinta_alf:
        raise ValueError("Sigma debe ser subconjunto de Gamma.")
    if blanco not in cinta_alf or blanco in entrada:
        raise ValueError("El blanco debe pertenecer a Gamma y no pertenecer a Sigma.")
    especiales = [campos[n] for n in ("inicial", "aceptacion", "rechazo")]
    if len(set(especiales)) != 3 or not set(especiales) <= estados:
        raise ValueError("Los estados inicial, de aceptación y de rechazo deben ser distintos y estar en Q.")
    if any(simbolo not in entrada for simbolo in campos["entrada"]):
        raise ValueError("La cadena contiene símbolos fuera de Sigma.")
    for (actual, leido), (siguiente, escrito, movimiento) in transiciones.items():
        if actual not in estados or siguiente not in estados:
            raise ValueError(f"Transición ({actual}, {leido}): estado no declarado.")
        if leido not in cinta_alf or escrito not in cinta_alf:
            raise ValueError(f"Transición ({actual}, {leido}): símbolo fuera de Gamma.")
        if movimiento not in ("L", "R"):
            raise ValueError(f"Transición ({actual}, {leido}): movimiento debe ser L o R.")
        if actual in especiales[1:]:
            raise ValueError(f"El estado final {actual} no puede tener transiciones salientes.")
    return campos, transiciones


def mostrar_configuracion(cinta, posicion, estado, blanco):
    """Escribe alfa q beta; la variable cinta es el almacenamiento de la MT."""
    ocupadas = [indice for indice, simbolo in cinta.items() if simbolo != blanco]
    izquierda = min([0, posicion] + ocupadas)
    derecha = max([posicion] + ocupadas)
    alfa = "".join(cinta.get(i, blanco) for i in range(izquierda, posicion))
    beta = "".join(cinta.get(i, blanco) for i in range(posicion, derecha + 1))
    return f"{alfa}{estado}{beta}"


def simular(entrada_archivo, salida_archivo, max_pasos):
    campos, delta = cargar_maquina(entrada_archivo)
    blanco = campos["blanco"]
    # Diccionario disperso: representa exclusivamente las casillas de la cinta.
    cinta = {i: simbolo for i, simbolo in enumerate(campos["entrada"])}
    cabeza = 0
    estado = campos["inicial"]
    pasos = 0
    destino = Path(salida_archivo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as archivo:
        archivo.write("CONFIGURACIONES DE LA MÁQUINA DE TURING\n")
        archivo.write(f"Entrada: {campos['entrada'] if campos['entrada'] else 'ε'}\n")
        archivo.write("Notación: αqβ; q aparece antes del símbolo leído. B = blanco.\n\n")
        archivo.write(f"{pasos:03d}: {mostrar_configuracion(cinta, cabeza, estado, blanco)}\n")
        while estado not in (campos["aceptacion"], campos["rechazo"]) and pasos < max_pasos:
            leido = cinta.get(cabeza, blanco)
            if (estado, leido) not in delta:
                raise ValueError(f"No está definida δ({estado}, {leido}); la MT queda bloqueada.")
            siguiente, escrito, movimiento = delta[(estado, leido)]
            if escrito == blanco:
                cinta.pop(cabeza, None)
            else:
                cinta[cabeza] = escrito
            cabeza += 1 if movimiento == "R" else -1
            estado = siguiente
            pasos += 1
            archivo.write(f"{pasos:03d}: {mostrar_configuracion(cinta, cabeza, estado, blanco)}\n")

        if estado == campos["aceptacion"]:
            resultado = "ACEPTADA"
        elif estado == campos["rechazo"]:
            resultado = "RECHAZADA"
        else:
            resultado = f"LÍMITE DE {max_pasos} PASOS ALCANZADO: no se observó detención"
        archivo.write(f"\nResultado: {resultado}\nPasos: {pasos}\n")
    return resultado


def main():
    parser = argparse.ArgumentParser(description="Simulador de MT determinista de una cinta")
    parser.add_argument("entrada", help="Archivo .txt con la especificación y la cadena")
    parser.add_argument("salida", help="Archivo .txt donde se guardan las configuraciones")
    parser.add_argument("--pasos", type=int, default=20, help="Máximo de transiciones (predeterminado: 20)")
    args = parser.parse_args()
    if args.pasos <= 0:
        parser.error("--pasos debe ser positivo")
    try:
        print(simular(args.entrada, args.salida, args.pasos))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
