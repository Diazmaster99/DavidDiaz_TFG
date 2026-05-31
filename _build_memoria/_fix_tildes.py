# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Sustituye 'observacion rica' (y variantes) por 'observacion detallada' y
corrige tildes y enes que faltan en los textos del proyecto.
Se ejecuta sobre .py (comentarios, docstrings y literales de texto), .txt y .md."""
import re
from pathlib import Path

ROOT = Path(".")

# Archivos donde intervenimos
TARGETS = [
    "COMANDOS.txt",
    "INSTALACION.txt",
    "README.md",
    "src/callbacks.py",
    "src/doubles_env.py",
    "src/singles_env.py",
    "src/rl_wrapper.py",
    "src/features.py",
    "src/policy.py",
    "src/teams.py",
    "src/poke_env_patch.py",
    "src/__init__.py",
    "train_singles.py",
    "train_doubles.py",
    "play.py",
    "battle_models.py",
    "selfplay_from.py",
    "plot_metrics.py",
    "patch_server_formats.py",
    "test_env.py",
    "check_teams.py",          # FALTABA
]

# ---- 1) Reemplazos especificos (observacion rica -> detallada) ----
# Usamos re.IGNORECASE para capturar tanto "rica" como "RICA" o "Rica".
SPECIFIC = [
    # observacion rica (todas las variantes de caja y con palabras intermedias)
    (r"\bobservaci[óo]n\s+rica\b",                  "observación detallada", re.I),
    (r"\bobservaci[óo]n\s+es\s+rica\b",             "observación es detallada", re.I),
    (r"\bla\s+observaci[óo]n\s+rica\b",             "la observación detallada", re.I),
    (r"\bobservaciones\s+ricas\b",                  "observaciones detalladas", re.I),
    (r"\bembedding\s+rico\b",                       "embedding detallado", re.I),
    # OJO con la 'R' inicial mayuscula
    (r"\bObservaci[óo]n\s+RICA\b",                  "Observación detallada", 0),
]

# ---- 2) Sustituciones de tildes y enes (palabra completa) ----
# Solo palabras españolas no técnicas que aparecen en TEXTO (comentarios,
# docstrings, README, COMANDOS, etc.). NO tocamos nombres de variables porque
# Python las nombra en inglés.
TILDE_MAP = {
    # ortografía básica
    "observacion": "observación",
    "Observacion": "Observación",
    "observaciones": "observaciones",
    "informacion": "información",
    "Informacion": "Información",
    "configuracion": "configuración",
    "Configuracion": "Configuración",
    "conexion": "conexión",
    "Conexion": "Conexión",
    "conexiones": "conexiones",
    "comunicacion": "comunicación",
    "Comunicacion": "Comunicación",
    "ejecucion": "ejecución",
    "Ejecucion": "Ejecución",
    "ejecutalo": "ejecútalo",
    "compilacion": "compilación",
    "Compilacion": "Compilación",
    "documentacion": "documentación",
    "Documentacion": "Documentación",
    "programacion": "programación",
    "Programacion": "Programación",
    "aplicacion": "aplicación",
    "Aplicacion": "Aplicación",
    "instalacion": "instalación",
    "Instalacion": "Instalación",
    "INSTALACION": "INSTALACIÓN",
    "verificacion": "verificación",
    "evaluacion": "evaluación",
    "Evaluacion": "Evaluación",
    "operacion": "operación",
    "actualizacion": "actualización",
    "reconstruccion": "reconstrucción",
    "Reconstruccion": "Reconstrucción",
    "simulacion": "simulación",
    "Simulacion": "Simulación",
    "interaccion": "interacción",
    "accion": "acción",
    "Accion": "Acción",
    "ACCION": "ACCIÓN",
    "acciones": "acciones",
    "Acciones": "Acciones",
    "interpretacion": "interpretación",
    "implementacion": "implementación",
    "Implementacion": "Implementación",
    "construccion": "construcción",
    "Construccion": "Construcción",
    "introduccion": "introducción",
    "Introduccion": "Introducción",
    "resolucion": "resolución",
    "transmision": "transmisión",
    "explicacion": "explicación",
    "decision": "decisión",
    "Decision": "Decisión",
    "decisiones": "decisiones",
    "extension": "extensión",
    "Extension": "Extensión",
    "extensiones": "extensiones",
    "version": "versión",
    "Version": "Versión",
    "versiones": "versiones",
    "definicion": "definición",
    "Definicion": "Definición",
    "edicion": "edición",
    "Edicion": "Edición",
    "publico": "público",
    "publica": "pública",
    "publicas": "públicas",
    "Publico": "Público",
    "metrica": "métrica",
    "metricas": "métricas",
    "Metrica": "Métrica",
    "Metricas": "Métricas",
    "metodo": "método",
    "metodos": "métodos",
    "Metodo": "Método",
    "metodologia": "metodología",
    "logica": "lógica",
    "logico": "lógico",
    "linea": "línea",
    "lineas": "líneas",
    "linealmente": "linealmente",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "tecnico": "técnico",
    "tecnicos": "técnicos",
    "Tecnica": "Técnica",
    "practica": "práctica",
    "practicas": "prácticas",
    "practico": "práctico",
    "Practica": "Práctica",
    "automatico": "automático",
    "automatica": "automática",
    "automaticas": "automáticas",
    "automaticos": "automáticos",
    "automaticamente": "automáticamente",
    "Automatico": "Automático",
    "Automatica": "Automática",
    "Automaticamente": "Automáticamente",
    "asincrono": "asíncrono",
    "asincrona": "asíncrona",
    "Asincrono": "Asíncrono",
    "sincrono": "síncrono",
    "sincrona": "síncrona",
    "Sincrono": "Síncrono",
    "minuscula": "minúscula",
    "minusculas": "minúsculas",
    "mayuscula": "mayúscula",
    "mayusculas": "mayúsculas",
    "MAYUSCULAS": "MAYÚSCULAS",
    "numero": "número",
    "numeros": "números",
    "numerico": "numérico",
    "numerica": "numérica",
    "alfanumerico": "alfanumérico",
    "caracter": "carácter",
    "caracteres": "caracteres",
    "caracteristica": "característica",
    "caracteristicas": "características",
    "Caracteristica": "Característica",
    "unico": "único",
    "unica": "única",
    "Unico": "Único",
    "unicamente": "únicamente",
    "rapido": "rápido",
    "rapida": "rápida",
    "rapidamente": "rápidamente",
    "Rapido": "Rápido",
    "ultimo": "último",
    "ultima": "última",
    "ultimos": "últimos",
    "ultimas": "últimas",
    "Ultimo": "Último",
    "Ultima": "Última",
    "tipico": "típico",
    "tipica": "típica",
    "Tipico": "Típico",
    "basico": "básico",
    "basica": "básica",
    "basicos": "básicos",
    "basicas": "básicas",
    "Basico": "Básico",
    "fisico": "físico",
    "fisica": "física",
    "politica": "política",
    "politicas": "políticas",
    "Politica": "Política",
    "estatico": "estático",
    "estatica": "estática",
    "Estatico": "Estático",
    "analisis": "análisis",
    "Analisis": "Análisis",
    "parametro": "parámetro",
    "parametros": "parámetros",
    "Parametro": "Parámetro",
    "Parametros": "Parámetros",
    "diametro": "diámetro",
    "atomo": "átomo",
    "boton": "botón",
    "botones": "botones",
    "actividad": "actividad",
    "tambien": "también",
    "Tambien": "También",
    "facil": "fácil",
    "Facil": "Fácil",
    "facilmente": "fácilmente",
    "dificil": "difícil",
    "dificiles": "difíciles",
    "Dificil": "Difícil",
    "util": "útil",
    "utiles": "útiles",
    "Util": "Útil",
    "veras": "verás",
    "Veras": "Verás",
    "iras": "irás",
    "podras": "podrás",
    "sera": "será",
    "Sera": "Será",
    "esta": "está",  # PELIGROSO: tambien es pronombre. Lo manejamos por contexto abajo.
    "estan": "están",
    "Estan": "Están",
    "esten": "estén",
    "Esten": "Estén",
    "aqui": "aquí",
    "Aqui": "Aquí",
    "ahi": "ahí",
    "alli": "allí",
    "alla": "allá",
    "cuando": "cuando",
    "como": "como",  # demasiado riesgo, lo dejamos
    "porque": "porque",
    "asi": "así",
    "Asi": "Así",
    # accentuaciones de "más"
    "Mas comandos": "Más comandos",
    "Mas pasos": "Más pasos",
    "Mas opciones": "Más opciones",
    "Mas formal": "Más formal",
    "Mas fuerte": "Más fuerte",
    "Mas largo": "Más largo",
    "Mas rapido": "Más rápido",
    "es mas": "es más",
    "lo mas": "lo más",
    "un mas": "un más",
    "y mas": "y más",
    "no mas": "no más",
    "mas que": "más que",
    "mas de": "más de",
    "mucho mas": "mucho más",
    "mucha mas": "mucha más",
    "muchos mas": "muchos más",
    "muchas mas": "muchas más",
    # otras palabras con ñ
    "anadir": "añadir",
    "Anadir": "Añadir",
    "anade": "añade",
    "Anade": "Añade",
    "anaden": "añaden",
    "anadirlo": "añadirlo",
    "anadirlos": "añadirlos",
    "anadiendo": "añadiendo",
    "anadira": "añadirá",
    "Anadira": "Añadirá",
    "anadido": "añadido",
    "anadida": "añadida",
    "anadidos": "añadidos",
    "anadidas": "añadidas",
    "ano": "año",
    "Ano": "Año",
    "anos": "años",
    "Anos": "Años",
    "pequeno": "pequeño",
    "pequena": "pequeña",
    "pequenos": "pequeños",
    "pequenas": "pequeñas",
    "Pequeno": "Pequeño",
    "Pequena": "Pequeña",
    "ensenar": "enseñar",
    "ensena": "enseña",
    "diseno": "diseño",
    "Diseno": "Diseño",
    "disenado": "diseñado",
    "disenada": "diseñada",
    "espana": "España",
    "Espana": "España",
    "espanol": "español",
    "Espanol": "Español",
    "manana": "mañana",
    # palabras tecnicas/proyecto
    "asegurate": "asegúrate",
    "Asegurate": "Asegúrate",
    "validos": "válidos",
    "Validos": "Válidos",
    "valido": "válido",
    "Valido": "Válido",
    "valida": "válida",
    "validas": "válidas",
    "invalido": "inválido",
    "Invalido": "Inválido",
    "invalidos": "inválidos",
    "Invalidos": "Inválidos",
    "invalida": "inválida",
    "invalidas": "inválidas",
    "desafio": "desafío",
    "Desafio": "Desafío",
    "desafios": "desafíos",
    "Desafios": "Desafíos",
    "rapido": "rápido",
    "Rapido": "Rápido",
    "rapida": "rápida",
    "rapidamente": "rápidamente",
    "Funcion": "Función",
    "funcion": "función",
    "funciones": "funciones",
    "Opcion": "Opción",
    "opcion": "opción",
    "opciones": "opciones",
    "Seleccion": "Selección",
    "seleccion": "selección",
    "selecciones": "selecciones",
    "Representacion": "Representación",
    "representacion": "representación",
    "representaciones": "representaciones",
    "Cancelacion": "Cancelación",
    "cancelacion": "cancelación",
    "Validacion": "Validación",
    "validacion": "validación",
    "validaciones": "validaciones",
    "Modificacion": "Modificación",
    "modificacion": "modificación",
    "Aceleracion": "Aceleración",
    "aceleracion": "aceleración",
    "Atencion": "Atención",
    "atencion": "atención",
    "Generacion": "Generación",
    "generacion": "generación",
    "generaciones": "generaciones",
    "Distribucion": "Distribución",
    "distribucion": "distribución",
    "distribuciones": "distribuciones",
    "Reduccion": "Reducción",
    "reduccion": "reducción",
    "Sustitucion": "Sustitución",
    "sustitucion": "sustitución",
    "Recompilacion": "Recompilación",
    "recompilacion": "recompilación",
    "Iteracion": "Iteración",
    "iteracion": "iteración",
    "iteraciones": "iteraciones",
    "Configuracion": "Configuración",
    "rapidos": "rápidos",
    "rapidas": "rápidas",
    "cuantos": "cuántos",  # heuristico: en mayoria de casos del proyecto es interrogativo
    "Cuantos": "Cuántos",
    "cuanto": "cuánto",
    "Cuanto": "Cuánto",
    "cuanta": "cuánta",
    "cuantas": "cuántas",
    "ejecutar": "ejecutar",  # no toca
    "informacion": "información",
    "Informacion": "Información",
    "operaciones": "operaciones",
    "estandar": "estándar",
    "Estandar": "Estándar",
    "ejecucion": "ejecución",
    "Pokemon": "Pokémon",  # se sobrescribe arriba para frases con contexto; en .py solo en docstrings/comentarios
    "ejecutalo": "ejecútalo",
    "cierrala": "ciérrala",
    "Cierrala": "Ciérrala",
    "abrelo": "ábrelo",
    "lanzalo": "lánzalo",
    "Lanzalo": "Lánzalo",
    "arrancalo": "arráncalo",
    "Arrancalo": "Arráncalo",
    "reinstalalo": "reinstálalo",
    "Reinstalalo": "Reinstálalo",
    "renombralo": "renómbralo",
    "Renombralo": "Renómbralo",
    "abreviado": "abreviado",
    # criterios y dependencias
    "ningun": "ningún",
    "Ningun": "Ningún",
    "algun": "algún",
    "Algun": "Algún",
    "segun": "según",
    "Segun": "Según",
    # texto reset
    "Codigo": "Código",
    "codigo": "código",
    "CODIGO": "CÓDIGO",
    # plurales de palabras corrientes
    "veran": "verán",
    "mas frecuente": "más frecuente",
    "Mas frecuente": "Más frecuente",
    "deben": "deben",
    "deberian": "deberían",
    "podrian": "podrían",
    "lo demas": "lo demás",
    "los demas": "los demás",
    "las demas": "las demás",
    # Pokemon -> Pokémon en texto (NO en nombre de carpeta/comando)
    "Pokemon Showdown": "Pokémon Showdown",
    "Pokemon VGC": "Pokémon VGC",
    "del Pokemon": "del Pokémon",
    "del pokemon": "del Pokémon",
    "los Pokemon": "los Pokémon",
    "los pokemon": "los Pokémon",
    "combates Pokemon": "combates Pokémon",
    "combate Pokemon": "combate Pokémon",
    "combates pokemon": "combates Pokémon",
    "de Pokemon": "de Pokémon",
}

# Palabras intencionadamente NO tocadas: las dejamos sin tilde porque son
# nombres de variables, identificadores, o porque cambiarlas rompe codigo.
# (la version global del paquete __version__, version=... como kwarg, etc.)
# Para version como kwarg de codigo Python, el reemplazo se hace solo si esta
# rodeado de palabras espanolas (lo gestiona la heuristica de comentario/docstring).

# ---- Heuristica para .py: solo modificar dentro de comentarios y docstrings ----
def fix_python(text: str) -> tuple[str, int]:
    """Reemplaza solo dentro de comentarios (# ...) y docstrings ('''...''' o
    \"\"\"...\"\"\"). El codigo (variables y funciones) queda intacto."""
    changes = 0
    out_parts = []
    i = 0
    n = len(text)
    while i < n:
        # Buscar el siguiente comentario o docstring
        ch = text[i]
        # Triple comilla doble
        if text[i:i+3] == '"""':
            j = text.find('"""', i+3)
            if j == -1:
                out_parts.append(text[i:]); break
            body = text[i:j+3]
            new_body, k = apply_replacements(body)
            changes += k
            out_parts.append(new_body)
            i = j + 3
        elif text[i:i+3] == "'''":
            j = text.find("'''", i+3)
            if j == -1:
                out_parts.append(text[i:]); break
            body = text[i:j+3]
            new_body, k = apply_replacements(body)
            changes += k
            out_parts.append(new_body)
            i = j + 3
        elif ch == '#':
            j = text.find('\n', i)
            if j == -1: j = n
            body = text[i:j]
            new_body, k = apply_replacements(body)
            changes += k
            out_parts.append(new_body)
            i = j
        elif ch in ('"', "'"):
            # Cadena de comillas simples: tambien aplicamos (suelen ser mensajes)
            q = ch
            j = i + 1
            while j < n and text[j] != q:
                if text[j] == '\\' and j+1 < n:
                    j += 2
                else:
                    j += 1
            if j >= n:
                out_parts.append(text[i:]); break
            body = text[i:j+1]
            new_body, k = apply_replacements(body)
            changes += k
            out_parts.append(new_body)
            i = j + 1
        else:
            out_parts.append(ch)
            i += 1
    return "".join(out_parts), changes


def apply_replacements(text: str) -> tuple[str, int]:
    """Aplica los reemplazos especificos y el mapa de tildes."""
    changes = 0
    for item in SPECIFIC:
        if len(item) == 3:
            pat, repl, flags = item
        else:
            pat, repl = item
            flags = 0
        new, k = re.subn(pat, repl, text, flags=flags)
        if k:
            text = new
            changes += k
    for word, repl in TILDE_MAP.items():
        if word == repl:
            continue
        # Reemplazo con frontera de palabra (no rompe tokens mas largos)
        pat = r'\b' + re.escape(word) + r'\b'
        new, k = re.subn(pat, repl, text)
        if k:
            text = new
            changes += k
    return text, changes


def fix_plain(text: str) -> tuple[str, int]:
    return apply_replacements(text)


# ---- Procesamos cada archivo ----
total = 0
for rel in TARGETS:
    p = ROOT / rel
    if not p.exists():
        print(f"AVISO: no existe {rel}")
        continue
    original = p.read_text(encoding="utf-8")
    if p.suffix == ".py":
        new, k = fix_python(original)
    else:
        new, k = fix_plain(original)
    if k > 0 and new != original:
        p.write_text(new, encoding="utf-8")
        print(f"  {rel}: {k} cambios")
        total += k
    else:
        print(f"  {rel}: sin cambios")

print(f"\nTotal de sustituciones: {total}")
