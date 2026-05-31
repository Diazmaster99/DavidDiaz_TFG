# -----------------------------------------------------------------------------
# Autor: David Díaz Espinosa de los Monteros
# TFG - Bot de combates Pokémon VGC con aprendizaje por refuerzo (PPO)
# -----------------------------------------------------------------------------
# -*- coding: utf-8 -*-
"""Sobre el doc APA 7: renumera encabezados, mete el running head con
paginacion (header por defecto) y vacia el header de portada."""
import re
from pathlib import Path

UNPACKED = Path("_build_memoria/unpacked_apa2")
DOC     = UNPACKED / "word/document.xml"
HEADER1 = UNPACKED / "word/header1.xml"   # default -> resto de paginas
HEADER2 = UNPACKED / "word/header2.xml"   # first  -> portada

# =====================================================================
# 1) Renumerar encabezados (Heading1/2/3)
# =====================================================================
FRONT_MATTER = {
    "Índice", "Resumen y palabras clave", "Abstract and keywords",
    "Resumen y palabras clave - Parte grupal",
    "Abstract and keywords - Group Project",
    "Glosario de términos y acrónimos",
    "Dedicatoria y agradecimientos",
}

xml = DOC.read_text(encoding="utf-8")
# Iteramos parrafos en orden y mantenemos contadores h1/h2/h3.
h1 = h2 = h3 = 0
out_chunks = []
last = 0
para_re = re.compile(
    r'<w:p\b[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="(Heading[1-3])"(?:(?!</w:p>).)*?</w:p>',
    re.S
)
text_re = re.compile(r'<w:t[^>]*>([^<]*)</w:t>')

for m in para_re.finditer(xml):
    block = m.group(0)
    level = m.group(1)  # Heading1/2/3
    tm = text_re.search(block)
    if not tm:
        continue
    text = tm.group(1)
    prefix = None
    if level == "Heading1":
        if text in FRONT_MATTER:
            prefix = None  # sin numerar
        else:
            h1 += 1
            h2 = h3 = 0
            prefix = f"{h1}. "
    elif level == "Heading2":
        if h1 == 0:
            prefix = None
        else:
            h2 += 1
            h3 = 0
            prefix = f"{h1}.{h2}. "
    elif level == "Heading3":
        if h1 == 0 or h2 == 0:
            prefix = None
        else:
            h3 += 1
            prefix = f"{h1}.{h2}.{h3}. "
    if prefix:
        new_text = prefix + text
        # Substituimos SOLO ese <w:t> dentro del bloque.
        new_block = block[:tm.start()] + f'<w:t xml:space="preserve">{new_text}</w:t>' + block[tm.end():]
        out_chunks.append(xml[last:m.start()])
        out_chunks.append(new_block)
        last = m.end()

out_chunks.append(xml[last:])
xml = "".join(out_chunks)
DOC.write_text(xml, encoding="utf-8")
print(f"Renumeracion completada: h1={h1} (h2 y h3 numerados bajo cada uno).")

# =====================================================================
# 2) Header por defecto (header1.xml): running head + paginacion
# =====================================================================
RH = "APRENDIZAJE POR REFUERZO EN POKÉMON VGC"
header_main = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">\n'
    '  <w:p w14:paraId="0F000001">\n'
    '    <w:pPr>\n'
    '      <w:tabs>\n'
    '        <w:tab w:val="right" w:pos="9026"/>\n'
    '      </w:tabs>\n'
    '      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>\n'
    '    </w:pPr>\n'
    '    <w:r>\n'
    '      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>\n'
    f'      <w:t xml:space="preserve">{RH}</w:t>\n'
    '      <w:tab/>\n'
    '    </w:r>\n'
    '    <w:r>\n'
    '      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="22"/></w:rPr>\n'
    '      <w:fldChar w:fldCharType="begin"/>\n'
    '      <w:instrText xml:space="preserve">PAGE</w:instrText>\n'
    '      <w:fldChar w:fldCharType="end"/>\n'
    '    </w:r>\n'
    '  </w:p>\n'
    '</w:hdr>\n'
)
HEADER1.write_text(header_main, encoding="utf-8")
print(f"header1.xml: running head '{RH}' + PAGE a la derecha.")

# =====================================================================
# 3) Header de portada (header2.xml): vacio
# =====================================================================
header_first = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">\n'
    '  <w:p w14:paraId="0F000002">\n'
    '    <w:pPr><w:rPr/></w:pPr>\n'
    '  </w:p>\n'
    '</w:hdr>\n'
)
HEADER2.write_text(header_first, encoding="utf-8")
print("header2.xml: vacio (portada sin running head ni paginacion).")

print("\nTodo aplicado.")
