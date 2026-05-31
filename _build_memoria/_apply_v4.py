# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Aplica sobre v3: amplia la seccion 4 y sustituye la tabla de metodologia por
prosa; anade citas APA de los trabajos de Pokemon en 3.3 y sus referencias."""
import re, sys

PATH = "_build_memoria/unpacked3/word/document.xml"
s = open(PATH, encoding="utf-8").read()
orig_len = len(s)

def body_par(pid, text):
    return (
        '    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
        'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
        '      <w:pPr>\n'
        '        <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>\n'
        '        <w:jc w:val="both"/>\n'
        '        <w:rPr/>\n'
        '      </w:pPr>\n'
        '      <w:r>\n'
        '        <w:rPr>\n'
        '          <w:rtl w:val="0"/>\n'
        '        </w:rPr>\n'
        '        <w:t xml:space="preserve">%s</w:t>\n'
        '      </w:r>\n'
        '    </w:p>' % (pid, text)
    )

def ref_par(pid, text):
    return (
        '    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
        'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
        '      <w:pPr>\n'
        '        <w:spacing w:after="120" w:line="276" w:lineRule="auto"/>\n'
        '        <w:ind w:left="720" w:hanging="720"/>\n'
        '        <w:jc w:val="both"/>\n'
        '        <w:rPr/>\n'
        '      </w:pPr>\n'
        '      <w:r>\n'
        '        <w:rPr>\n'
        '          <w:rtl w:val="0"/>\n'
        '        </w:rPr>\n'
        '        <w:t xml:space="preserve">%s</w:t>\n'
        '      </w:r>\n'
        '    </w:p>' % (pid, text)
    )

# ---- 1) Sustituir parrafo introductorio + tabla de metodologia por prosa ----
A = ("En conjunto, el trabajo combinó varios enfoques metodológicos que conviene "
     "hacer explícitos. Tuvo una vertiente documental en su fase inicial, con el "
     "estudio del estado de la cuestión y de la documentación de las herramientas "
     "(apartado 3). El núcleo, sin embargo, fue experimental: el conocimiento se "
     "generó entrenando y evaluando agentes, y no razonando en abstracto. Ese "
     "trabajo experimental se organizó de forma inductiva, de lo particular a lo "
     "general —validando primero el caso sencillo de singles antes de generalizar "
     "a dobles VGC—, y de forma comparativa, enfrentando entre sí distintas "
     "configuraciones (las arquitecturas MLP y Transformer, o los distintos "
     "regímenes de oponente) y midiéndolas frente a los baselines. En todos los "
     "casos el análisis fue eminentemente cuantitativo, apoyado en la tasa de "
     "victorias y en las métricas de entrenamiento ya descritas.")
B = ("Para que esas comparaciones resultaran informativas se procuró aislar el "
     "efecto de cada factor: al contrastar dos arquitecturas o dos tipos de "
     "oponente, el resto de elementos —la representación del estado, la función de "
     "recompensa y los hiperparámetros— se mantenía fijo, de modo que las "
     "diferencias observadas pudieran atribuirse al factor en estudio y no a una "
     "variación incontrolada. Esta lógica, próxima a la de un estudio de ablación, "
     "es la que da sentido a entrenar las variantes por separado y enfrentarlas "
     "después en igualdad de condiciones.")
C = ("Conviene, por último, reconocer los límites de esta metodología. La fuerte "
     "componente aleatoria de los combates Pokémon —la precisión de los "
     "movimientos, los golpes críticos o los efectos secundarios— introduce ruido "
     "en cualquier medición; ese ruido se mitiga promediando sobre muchos "
     "combates, pero no llega a eliminarse. Además, el cómputo se realizó "
     "principalmente por CPU, lo que acotó tanto la duración de los entrenamientos "
     "como el número de repeticiones (semillas) que fue viable ejecutar. Por ello, "
     "los resultados que se presentan deben leerse como indicativos de tendencias "
     "y no como una medida exhaustiva del rendimiento máximo alcanzable por el "
     "enfoque.")
NEW = "\n".join([body_par("0A000080", A), body_par("0A000081", B), body_par("0A000082", C)])

marker = "La siguiente tabla resume los tipos de metodología"
i = s.index(marker)
pstart = s.rfind("<w:p ", 0, i)
line_start = s.rfind("\n", 0, pstart) + 1
tbl_end = s.index("</w:tbl>", i) + len("</w:tbl>")
# Sanidad: el bloque eliminado debe contener la tabla de metodologia
chunk = s[line_start:tbl_end]
assert "<w:tbl>" in chunk and "Documental" in chunk and "Cuantitativa" in chunk, "bloque tabla incorrecto"
s = s[:line_start] + NEW + s[tbl_end:]
print("Tabla de metodologia sustituida por prosa (3 parrafos).")

# ---- 2) Citas APA en el parrafo de 3.3 (trabajos previos de Pokemon) ----
c1 = ("rentable a largo plazo. Otros han abordado",
      "rentable a largo plazo (Simões et al., 2020). Otros han abordado")
c2 = ("enfrentándose a versiones de sí mismo. El presente trabajo",
      "enfrentándose a versiones de sí mismo (Huang y Lee, 2019). El presente trabajo")
for old, new in (c1, c2):
    assert s.count(old) == 1, "cita: ancla no unica -> %r (%d)" % (old, s.count(old))
    s = s.replace(old, new)
print("Citas (Simões et al., 2020) y (Huang y Lee, 2019) insertadas en 3.3.")

# ---- 3) Referencias APA en seccion 9 (orden alfabetico) ----
REF_HUANG = ("Huang, D., &amp; Lee, S. (2019). A self-play policy optimization approach "
             "to battling Pokémon. En 2019 IEEE Conference on Games (CoG) (pp. 1–4). IEEE.")
REF_SIMOES = ("Simões, D., Reis, S., Lau, N., &amp; Reis, L. P. (2020). Competitive deep "
              "reinforcement learning over a Pokémon battling simulator. En 2020 IEEE "
              "International Conference on Autonomous Robot Systems and Competitions "
              "(ICARSC) (pp. 40–45). IEEE.")

def insert_ref_before(marker_text, ref_xml):
    j = s_holder[0].index(marker_text)
    ps = s_holder[0].rfind("<w:p ", 0, j)
    ls = s_holder[0].rfind("\n", 0, ps) + 1
    s_holder[0] = s_holder[0][:ls] + ref_xml + "\n" + s_holder[0][ls:]

s_holder = [s]
insert_ref_before("Huang, S., &amp; Ontañón, S. (2022)", ref_par("0A000090", REF_HUANG))
insert_ref_before("Sutton, R. S., &amp; Barto, A. G. (2018)", ref_par("0A000091", REF_SIMOES))
s = s_holder[0]
print("Referencias APA de Huang y Lee (2019) y Simões et al. (2020) anadidas en orden.")

open(PATH, "w", encoding="utf-8").write(s)
print("OK. delta chars:", len(s) - orig_len)
