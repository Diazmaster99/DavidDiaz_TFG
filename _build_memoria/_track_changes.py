# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Construye una version con CONTROL DE CAMBIOS (tracked changes) del diff
(2) -> v4, sobre una copia limpia de (2). Autor: Claude."""
import re

PATH = "_build_memoria/unpacked_tc/word/document.xml"
DATE = "2026-05-27T12:00:00Z"
AUTHOR = "Claude"
s = open(PATH, encoding="utf-8").read()

_idc = [9000]
def nid():
    _idc[0] += 1
    return _idc[0]

# ---------------- builders de INSERCIONES ----------------
def _ins_open():
    return '<w:ins w:id="%d" w:author="%s" w:date="%s">' % (nid(), AUTHOR, DATE)
def _markpar_ins():
    return '<w:ins w:id="%d" w:author="%s" w:date="%s"/>' % (nid(), AUTHOR, DATE)
def _markpar_del():
    return '<w:del w:id="%d" w:author="%s" w:date="%s"/>' % (nid(), AUTHOR, DATE)

def ins_body(pid, text):
    return ('    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
            'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
            '      <w:pPr>\n'
            '        <w:spacing w:after="160" w:line="276" w:lineRule="auto"/>\n'
            '        <w:jc w:val="both"/>\n'
            '        <w:rPr>%s</w:rPr>\n'
            '      </w:pPr>\n'
            '      %s\n'
            '        <w:r>\n          <w:rPr>\n            <w:rtl w:val="0"/>\n          </w:rPr>\n'
            '          <w:t xml:space="preserve">%s</w:t>\n        </w:r>\n'
            '      </w:ins>\n'
            '    </w:p>' % (pid, _markpar_ins(), _ins_open(), text))

def ins_heading3(pid, text):
    return ('    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
            'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
            '      <w:pPr>\n'
            '        <w:pStyle w:val="Heading3"/>\n'
            '        <w:rPr>%s<w:color w:val="000000"/></w:rPr>\n'
            '      </w:pPr>\n'
            '      %s\n'
            '        <w:r>\n          <w:rPr>\n            <w:color w:val="000000"/>\n            <w:rtl w:val="0"/>\n          </w:rPr>\n'
            '          <w:t xml:space="preserve">%s</w:t>\n        </w:r>\n'
            '      </w:ins>\n'
            '    </w:p>' % (pid, _markpar_ins(), _ins_open(), text))

def ins_listitem(pid, lead, rest):
    pbdr = ('<w:pBdr><w:top w:space="0" w:sz="0" w:val="nil"/><w:left w:space="0" w:sz="0" w:val="nil"/>'
            '<w:bottom w:space="0" w:sz="0" w:val="nil"/><w:right w:space="0" w:sz="0" w:val="nil"/>'
            '<w:between w:space="0" w:sz="0" w:val="nil"/></w:pBdr>')
    boldrun = ('<w:r><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/>'
               '<w:b w:val="1"/><w:bCs w:val="1"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:rtl w:val="0"/></w:rPr>'
               '<w:t xml:space="preserve">%s</w:t></w:r>' % lead)
    normrun = ('<w:r><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/>'
               '<w:b w:val="0"/><w:bCs w:val="0"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:rtl w:val="0"/></w:rPr>'
               '<w:t xml:space="preserve">%s</w:t></w:r>' % rest)
    return ('    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
            'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
            '      <w:pPr>\n        <w:numPr><w:ilvl w:val="0"/><w:numId w:val="6"/></w:numPr>\n'
            '        %s\n        <w:spacing w:after="80" w:before="0" w:line="276" w:lineRule="auto"/>\n'
            '        <w:ind w:left="720" w:right="0" w:hanging="360"/>\n        <w:jc w:val="both"/>\n'
            '        <w:rPr>%s</w:rPr>\n      </w:pPr>\n'
            '      %s%s%s</w:ins>\n    </w:p>'
            % (pid, pbdr, _markpar_ins(), _ins_open(), boldrun, normrun))

def ins_ref(pid, text):
    return ('    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
            'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
            '      <w:pPr>\n        <w:spacing w:after="120" w:line="276" w:lineRule="auto"/>\n'
            '        <w:ind w:left="720" w:hanging="720"/>\n        <w:jc w:val="both"/>\n'
            '        <w:rPr>%s</w:rPr>\n      </w:pPr>\n'
            '      %s\n        <w:r>\n          <w:rPr>\n            <w:rtl w:val="0"/>\n          </w:rPr>\n'
            '          <w:t xml:space="preserve">%s</w:t>\n        </w:r>\n      </w:ins>\n    </w:p>'
            % (pid, _markpar_ins(), _ins_open(), text))

# ---------------- transformacion a DELECION ----------------
def mark_deleted(block):
    head, sep, tail = block.partition('</w:pPr>')
    if sep:  # tiene pPr
        if '<w:rPr/>' in head:
            head = head.replace('<w:rPr/>', '<w:rPr>%s</w:rPr>' % _markpar_del(), 1)
        elif '<w:rPr>' in head:
            head = head.replace('<w:rPr>', '<w:rPr>%s' % _markpar_del(), 1)
        else:
            head = head.replace('</w:pPr', '<w:rPr>%s</w:rPr></w:pPr' % _markpar_del(), 1) if False else head + ''
            # si no hay rPr en pPr, lo anadimos justo antes de cerrar pPr
            head = head[:head.rfind('<')] if False else head
        block = head + sep + tail
    # t -> delText
    block = (block.replace('<w:t xml:space="preserve">', '<w:delText xml:space="preserve">')
                  .replace('<w:t>', '<w:delText>').replace('</w:t>', '</w:delText>'))
    # envolver cada run en <w:del>
    block = re.sub(r'<w:r>.*?</w:r>',
                   lambda m: '<w:del w:id="%d" w:author="%s" w:date="%s">%s</w:del>' % (nid(), AUTHOR, DATE, m.group(0)),
                   block, flags=re.S)
    return block

def enclosing_p(marker):
    idx = s_index(marker)
    ps = S[0].rfind('<w:p ', 0, idx)
    pe = S[0].index('</w:p>', idx) + len('</w:p>')
    return ps, pe

S = [s]
def s_index(m):
    return S[0].index(m)

def replace_block(start, end, new):
    S[0] = S[0][:start] + new + S[0][end:]

def insert_before_marker(marker, new_xml):
    idx = s_index(marker)
    ps = S[0].rfind('<w:p ', 0, idx)
    ls = S[0].rfind('\n', 0, ps) + 1
    S[0] = S[0][:ls] + new_xml + '\n' + S[0][ls:]

# ===================== CONTENIDOS INSERTADOS =====================
VIZDOOM = ("No todos estos hitos parten de una representación simbólica del estado. En los "
    "videojuegos en primera persona, por ejemplo, se ha aplicado el aprendizaje por refuerzo "
    "directamente sobre los píxeles de la pantalla —como en los trabajos sobre el shooter "
    "Doom—, donde el agente debe percibir un entorno tridimensional e interpretarlo a partir "
    "de la imagen para decidir hacia dónde moverse o cuándo disparar. Estos enfoques basados "
    "en visión, que emplean redes convolucionales y técnicas como el salto de fotogramas para "
    "acelerar el entrenamiento, contrastan con el adoptado en este trabajo, en el que el "
    "estado del combate se codifica de forma simbólica (estadísticas, tipos, efectividades) en "
    "lugar de a partir de imágenes. Aun así, ambos comparten la misma idea de fondo: un agente "
    "que mejora su comportamiento interactuando con el entorno y maximizando una recompensa.")
PRIORWORK = ("La aplicación del aprendizaje por refuerzo a los combates Pokémon no es nueva: "
    "existen trabajos académicos previos que han explorado este dominio. Algunos optaron por "
    "entornos de combate simplificados —con equipos reducidos e información parcial— para "
    "aislar el aprendizaje del razonamiento sobre tipos y efectividades, y mostraron que un "
    "agente puede aprender a renunciar a una ventaja inmediata (por ejemplo, sacrificar un "
    "turno de ataque para cambiar a un Pokémon con un emparejamiento de tipos más favorable) "
    "en favor de una estrategia más rentable a largo plazo (Simões et al., 2020). Otros han "
    "abordado el problema mediante optimización de la política por self-play, haciendo que el "
    "agente progrese enfrentándose a versiones de sí mismo (Huang y Lee, 2019). El presente "
    "trabajo se inscribe en esa línea, pero se distingue en dos aspectos: opera sobre el "
    "simulador completo y estándar, sin simplificar las reglas del juego, y aborda directamente "
    "el formato dobles VGC, sensiblemente más complejo que el combate individual al que suelen "
    "limitarse esos estudios.")
M4A = ("En conjunto, el trabajo combinó varios enfoques metodológicos que conviene hacer "
    "explícitos. Tuvo una vertiente documental en su fase inicial, con el estudio del estado "
    "de la cuestión y de la documentación de las herramientas (apartado 3). El núcleo, sin "
    "embargo, fue experimental: el conocimiento se generó entrenando y evaluando agentes, y no "
    "razonando en abstracto. Ese trabajo experimental se organizó de forma inductiva, de lo "
    "particular a lo general —validando primero el caso sencillo de singles antes de "
    "generalizar a dobles VGC—, y de forma comparativa, enfrentando entre sí distintas "
    "configuraciones (las arquitecturas MLP y Transformer, o los distintos regímenes de "
    "oponente) y midiéndolas frente a los baselines. En todos los casos el análisis fue "
    "eminentemente cuantitativo, apoyado en la tasa de victorias y en las métricas de "
    "entrenamiento ya descritas.")
M4B = ("Para que esas comparaciones resultaran informativas se procuró aislar el efecto de "
    "cada factor: al contrastar dos arquitecturas o dos tipos de oponente, el resto de "
    "elementos —la representación del estado, la función de recompensa y los hiperparámetros— "
    "se mantenía fijo, de modo que las diferencias observadas pudieran atribuirse al factor en "
    "estudio y no a una variación incontrolada. Esta lógica, próxima a la de un estudio de "
    "ablación, es la que da sentido a entrenar las variantes por separado y enfrentarlas "
    "después en igualdad de condiciones.")
M4C = ("Conviene, por último, reconocer los límites de esta metodología. La fuerte componente "
    "aleatoria de los combates Pokémon —la precisión de los movimientos, los golpes críticos o "
    "los efectos secundarios— introduce ruido en cualquier medición; ese ruido se mitiga "
    "promediando sobre muchos combates, pero no llega a eliminarse. Además, el cómputo se "
    "realizó principalmente por CPU, lo que acotó tanto la duración de los entrenamientos como "
    "el número de repeticiones (semillas) que fue viable ejecutar. Por ello, los resultados que "
    "se presentan deben leerse como indicativos de tendencias y no como una medida exhaustiva "
    "del rendimiento máximo alcanzable por el enfoque.")
R37_1 = ("Los entrenamientos prolongados de dobles encadenan miles de combates sobre una "
    "conexión por websocket con el servidor local; a lo largo de tantas horas, los fallos de "
    "comunicación y los bloqueos resultan inevitables, y el objetivo de esta capa de robustez "
    "fue que un incidente puntual no abortara una sesión de varias horas. La primera fuente de "
    "problemas era el propio servidor: la versión estándar sufría bloqueos esporádicos por su "
    "gestión de las salas y de los tiempos de espera en los combates largos de dobles. Por ello "
    "se adoptó una variante adaptada del servidor que corrige ese comportamiento y se le "
    "añadieron los formatos VGC vigentes que faltaban. Como salvaguarda adicional se activó el "
    "temporizador de combate del propio servidor, de modo que una batalla atascada termine por "
    "tiempo en lugar de quedarse esperando indefinidamente.")
R37_2 = ("Sobre esa base, el entorno incorpora una capa de recuperación en el lado del cliente. "
    "Cuando el desafío entre los dos agentes no llega a establecerse, poke-env lanza un error; "
    "para detectarlo cuanto antes se redujo el tiempo de espera del desafío (de un minuto a "
    "unos pocos segundos, de sobra holgado en una conexión local) y se reintenta reconstruyendo "
    "el entorno con una conexión limpia. Antes de cada reinicio se cierran de forma preventiva "
    "los combates que pudieran haber quedado pendientes, lo que evita que el simulador rechace "
    "el reinicio por tener batallas sin terminar. Y, dentro de un turno, un vigilante (watchdog) "
    "con un tiempo máximo abandona el combate si lo detecta atascado y dispara la reconstrucción "
    "del entorno, sin esperar al temporizador del servidor.")
R37_3 = ("La reconstrucción del entorno exigió un cuidado particular: el cierre por defecto del "
    "entorno esperaba a que terminara la tarea de desafío pendiente, lo que —precisamente cuando "
    "ese desafío estaba colgado— bloqueaba el proceso de forma indefinida; fue necesario cerrar "
    "el entorno sin esperar a dicha tarea para que la propia recuperación no se congelara. A "
    "todo lo anterior se suma una validación previa de los equipos, que descarta antes de "
    "empezar los que no son legales en el formato. El conjunto de estas medidas —servidor "
    "adaptado, temporizadores, reintentos, cierre preventivo, watchdog y reconstrucción— "
    "permitió completar entrenamientos largos de forma fiable. No son infalibles y, por la "
    "propia naturaleza del sistema, algún error puede seguir apareciendo, pero con una "
    "frecuencia mucho menor.")
REF_HUANG = ("Huang, D., &amp; Lee, S. (2019). A self-play policy optimization approach to "
    "battling Pokémon. En 2019 IEEE Conference on Games (CoG) (pp. 1–4). IEEE.")
REF_SIMOES = ("Simões, D., Reis, S., Lau, N., &amp; Reis, L. P. (2020). Competitive deep "
    "reinforcement learning over a Pokémon battling simulator. En 2020 IEEE International "
    "Conference on Autonomous Robot Systems and Competitions (ICARSC) (pp. 40–45). IEEE.")

# ===================== APLICAR =====================
# I1: VizDoom al final de 3.2 (antes del encabezado 3.3)
insert_before_marker("3.3. Pokémon como dominio de IA y el competitivo VGC", ins_body("0B000001", VIZDOOM))
# I2: trabajos previos al final de 3.3 (antes del encabezado 3.4)
insert_before_marker("3.4. Herramientas y trabajos de referencia", ins_body("0B000002", PRIORWORK))

# D1+D2+I3: borrar frase "La siguiente tabla..." + tabla; insertar 3 parrafos prosa
idx = s_index("La siguiente tabla resume los tipos de metodología")
ps = S[0].rfind('<w:p ', 0, idx)
ls = S[0].rfind('\n', 0, ps) + 1
pe = S[0].index('</w:p>', idx) + len('</w:p>')
sent_block = S[0][ps:pe]
tbl_start = S[0].index('<w:tbl>', pe)
tbl_end = S[0].index('</w:tbl>', tbl_start) + len('</w:tbl>')
tbl_block = S[0][tbl_start:tbl_end]
assert 'Documental' in tbl_block and 'Cuantitativa' in tbl_block
# marcar tabla como borrada: cada <w:p> interno + filas
tbl_del = re.sub(r'<w:p\b.*?</w:p>', lambda m: mark_deleted(m.group(0)), tbl_block, flags=re.S)
tbl_del = re.sub(r'</w:trPr>', lambda m: '%s</w:trPr>' % _markpar_del(), tbl_del)
new_block = (mark_deleted(sent_block) + '\n' + ins_body("0B000010", M4A) + '\n'
             + ins_body("0B000011", M4B) + '\n' + ins_body("0B000012", M4C))
# reemplazar desde inicio de la frase hasta fin de tabla
S[0] = S[0][:ls] + new_block + '\n    ' + tbl_del + S[0][tbl_end:]

# D3+I4+I5: borrar parrafo viejo 5.3.7 (texto + titulo inline 5.3.8); insertar 3 parrafos + heading 5.3.8
idx = s_index("Los entrenamientos prolongados de dobles requieren miles")
ps = S[0].rfind('<w:p ', 0, idx)
ls = S[0].rfind('\n', 0, ps) + 1
pe = S[0].index('</w:p>', idx) + len('</w:p>')
old37 = S[0][ps:pe]
new37 = (mark_deleted(old37) + '\n' + ins_body("0B000020", R37_1) + '\n' + ins_body("0B000021", R37_2)
         + '\n' + ins_body("0B000022", R37_3) + '\n' + ins_heading3("0B000023", "5.3.8. Dificultades técnicas encontradas y soluciones"))
S[0] = S[0][:ls] + new37 + S[0][pe:]

# D4: borrar bullet "Reinicios y combates colgados"
idx = s_index("Reinicios y combates colgados.")
ps = S[0].rfind('<w:p ', 0, idx)
ls = S[0].rfind('\n', 0, ps) + 1
pe = S[0].index('</w:p>', idx) + len('</w:p>')
S[0] = S[0][:ls] + mark_deleted(S[0][ps:pe]) + S[0][pe:]

# I6: 2 lineas de futuro antes de "Entrenamiento frente a equipos diversos"
items = (ins_listitem("0B000030", "Aceleración mediante vectorización del entorno. ",
            "Ejecutar varios combates en paralelo (entornos vectorizados), una técnica estándar "
            "en Stable-Baselines3, permitiría recoger experiencia mucho más deprisa y acortar de "
            "forma notable los tiempos de entrenamiento, que en este trabajo fueron el principal "
            "factor limitante al entrenar por CPU. Es una vía complementaria a la aceleración por GPU.")
         + '\n' +
         ins_listitem("0B000031", "Currículo de oponentes de dificultad creciente. ",
            "En lugar de fijar un único tipo de rival, entrenar contra oponentes progresivamente "
            "más fuertes —del jugador aleatorio al de máxima potencia, después al heurístico y "
            "finalmente al self-play— de modo que el agente consolide lo básico antes de afrontar "
            "rivales más exigentes, a la manera de un currículo de aprendizaje que evita "
            "estancamientos tempranos."))
insert_before_marker("Entrenamiento frente a equipos diversos.", items)

# I7: referencias en orden alfabetico
insert_before_marker("Huang, S., &amp; Ontañón, S. (2022)", ins_ref("0B000040", REF_HUANG))
insert_before_marker("Sutton, R. S., &amp; Barto, A. G. (2018)", ins_ref("0B000041", REF_SIMOES))

open(PATH, "w", encoding="utf-8").write(S[0])
print("Cambios marcados. ins:", S[0].count('<w:ins '), " del:", S[0].count('<w:del '))
