// Genera Anexo_A_Documentacion_codigo.docx y Anexo_B_Manual_usuario.docx
// Estilo: Arial 11 negro, justificado, A4, interlineado 1.15.
// Para luego pasarlo a PDF desde Word.
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType, ShadingType,
  HeadingLevel, PageBreak,
} = require("docx");

const FONT = "Arial";

function P(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.after == null ? 140 : opts.after, line: 276 },
    children: Array.isArray(text)
      ? text
      : [new TextRun({ text, bold: !!opts.bold, italics: !!opts.italics, font: FONT, size: 22 })],
    ...(opts.pageBreakBefore ? { pageBreakBefore: true } : {}),
  });
}
function run(text, o = {}) {
  return new TextRun({ text, bold: !!o.bold, italics: !!o.italics, font: FONT, size: o.size || 22 });
}
function H1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 320, after: 180 },
    children: [new TextRun({ text, bold: true, font: FONT, size: 32 })],
  });
}
function H2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 140 },
    children: [new TextRun({ text, bold: true, font: FONT, size: 26 })],
  });
}
function H3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 120 },
    children: [new TextRun({ text, bold: true, font: FONT, size: 22 })],
  });
}
function title(text, sub) {
  const arr = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 400, after: 120 },
      children: [new TextRun({ text, bold: true, font: FONT, size: 44 })],
    }),
  ];
  if (sub) {
    arr.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 360 },
      children: [new TextRun({ text: sub, italics: true, font: FONT, size: 26 })],
    }));
  }
  return arr;
}
function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 80, line: 276 },
    children: Array.isArray(text) ? text : [new TextRun({ text, font: FONT, size: 22 })],
  });
}
function placeholder(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 160, after: 80 },
    shading: { fill: "EDEDED", type: ShadingType.CLEAR },
    children: [new TextRun({ text, italics: true, color: "555555", font: FONT, size: 22 })],
  });
}
function code(text) {
  // Cada \n se convierte en un salto de linea REAL (<w:br/>), de modo que el
  // bloque monoespaciado se renderiza en varias lineas dentro de un mismo
  // parrafo con sombreado continuo (en vez de quedar todo en una sola linea).
  const lines = String(text).split("\n");
  const runs = [];
  lines.forEach((line, i) => {
    if (i > 0) runs.push(new TextRun({ break: 1 }));
    runs.push(new TextRun({ text: line, font: "Consolas", size: 20 }));
  });
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { after: 80, line: 260 },
    shading: { fill: "F5F5F5", type: ShadingType.CLEAR },
    children: runs,
  });
}
function tbl(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const b = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
  const borders = { top: b, bottom: b, left: b, right: b };
  const headRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 110, right: 110 },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, font: FONT, size: 20 })] })],
    })),
  });
  const bodyRows = rows.map(r => new TableRow({
    children: r.map((c, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 110, right: 110 },
      children: [new Paragraph({ children: [new TextRun({ text: c, font: FONT, size: 20 })] })],
    })),
  }));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: [headRow, ...bodyRows] });
}

