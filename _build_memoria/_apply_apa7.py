# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Aplica formato APA 7 (opcion B) al documento desempaquetado:
   1) Portada APA 7 (centrada, sin logo ni cabecera UDIT).
   2) Interlineado doble (line=480, lineRule=auto).
   3) Alineacion izquierda (jc=left) en lugar de justificado.
   4) Sangria de primera linea (firstLine=720, 1.27cm) en parrafos de cuerpo.
   5) Eliminar la numeracion ("1.", "1.1.", "5.3.7.", ...) de los encabezados.
   6) Paginacion arriba a la derecha (header) y footer limpio."""
import re
from pathlib import Path

UNPACKED = Path("_build_memoria/unpacked_apa")
DOC      = UNPACKED / "word/document.xml"
STYLES   = UNPACKED / "word/styles.xml"
HEADER1  = UNPACKED / "word/header1.xml"
FOOTER1  = UNPACKED / "word/footer1.xml"
HEADER2  = UNPACKED / "word/header2.xml"
FOOTER2  = UNPACKED / "word/footer2.xml"

# ===================== DOCUMENT.XML =====================
xml = DOC.read_text(encoding="utf-8")
orig_len = len(xml)

# ---- 1) Sustituir la PORTADA por una APA 7 ----
# La portada va desde el primer parrafo del body hasta justo antes del primer
# encabezado "Índice" (primer Heading1).
body_open = xml.index("<w:body>") + len("<w:body>")
indice_marker = xml.index("Índice", body_open)
# Retrocede hasta el <w:p ...> que contiene "Índice".
p_indice_start = xml.rfind("<w:p ", 0, indice_marker)

def cover_par(pid, text, *, bold=False, size=22):
    """Parrafo centrado, doble interlineado, con tamano configurable. APA 7
    pide la portada centrada y doble espacio."""
    bold_xml = '<w:b w:val="1"/><w:bCs w:val="1"/>' if bold else ''
    return ('    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
            'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
            '      <w:pPr>\n'
            '        <w:spacing w:after="0" w:line="480" w:lineRule="auto"/>\n'
            '        <w:jc w:val="center"/>\n        <w:rPr/>\n'
            '      </w:pPr>\n'
            '      <w:r><w:rPr>%s<w:sz w:val="%d"/><w:szCs w:val="%d"/>'
            '<w:rtl w:val="0"/></w:rPr><w:t xml:space="preserve">%s</w:t></w:r>\n'
            '    </w:p>' % (pid, bold_xml, size, size, text))

def cover_blank(pid):
    """Linea en blanco (doble espacio) para separar bloques de la portada."""
    return ('    <w:p w:rsidR="00000000" w:rsidDel="00000000" w:rsidP="00000000" '
            'w:rsidRDefault="00000000" w:rsidRPr="00000000" w14:paraId="%s">\n'
            '      <w:pPr><w:spacing w:after="0" w:line="480" w:lineRule="auto"/>'
            '<w:jc w:val="center"/><w:rPr/></w:pPr>\n    </w:p>' % pid)

# APA 7 (estudiante): titulo a unas lineas del margen superior, en negrita y
# centrado; luego autor, institucion, programa, asignatura/trabajo, tutor y
# fecha, cada uno en su linea con doble espacio.
portada = "\n".join([
    cover_blank("0D000001"),
    cover_blank("0D000002"),
    cover_blank("0D000003"),
    cover_par("0D000010",
              "Diseño y entrenamiento de un agente de aprendizaje por refuerzo "
              "para combates dobles de Pokémon en formato VGC",
              bold=True, size=28),
    cover_blank("0D000011"),
    cover_par("0D000020", "David Díaz Espinosa de los Monteros", size=24),
    cover_par("0D000021", "Universidad de Diseño, Innovación y Tecnología (UDIT)", size=24),
    cover_par("0D000022", "Grado en Diseño y Desarrollo de Videojuegos — Especialidad de Programación", size=24),
    cover_par("0D000023", "Trabajo de Fin de Grado", size=24),
    cover_par("0D000024", "Tutor: [Nombre del tutor/a]", size=24),
    cover_par("0D000025", "Proyecto grupal: Hortensia Studios", size=24),
    cover_par("0D000026", "[día] de [mes] de 2026", size=24),
])

xml = xml[:body_open] + "\n" + portada + "\n" + xml[p_indice_start:]
print("Portada APA 7 sustituida.")

# ---- 2) Interlineado doble en todos los parrafos ----
n_lines = xml.count('w:line="276"')
xml = xml.replace('w:line="276"', 'w:line="480"')
print(f"Interlineado doble aplicado en {n_lines} parrafos.")

# ---- 3) Alineacion izquierda (APA 7 pide flush-left, no justificado) ----
n_jc = xml.count('<w:jc w:val="both"/>')
xml = xml.replace('<w:jc w:val="both"/>', '<w:jc w:val="left"/>')
print(f"Alineacion izquierda aplicada en {n_jc} parrafos.")

# ---- 4) Sangria de primera linea (1.27 cm = 720 twips) ----
# Solo en parrafos de cuerpo "normales": pPr con spacing + jc=left + rPr/.
# Excluye listas (numPr), encabezados (pStyle), referencias (ind hanging), y
# huecos de figura (con shd). Patron muy especifico para no estropear nada.
body_pPr_pattern = re.compile(
    r'(<w:pPr>\s*'
    r'<w:spacing w:after="\d+" w:line="480" w:lineRule="auto"/>\s*'
    r'<w:jc w:val="left"/>\s*'
    r'<w:rPr/>\s*'
    r'</w:pPr>)',
    re.S
)
def add_indent(m):
    inner = m.group(1)
    # Insertar <w:ind w:firstLine="720"/> antes del cierre </w:pPr>, justo
    # despues de <w:jc .../>.
    return inner.replace(
        '<w:jc w:val="left"/>',
        '<w:ind w:firstLine="720"/>\n        <w:jc w:val="left"/>'
    )
xml, n_ind = body_pPr_pattern.subn(add_indent, xml)
print(f"Sangria de primera linea anadida en {n_ind} parrafos de cuerpo.")

# ---- 5) Quitar numeracion de encabezados (Heading1/2/3) ----
heading_par_pattern = re.compile(
    r'(<w:p\b[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="Heading[1-3]"(?:(?!</w:p>).)*?</w:p>)',
    re.S
)
num_prefix = re.compile(r'^(\d+(?:\.\d+)*\.?\s+)')
def strip_heading_num(m):
    block = m.group(1)
    def fix_t(tm):
        text = tm.group(1)
        new = num_prefix.sub('', text)
        return f'<w:t xml:space="preserve">{new}</w:t>'
    return re.sub(r'<w:t[^>]*>([^<]*)</w:t>', fix_t, block, count=1)
xml, n_hd = heading_par_pattern.subn(strip_heading_num, xml)
print(f"Numeracion quitada en {n_hd} encabezados.")

DOC.write_text(xml, encoding="utf-8")
print(f"document.xml escrito (delta {len(xml)-orig_len} chars).")

# ===================== HEADER1: pag arriba derecha =====================
NS_HDR_FTR_OPEN = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">'
)
NS_FTR_OPEN = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">'
)

header_apa = (
    NS_HDR_FTR_OPEN + '\n'
    '  <w:p w14:paraId="0E000001">\n'
    '    <w:pPr>\n'
    '      <w:jc w:val="right"/>\n'
    '      <w:rPr/>\n'
    '    </w:pPr>\n'
    '    <w:r>\n'
    '      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>\n'
    '      <w:fldChar w:fldCharType="begin"/>\n'
    '      <w:instrText xml:space="preserve">PAGE</w:instrText>\n'
    '      <w:fldChar w:fldCharType="end"/>\n'
    '    </w:r>\n'
    '  </w:p>\n'
    '</w:hdr>\n'
)
HEADER1.write_text(header_apa, encoding="utf-8")
if HEADER2.exists():
    HEADER2.write_text(header_apa, encoding="utf-8")
print("header con paginacion arriba derecha aplicado.")

# ===================== FOOTER1: limpio (sin pag) =====================
footer_empty = (
    NS_FTR_OPEN + '\n'
    '  <w:p w14:paraId="0E000002">\n'
    '    <w:pPr><w:rPr/></w:pPr>\n'
    '  </w:p>\n'
    '</w:ftr>\n'
)
FOOTER1.write_text(footer_empty, encoding="utf-8")
if FOOTER2.exists():
    FOOTER2.write_text(footer_empty, encoding="utf-8")
print("footer limpio.")

print("\nTodo aplicado. Listo para repackar.")