// ====================================================================
// ANEXO A — DOCUMENTACIÓN DEL CÓDIGO
// ====================================================================
function buildAnexoA() {
  const c = [];
  c.push(...title("Anexo A. Documentación del código",
    "Diseño y entrenamiento de un agente de aprendizaje por refuerzo para combates dobles de Pokémon en formato VGC"));
  c.push(P("Autor: David Díaz Espinosa de los Monteros", { align: AlignmentType.CENTER }));
  c.push(P("Universidad de Diseño, Innovación y Tecnología (UDIT) — Grado en Diseño y Desarrollo de Videojuegos, Especialidad de Programación",
    { align: AlignmentType.CENTER, italics: true }));
  c.push(P("Curso académico 2025-2026", { align: AlignmentType.CENTER, italics: true, after: 360 }));

  c.push(P("Este documento, anexo a la memoria individual del Trabajo de Fin de Grado, recoge la documentación técnica del código del proyecto en los seis apartados requeridos por la guía de redacción de la memoria de la Especialidad de Programación: componentes, bibliotecas de terceros, clases, requisitos para usar el proyecto, estructura del proyecto y otra documentación."));

  // -----------------------------------------------------------
  c.push(H1("Componentes"));
  c.push(P("El software se ha dividido en los componentes que se enumeran a continuación. Las flechas del diagrama indican una relación de dependencia: A → B significa que el componente A utiliza el componente B."));
  c.push(placeholder("[Insertar aquí el diagrama de componentes en notación UML 2. Indicar los componentes que se describen debajo y sus relaciones de dependencia.]"));
  c.push(P("La descripción de cada componente es la siguiente:"));
  c.push(bullet([run("Servidor de combates (externo). ", { bold: true }), run("Pokémon Showdown en su variante adaptada por el proyecto VGC-Bench, ejecutado localmente en Node.js. Simula los combates y expone una API por WebSocket en el puerto 8000.")]));
  c.push(bullet([run("Cliente del servidor (externo). ", { bold: true }), run("La biblioteca poke-env, que abstrae la comunicación por WebSocket con el servidor, mantiene el estado del combate y expone una interfaz compatible con el estándar Gymnasium.")]));
  c.push(bullet([run("Entornos de combate del proyecto. ", { bold: true }), run("Las clases MySinglesEnv y MyDoublesEnv heredan de los entornos de poke-env y añaden dos elementos propios: la construcción de la observación rica (apartado 5.3.3 de la memoria) y el cálculo de la función de recompensa.")]));
  c.push(bullet([run("Envoltorio de un solo agente. ", { bold: true }), run("El componente OpponentSamplingEnv convierte el entorno multiagente de poke-env en un entorno Gymnasium de un solo agente, gestiona la elección de acciones del oponente (aleatorio, máxima potencia, heurístico o self-play) y la robustez frente a fallos del servidor.")]));
  c.push(bullet([run("Envoltorios de Stable-Baselines3. ", { bold: true }), run("Las clases SinglesGymEnv y DoublesGymEnv encapsulan el componente anterior y exponen un objeto Gymnasium con espacios de observación y de acciones que Stable-Baselines3 acepta directamente.")]));
  c.push(bullet([run("Construcción de la observación. ", { bold: true }), run("El módulo features.py reúne las funciones build_singles_obs y build_doubles_obs, que generan el vector numérico que el agente recibe en cada turno.")]));
  c.push(bullet([run("Política y red neuronal. ", { bold: true }), run("El módulo policy.py expone una función que devuelve, según se elija MLP o Transformer, los argumentos de política para MaskablePPO. El extractor con atención (BattleTransformerExtractor) está implementado en este mismo módulo.")]));
  c.push(bullet([run("Algoritmo de aprendizaje por refuerzo (externo). ", { bold: true }), run("MaskablePPO de la biblioteca sb3-contrib, una variante de PPO con enmascaramiento de acciones, distribuida por encima de Stable-Baselines3.")]));
  c.push(bullet([run("Motor de redes neuronales (externo). ", { bold: true }), run("PyTorch, que proporciona las capas, los tensores y la diferenciación automática que Stable-Baselines3 emplea internamente y que el extractor Transformer utiliza de manera explícita.")]));
  c.push(bullet([run("Parche de poke-env. ", { bold: true }), run("El módulo poke_env_patch.py corrige en memoria, al importarse, un desajuste de poke-env con los Pokémon Zacian-Coronado y Zamazenta-Coronado (Behemoth Blade y Behemoth Bash frente a Iron Head), que impedía al agente y al oponente utilizar esos movimientos.")]));
  c.push(bullet([run("Callback de métricas. ", { bold: true }), run("WinRateCallback (callbacks.py) registra en TensorBoard la tasa de victorias móvil del agente durante el entrenamiento.")]));
  c.push(bullet([run("Scripts de entrada. ", { bold: true }), run("train_singles.py y train_doubles.py para entrenar; play.py para jugar contra humanos o en la ladder; battle_models.py para enfrentar dos modelos o un modelo frente a baselines; selfplay_from.py para arrancar un entrenamiento por self-play a partir de un modelo ya entrenado; plot_metrics.py para exportar las gráficas; patch_server_formats.py para añadir formatos VGC vigentes al servidor.")]));
  c.push(P("La dependencia es, en líneas generales, de arriba a abajo: los scripts de entrada utilizan los envoltorios de Stable-Baselines3, que dependen del envoltorio de un solo agente, que depende del entorno propio del proyecto, que a su vez depende de poke-env y este del servidor de Pokémon Showdown."));

  // -----------------------------------------------------------
  c.push(H1("Bibliotecas de terceros"));
  c.push(P("En la siguiente tabla se enumeran las bibliotecas de terceros utilizadas, junto con su versión, la función que cumplen en el proyecto, el motivo por el que se eligieron y los enlaces a sus fuentes y documentación. Las versiones exactas, incluidas las transitivas, se fijan en el archivo requirements.lock entregado dentro del Anexo C (Archivos del proyecto)."));
  c.push(tbl(
    ["Biblioteca (versión)", "Función en el proyecto", "Motivo de elección", "Fuente / documentación"],
    [
      ["poke-env (0.15.0)", "Cliente Python del servidor de Pokémon Showdown. Mantiene el estado del combate y expone entornos compatibles con Gymnasium para combates individuales y dobles.", "Es la única biblioteca consolidada en Python que comunica con Pokémon Showdown y que ofrece entornos preparados para aprendizaje por refuerzo en el dominio. Reescribirla habría sido un proyecto en sí mismo.", "https://github.com/hsahovic/poke-env"],
      ["Stable-Baselines3 (2.7.1)", "Implementación de los algoritmos de aprendizaje por refuerzo (PPO, A2C, etc.). Orquesta el ciclo de entrenamiento.", "Es la biblioteca de referencia para RL en PyTorch, contrastada y documentada. Reutilizarla evita errores sutiles en la implementación del algoritmo y permite centrar el esfuerzo en el dominio.", "https://stable-baselines3.readthedocs.io"],
      ["sb3-contrib (2.7.0)", "Extensión de Stable-Baselines3. Aporta MaskablePPO (PPO con enmascaramiento de acciones).", "El enmascaramiento de acciones es imprescindible en este dominio (muchas jugadas son ilegales según el estado del combate) y sb3-contrib lo implementa de forma compatible con Stable-Baselines3.", "https://sb3-contrib.readthedocs.io"],
      ["PyTorch (2.9.1)", "Motor de cálculo para las redes neuronales (capas, tensores y diferenciación automática). Se utiliza de forma implícita a través de Stable-Baselines3 y explícitamente en el extractor Transformer.", "Es el estándar de hecho que utiliza Stable-Baselines3 y la opción más portable entre CPU y GPU.", "https://pytorch.org"],
      ["Gymnasium (1.2.3)", "Estándar de interfaz para entornos de aprendizaje por refuerzo (reset, step, espacios de observación y de acciones).", "Es el estándar que consumen poke-env (en sus versiones recientes) y Stable-Baselines3, lo que evita escribir código de unión entre ambos.", "https://gymnasium.farama.org"],
      ["TensorBoard (2.20.0)", "Visualización de las métricas de entrenamiento (recompensa media, tasa de victorias, entropía de la política, etc.).", "Es la herramienta estándar para visualizar los registros que produce Stable-Baselines3, sin necesidad de configuración adicional.", "https://www.tensorflow.org/tensorboard"],
      ["matplotlib (3.10.9)", "Exportación a imagen (PNG) de las curvas de entrenamiento registradas en TensorBoard para incluirlas en la memoria.", "Permite generar figuras a medida con etiquetas en español y formato de eje específico (0, 200k, 1M, etc.), algo que la web de TensorBoard no facilita.", "https://matplotlib.org"],
    ],
    [3000, 2800, 2200, 1360]
  ));

  // -----------------------------------------------------------
  c.push(H1("Clases"));
  c.push(P("Se presenta a continuación el diagrama de clases del código propio del proyecto. Se han omitido las clases pertenecientes a poke-env, Stable-Baselines3, sb3-contrib y PyTorch, salvo aquellas de las que el código propio hereda directamente, indicadas en cursiva."));
  c.push(placeholder("[Insertar aquí el diagrama de clases en notación UML 2. Mostrar las herencias y las asociaciones entre las clases descritas más abajo.]"));
  c.push(P("Las principales clases del código propio son las siguientes:"));
  c.push(bullet([run("MySinglesEnv ", { bold: true }), run("(hereda de "), run("SinglesEnv", { italics: true }), run(" de poke-env). Sobrescribe los métodos embed_battle y calc_reward para construir la observación rica del estado del combate y la función de recompensa.")]));
  c.push(bullet([run("MyDoublesEnv ", { bold: true }), run("(hereda de "), run("DoublesEnv", { italics: true }), run(" de poke-env). Equivalente a la anterior para combates dobles VGC.")]));
  c.push(bullet([run("OpponentSamplingEnv ", { bold: true }), run("(hereda de "), run("gymnasium.Env", { italics: true }), run("). Encapsula uno de los dos entornos anteriores y convierte la simulación de dos agentes en un entorno de un solo agente. Decide la acción del oponente (modalidad aleatoria, máxima potencia, heurística o self-play), implementa el vigilante (watchdog), la reconstrucción del entorno tras un fallo y el cierre preventivo de batallas pendientes antes de cada reinicio.")]));
  c.push(bullet([run("SinglesGymEnv y DoublesGymEnv ", { bold: true }), run("(heredan de "), run("gymnasium.Env", { italics: true }), run("). Envoltorios externos que crean el entorno anterior a partir de los parámetros de línea de comandos y exponen los espacios de observación y de acciones a Stable-Baselines3.")]));
  c.push(bullet([run("BattleTransformerExtractor ", { bold: true }), run("(hereda de "), run("BaseFeaturesExtractor", { italics: true }), run(" de Stable-Baselines3). Implementa el extractor de características basado en atención: interpreta la observación como un conjunto de fichas, proyecta cada tipo de entidad a una dimensión común, aplica un codificador Transformer y resume el resultado en una ficha CLS que alimenta las cabezas de política y de valor.")]));
  c.push(bullet([run("WinRateCallback ", { bold: true }), run("(hereda de "), run("BaseCallback", { italics: true }), run(" de Stable-Baselines3). Acumula los resultados de las últimas N batallas (a partir de la recompensa terminal) y registra en TensorBoard la tasa de victorias móvil del agente.")]));
  c.push(P("El módulo poke_env_patch.py no expone clases propias: contiene funciones de reemplazo que se asignan en tiempo de importación a métodos estáticos de DoublesEnv y SinglesEnv de poke-env."));

  // -----------------------------------------------------------
  c.push(H1("Requisitos para usar el proyecto"));
  c.push(H2("Sistema operativo"));
  c.push(P("El proyecto se ha desarrollado y verificado en Windows 10 y Windows 11. El código es portable: funciona también en Linux y macOS, aunque las instrucciones de instalación pueden requerir adaptaciones menores (por ejemplo, el script de activación del entorno virtual)."));
  c.push(H2("Software necesario"));
  c.push(P("Hay que instalar previamente los tres programas siguientes:"));
  c.push(bullet([run("Python 3.10–3.13. ", { bold: true }), run("Descargable de python.org. Durante la instalación es imprescindible marcar la casilla «Add python.exe to PATH», pues, en caso contrario, los comandos posteriores no encontrarán el intérprete.")]));
  c.push(bullet([run("Node.js (versión LTS). ", { bold: true }), run("Necesario para ejecutar el servidor de Pokémon Showdown.")]));
  c.push(bullet([run("Git. ", { bold: true }), run("Necesario para clonar el proyecto y la variante adaptada del servidor.")]));
  c.push(H2("Instalación del proyecto"));
  c.push(P("Desde una terminal nueva, se descarga el proyecto, se crea un entorno virtual de Python y se instalan las dependencias:"));
  c.push(code("git clone <URL_DEL_REPOSITORIO> DavidDiaz_TFG"));
  c.push(code("cd DavidDiaz_TFG"));
  c.push(code("python -m venv .venv"));
  c.push(code(".venv\\Scripts\\activate"));
  c.push(code("pip install -r requirements.txt"));
  c.push(P("La última orden instala las versiones de las bibliotecas listadas en requirements.txt. Para reproducir el entorno completo verificado (incluyendo las dependencias transitivas) puede emplearse, en su lugar, requirements.lock."));
  c.push(P("Por defecto se instala la edición de PyTorch para CPU. Para ejecutar el entrenamiento sobre una GPU compatible con CUDA, una vez activado el entorno virtual hay que reinstalar PyTorch desde su índice específico:"));
  c.push(code("pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu121"));
  c.push(H2("Instalación del servidor"));
  c.push(P("El servidor de Pokémon Showdown no se distribuye con el proyecto (queda excluido por .gitignore por su tamaño y por ser código de terceros). Se clona el fork de VGC-Bench dentro de la carpeta del proyecto, se instalan sus dependencias de Node.js y se compila:"));
  c.push(code("git clone -b vgc-bench https://github.com/cameronangliss/pokemon-showdown.git"));
  c.push(code("cd pokemon-showdown"));
  c.push(code("npm i"));
  c.push(code("node build"));
  c.push(P("Opcionalmente, para añadir al fork los formatos VGC vigentes que no incluye, se ejecuta desde la raíz del proyecto el script patch_server_formats.py y se recompila el servidor."));
  c.push(H2("Configuración por defecto"));
  c.push(P("No es necesario configurar nada adicional. El servidor escucha en localhost en el puerto 8000 y los scripts del proyecto se conectan a esa dirección por defecto. Si se desea utilizar otro puerto, todos los scripts admiten el argumento --port. Si se desea utilizar el servidor oficial play.pokemonshowdown.com en lugar del local, se utiliza el argumento --official (solo en play.py)."));

  // -----------------------------------------------------------
  c.push(H1("Estructura del proyecto"));
  c.push(P("La carpeta del proyecto está organizada de modo que las distintas categorías de archivos (código propio, código de terceros, recursos, configuración) queden separadas en directorios distintos. Su contenido es el siguiente:"));
  c.push(code(
    "DavidDiaz_TFG/\n" +
    "├── src/                          # CÓDIGO FUENTE PROPIO (módulos importables)\n" +
    "│   ├── singles_env.py            # MySinglesEnv: entorno de combates individuales\n" +
    "│   ├── doubles_env.py            # MyDoublesEnv: entorno de combates dobles VGC\n" +
    "│   ├── rl_wrapper.py             # OpponentSamplingEnv: envoltorio de un solo agente\n" +
    "│   ├── features.py               # Construccion de la observacion rica\n" +
    "│   ├── policy.py                 # Argumentos de politica MLP y extractor Transformer\n" +
    "│   ├── callbacks.py              # WinRateCallback para TensorBoard\n" +
    "│   ├── poke_env_patch.py         # Parche de poke-env (Behemoth Blade y Behemoth Bash)\n" +
    "│   └── teams.py                  # Constructor de equipos para los entornos de dobles\n" +
    "│\n" +
    "├── train_singles.py              # SCRIPTS DE ENTRADA (propios, raiz del proyecto)\n" +
    "├── train_doubles.py\n" +
    "├── play.py\n" +
    "├── battle_models.py\n" +
    "├── selfplay_from.py\n" +
    "├── plot_metrics.py\n" +
    "├── patch_server_formats.py\n" +
    "├── test_env.py\n" +
    "│\n" +
    "├── teams/                        # RECURSOS (equipos Pokemon en formato Showdown)\n" +
    "│   └── vgc/                      # subcarpetas por formato y por regulacion\n" +
    "│\n" +
    "├── pokemon-showdown/             # CODIGO DE TERCEROS (servidor, Node.js)\n" +
    "│                                   No se distribuye; se clona del fork de VGC-Bench\n" +
    "│\n" +
    "├── models/                       # MODELOS ENTRENADOS (artefactos)\n" +
    "│   ├── singles/<formato>/<policy>/seed<N>/   modelos de singles\n" +
    "│   └── doubles/<formato>/<policy>/seed<N>/   modelos de dobles (y seed<N>_selfplay)\n" +
    "│\n" +
    "├── logs/                         # REGISTROS DE TENSORBOARD (artefactos)\n" +
    "├── metrics/                      # GRAFICAS EXPORTADAS (PNG)\n" +
    "├── replays/                      # REPETICIONES DE COMBATES (HTML / JSON)\n" +
    "│\n" +
    "├── requirements.txt              # CONFIGURACION (dependencias de Python)\n" +
    "├── requirements.lock             # entorno verificado, version exacta de todas las dependencias\n" +
    "├── COMANDOS.txt                  # ayuda de uso diario\n" +
    "├── INSTALACION.txt               # guia de instalacion desde cero\n" +
    "├── README.md                     # presentacion del proyecto\n" +
    "└── .gitignore                    # exclusiones de Git"
  ));
  c.push(P("Como se aprecia en el árbol anterior, el código propio del proyecto queda recogido bajo src/ (módulos importables) y en los scripts de entrada de la raíz; el código de terceros principal (el servidor) se ubica en su propia carpeta pokemon-showdown/; los recursos en teams/; los archivos de configuración (dependencias y guías) en la raíz, y los artefactos generados durante la ejecución (modelos, registros, gráficas y repeticiones) en sus respectivas carpetas. Las dependencias instaladas con pip se gestionan en un entorno virtual aislado en .venv/ (no se distribuye, se reconstruye con requirements.txt)."));

  // -----------------------------------------------------------
  c.push(H1("Otra documentación"));
  c.push(P("Junto al código fuente se aporta documentación técnica complementaria que ha resultado útil durante el desarrollo. Se distinguen dos grupos según dónde quedan ubicados en la entrega final."));

  c.push(H2("Archivos incluidos dentro del propio proyecto"));
  c.push(P("Los cuatro archivos siguientes viajan junto al código fuente, en la raíz del propio proyecto, de modo que cualquiera que descomprima las fuentes los encuentra inmediatamente:"));
  c.push(bullet([run("INSTALACION.txt. ", { bold: true }), run("Guía paso a paso para reinstalar el proyecto en un ordenador sin nada previamente instalado.")]));
  c.push(bullet([run("COMANDOS.txt. ", { bold: true }), run("Recopilación ordenada por temas de los comandos de uso diario del proyecto: entrenar, jugar, enfrentar modelos, ver el progreso en TensorBoard, exportar gráficas y depurar errores.")]));
  c.push(bullet([run("requirements.txt y requirements.lock. ", { bold: true }), run("Especificación de las dependencias de Python, con sus versiones, lo que permite reconstruir el entorno completo en otra máquina.")]));
  c.push(bullet([run("README.md. ", { bold: true }), run("Presentación breve del proyecto, con un resumen de qué hace, cómo se instala y cómo se ejecuta.")]));

  c.push(H2("Carpetas entregadas aparte, fuera del proyecto"));
  c.push(P("Las dos carpetas siguientes recogen material generado por el agente durante el entrenamiento y la evaluación. No forman parte de las fuentes y se entregan por separado dentro del Anexo C, junto al proyecto pero fuera de él:"));
  c.push(bullet([run("Carpeta replays/. ", { bold: true }), run("Repeticiones de combates del agente entrenado, en el formato propio de Pokémon Showdown (archivo HTML autocontenido por combate, o JSON). Estas repeticiones pueden visualizarse subiendo el archivo a play.pokemonshowdown.com/replay o reproduciéndolo directamente en un navegador. Documentan, sin necesidad de ejecutar el proyecto, el comportamiento que el agente exhibe tras el entrenamiento.")]));
  c.push(bullet([run("Carpeta metrics/. ", { bold: true }), run("Gráficas de las métricas de entrenamiento exportadas desde TensorBoard a PNG (tasa de victorias móvil, recompensa media, varianza explicada, divergencia KL, etc.). Son las mismas figuras incluidas en la memoria, suministradas también como ficheros sueltos para facilitar su inspección a tamaño original.")]));

  c.push(P("Tanto los archivos del primer grupo como las carpetas del segundo, junto con la documentación extraída automáticamente del código fuente con pdoc y el binario distribuible, se entregan en el Anexo C — Archivos del proyecto."));

  return c;
}

// ====================================================================
// ANEXO B — MANUAL DE USUARIO
// ====================================================================
function buildAnexoB() {
  const c = [];
  c.push(...title("Anexo B. Manual de usuario",
    "Diseño y entrenamiento de un agente de aprendizaje por refuerzo para combates dobles de Pokémon en formato VGC"));
  c.push(P("Autor: David Díaz Espinosa de los Monteros", { align: AlignmentType.CENTER }));
  c.push(P("Universidad de Diseño, Innovación y Tecnología (UDIT) — Grado en Diseño y Desarrollo de Videojuegos, Especialidad de Programación",
    { align: AlignmentType.CENTER, italics: true }));
  c.push(P("Curso académico 2025-2026", { align: AlignmentType.CENTER, italics: true, after: 360 }));

  c.push(H1("1. Qué hace este programa"));
  c.push(P("El programa permite entrenar, jugar y evaluar agentes de inteligencia artificial que disputan combates Pokémon, con especial atención al formato competitivo oficial de dobles (VGC). Los combates se desarrollan sobre un simulador local de Pokémon Showdown que el propio programa pone en marcha. Una vez entrenado, el agente puede aceptar desafíos en el simulador local o en el servidor oficial de Pokémon Showdown, y enfrentarse a personas reales o a otros agentes."));
  c.push(P("Este manual está pensado para usuarios finales que quieren instalarlo y utilizarlo. No es necesario conocer Python ni aprendizaje por refuerzo para seguirlo; basta con escribir las órdenes en una terminal de Windows."));

  c.push(H1("2. Requisitos previos"));
  c.push(P("Hay que instalar tres programas gratuitos antes de utilizar el proyecto:"));
  c.push(bullet([run("Python 3.10, 3.11, 3.12 o 3.13. ", { bold: true }), run("Se descarga de python.org. Durante la instalación es imprescindible marcar la casilla «Add python.exe to PATH».")]));
  c.push(bullet([run("Node.js, versión LTS. ", { bold: true }), run("Se descarga de nodejs.org. Es la base sobre la que se ejecuta el simulador de combates.")]));
  c.push(bullet([run("Git. ", { bold: true }), run("Se descarga de git-scm.com. Sirve para obtener el proyecto y el simulador.")]));
  c.push(P("Para comprobar que los tres se han instalado correctamente, basta con abrir una terminal nueva (Símbolo del sistema o PowerShell) y escribir, una en cada línea, las órdenes python --version, node --version y git --version. Si las tres responden con un número de versión, todo está listo."));

  c.push(H1("3. Instalación"));
  c.push(P("Los pasos siguientes solo hay que hacerlos la primera vez. En las próximas sesiones bastará con saltar al apartado 4."));
  c.push(H2("3.1. Descargar el proyecto"));
  c.push(P("Desde una terminal nueva:"));
  c.push(code("git clone <URL_DEL_REPOSITORIO> DavidDiaz_TFG"));
  c.push(code("cd DavidDiaz_TFG"));
  c.push(P("Todas las órdenes posteriores se ejecutan desde esta carpeta."));
  c.push(H2("3.2. Crear el entorno e instalar dependencias"));
  c.push(code("python -m venv .venv"));
  c.push(code(".venv\\Scripts\\activate"));
  c.push(code("pip install -r requirements.txt"));
  c.push(P("Tras activarse el entorno virtual aparece «(.venv)» al principio del símbolo del sistema."));
  c.push(H2("3.3. Instalar el servidor de combates"));
  c.push(code("git clone -b vgc-bench https://github.com/cameronangliss/pokemon-showdown.git"));
  c.push(code("cd pokemon-showdown"));
  c.push(code("npm i"));
  c.push(code("node build"));
  c.push(P("Esta última orden compila el servidor. La primera ejecución puede tardar varios minutos."));

  c.push(H1("4. Arrancar el simulador de combates"));
  c.push(P("Antes de entrenar o jugar hay que arrancar el simulador local. Conviene dejarlo abierto en una terminal aparte mientras se utiliza el programa."));
  c.push(code("cd pokemon-showdown"));
  c.push(code("node pokemon-showdown start --no-security"));
  c.push(P("Cuando aparezca el mensaje «Worker 1 now listening on 0.0.0.0:8000» el servidor está listo. El cliente web del simulador queda accesible en el navegador en http://localhost:8000, lo que resulta útil para retar al agente desde la propia máquina."));

  c.push(H1("5. Entrenar al agente"));
  c.push(P("Desde una segunda terminal, con el entorno virtual activado:"));
  c.push(code(".venv\\Scripts\\activate"));
  c.push(H2("5.1. Combates dobles VGC"));
  c.push(P("Para entrenar al agente en el formato dobles del campeonato VGC contra un oponente heurístico:"));
  c.push(code("python train_doubles.py --team teams/vgc/I1.txt --format gen9vgc2026regi --opponent heuristic --total_steps 500000"));
  c.push(P("El argumento --team admite también una carpeta con varios equipos (uno aleatorio por combate). El argumento --opponent acepta los valores random, maxpower, heuristic y self (para self-play). El argumento --total_steps fija la duración total del entrenamiento. El proceso guarda puntos de control de forma periódica en la carpeta models/."));
  c.push(H2("5.2. Combates individuales"));
  c.push(P("De forma equivalente, para combates individuales (formato gen9randombattle por defecto):"));
  c.push(code("python train_singles.py --opponent heuristic --total_steps 500000"));
  c.push(H2("5.3. Continuar un entrenamiento ya iniciado"));
  c.push(P("Si se vuelve a lanzar el mismo comando con un valor mayor de --total_steps, el programa detecta el último punto de control guardado y reanuda el entrenamiento desde ahí. No es necesario indicar nada adicional."));

  c.push(H1("6. Jugar contra el agente"));
  c.push(H2("6.1. En el simulador local"));
  c.push(P("Una vez entrenado el agente, en una nueva terminal con el entorno virtual activado:"));
  c.push(code("python play.py --mode doubles --username MiBot --team teams/vgc/I1.txt --format gen9vgc2026regi"));
  c.push(P("El agente se conecta al servidor local con el nombre indicado en --username y queda esperando desafíos. Para retarlo, basta con abrir http://localhost:8000 en el navegador, registrarse con otro nombre, elegir el formato y desafiar al usuario del agente. Si se desea que acepte varios desafíos seguidos, se utiliza el argumento -n N (por ejemplo, -n 5)."));
  c.push(H2("6.2. En el servidor oficial"));
  c.push(P("El agente puede también jugar en el servidor oficial play.pokemonshowdown.com con una cuenta registrada. Hay que añadir --official y la contraseña:"));
  c.push(code("python play.py --mode doubles --username MiBotRegistrado --password MiClave --official --team teams/vgc/I1.txt --format gen9vgc2026regi -n 5"));
  c.push(H2("6.3. Varios combates simultáneos"));
  c.push(P("Por defecto el agente juega un combate cada vez. Si se desea que acepte varios desafíos en paralelo (por ejemplo, para que varias personas le reten a la vez en el servidor oficial), se utiliza el argumento --max-concurrent:"));
  c.push(code("python play.py --mode doubles --username MiBot --official --team teams/vgc/I1.txt --format gen9vgc2026regi -n 15 --max-concurrent 3"));
  c.push(P("Con el ejemplo anterior, el agente acepta hasta quince desafíos en total y juega hasta tres combates simultáneamente."));

  c.push(H1("7. Enfrentar dos modelos"));
  c.push(P("Es posible enfrentar dos modelos entre sí o un modelo contra un oponente de referencia (aleatorio, máxima potencia o heurístico) y medir la tasa de victorias sobre un número configurable de combates:"));
  c.push(code("python battle_models.py --mode doubles --format gen9vgc2026regi --team teams/vgc/I1.txt --a mlp --b heuristic -n 50"));
  c.push(P("Los argumentos --a y --b admiten los valores mlp, transformer (modelos entrenados) y random, maxpower, heuristic (rivales de referencia). Los argumentos --run_id_a y --run_id_b permiten elegir la semilla (es decir, qué modelo concreto se utiliza) cuando se enfrenta a un modelo de aprendizaje por refuerzo."));

  c.push(H1("8. Ver el progreso del entrenamiento"));
  c.push(P("Durante el entrenamiento se generan registros que pueden visualizarse en tiempo real con TensorBoard. Desde una terminal, en la carpeta del proyecto:"));
  c.push(code("tensorboard --logdir logs"));
  c.push(P("Al abrir en el navegador la dirección que muestra (habitualmente http://localhost:6006) aparecen las curvas de entrenamiento: recompensa media por episodio, tasa de victorias móvil, entropía de la política, varianza explicada y otras."));
  c.push(P("Para exportar las gráficas a imagen, se utiliza:"));
  c.push(code("python plot_metrics.py"));
  c.push(P("El programa genera un PNG por métrica en la carpeta metrics/, con los nombres de las métricas en español y el eje de pasos formateado en miles (200k, 400k, etc.) y millones (1M)."));

  c.push(H1("9. Repeticiones de los combates"));
  c.push(P("Las repeticiones de combates ya jugados se guardan en la carpeta replays/ del proyecto (entregada dentro del Anexo C — Archivos del proyecto). Cada repetición es un archivo HTML autocontenido que puede:"));
  c.push(bullet("abrirse directamente en cualquier navegador web (haciendo doble clic sobre el archivo), o"));
  c.push(bullet("subirse a play.pokemonshowdown.com/upload para obtener un enlace permanente."));
  c.push(P("Las repeticiones reproducen la animación completa del combate, turno por turno, junto con el registro de mensajes del simulador. Sirven para revisar el comportamiento del agente sin necesidad de ejecutar el proyecto."));

  c.push(H1("10. Problemas frecuentes"));
  c.push(bullet([run("\"python no se reconoce como un comando interno o externo\". ", { bold: true }), run("Durante la instalación de Python no se marcó la casilla «Add python.exe to PATH». Hay que reinstalar Python marcándola, o utilizar py en lugar de python.")]));
  c.push(bullet([run("\"No hay servidor Showdown en localhost:8000\". ", { bold: true }), run("El simulador no se ha arrancado o se ha cerrado. Vuelva al apartado 4 y déjelo abierto en una terminal antes de utilizar el programa.")]));
  c.push(bullet([run("\"bind EADDRINUSE 0.0.0.0:8000\" al arrancar el servidor. ", { bold: true }), run("Ya hay otro servidor escuchando en el mismo puerto. Cierre el anterior (Ctrl+C en su terminal) antes de volver a arrancarlo.")]));
  c.push(bullet([run("Errores de compilación en \"npm i\". ", { bold: true }), run("Conviene asegurarse de tener una versión LTS reciente de Node.js (18 o superior).")]));
  c.push(bullet([run("El entrenamiento parece detenerse y muestra mensajes de reconstrucción. ", { bold: true }), run("Es el comportamiento normal del programa al detectar un fallo temporal de comunicación con el simulador: se reconstruye la conexión y se reintenta. Si los mensajes se repiten con mucha frecuencia, conviene reiniciar el servidor de combates.")]));

  c.push(H1("11. Reconstrucción del binario distribuible"));
  c.push(P("El proyecto se entrega como binario distribuible en dos formatos complementarios, ambos reproducibles desde las fuentes con los scripts incluidos en la carpeta _build_release/ del Anexo C. Esta sección está dirigida al lector que desee regenerar dicho binario; el usuario final que solo quiera utilizar el programa puede hacerlo directamente con cualquiera de los dos archivos entregados."));

  c.push(H2("11.1. Formatos generados"));
  c.push(bullet([run("Paquete portable (DavidDiaz_TFG_portable.7z). ", { bold: true }), run("Contiene Python embebido, un entorno virtual con todas las dependencias instaladas, Node.js portable, el servidor Pokémon Showdown ya compilado, los modelos entrenados y los lanzadores .bat. El usuario descomprime el archivo y ejecuta los lanzadores sin instalar nada en el sistema.")]));
  c.push(bullet([run("Instalador Windows (DavidDiaz_TFG_setup.exe). ", { bold: true }), run("Se genera con Inno Setup 6 a partir del paquete anterior. Instala el programa en Program Files, crea accesos directos en el menú Inicio y permite la desinstalación limpia desde el panel de control.")]));

  c.push(H2("11.2. Requisitos del equipo de construcción"));
  c.push(P("Para regenerar el binario distribuible es necesario disponer de:"));
  c.push(bullet([run("Windows 10 u 11 de 64 bits con PowerShell 5 o superior."), ]));
  c.push(bullet([run("Conexión a Internet la primera vez que se ejecuta el script (descarga la distribución embeddable de Python y la versión portable de Node.js; ambas quedan cacheadas para construcciones posteriores)."), ]));
  c.push(bullet([run("7-Zip instalado (https://www.7-zip.org), para crear el archivo .7z final."), ]));
  c.push(bullet([run("Inno Setup 6 instalado (https://jrsoftware.org/isinfo.php), únicamente si se desea generar también el instalador setup.exe."), ]));
  c.push(bullet([run("El fork del servidor situado en pokemon-showdown/ con sus dependencias ya instaladas y compilado, lo que se hace una sola vez con npm install y node build dentro de esa carpeta."), ]));

  c.push(H2("11.3. Pasos de reconstrucción"));
  c.push(P("Desde la raíz del proyecto, en una terminal PowerShell:"));
  c.push(code("powershell -ExecutionPolicy Bypass -File _build_release\\build_portable.ps1"));
  c.push(P("El script ejecuta, por orden: descarga (o reutiliza de la caché) Python embeddable y Node.js portable; activa la directiva import site del Python embebido; instala pip y crea el entorno virtual con todas las dependencias de requirements.txt; copia el servidor Pokémon Showdown junto con su node_modules y su carpeta dist; copia el código fuente del bot (src/, los scripts de raíz, teams/ y models/); escribe los lanzadores START_servidor.bat, START_bot.bat y ABRIR_shell.bat junto con un archivo LEEME.txt de instrucciones; y comprime el conjunto con 7-Zip."));
  c.push(P("Para generar a continuación el instalador Windows:"));
  c.push(code("& \"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe\" _build_release\\setup.iss"));
  c.push(P("La duración total de una reconstrucción limpia ronda los diez minutos, dominada por la descarga de PyTorch. Las construcciones posteriores son mucho más rápidas gracias al directorio de caché."));

  c.push(H2("11.4. Salida"));
  c.push(P("Ambos archivos quedan depositados en _build_release/dist/:"));
  c.push(bullet([run("DavidDiaz_TFG_portable.7z. ", { bold: true }), run("Paquete portable comprimido.")]));
  c.push(bullet([run("DavidDiaz_TFG_setup.exe. ", { bold: true }), run("Instalador Windows.")]));
  c.push(P("Una descripción más detallada de los argumentos del script de construcción y de la estructura interna del paquete portable se encuentra en _build_release/README.md."));

  return c;
}

// =================== EJECUCIÓN ===================
function buildDoc(children) {
  return new Document({
    styles: {
      default: { document: { run: { font: FONT, size: 22 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 32, bold: true, font: FONT, color: "1F3A5F" },
          paragraph: { spacing: { before: 320, after: 180 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 26, bold: true, font: FONT, color: "1F3A5F" },
          paragraph: { spacing: { before: 240, after: 140 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 22, bold: true, font: FONT },
          paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
      ],
    },
    numbering: {
      config: [
        { reference: "bullets",
          levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ],
    },
    sections: [{
      properties: {
        page: {
          size: { width: 11906, height: 16838 }, // A4
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      children,
    }],
  });
}

Packer.toBuffer(buildDoc(buildAnexoA())).then(buf => {
  fs.writeFileSync("Anexo_A_Documentacion_del_codigo.docx", buf);
  console.log("OK Anexo_A_Documentacion_del_codigo.docx generado");
});
Packer.toBuffer(buildDoc(buildAnexoB())).then(buf => {
  fs.writeFileSync("Anexo_B_Manual_de_usuario.docx", buf);
  console.log("OK Anexo_B_Manual_de_usuario.docx generado");
});
