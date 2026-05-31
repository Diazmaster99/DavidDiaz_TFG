const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, TabStopType, TabStopPosition,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak,
} = require("docx");

// ---------- Helpers ----------
const FONT = "Arial";
function P(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: opts.after == null ? 160 : opts.after, line: 276 },
    children: Array.isArray(text)
      ? text
      : [new TextRun({ text, bold: !!opts.bold, italics: !!opts.italics })],
    ...(opts.pageBreakBefore ? { pageBreakBefore: true } : {}),
  });
}
function run(text, o = {}) { return new TextRun({ text, bold: !!o.bold, italics: !!o.italics }); }
function H1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 200 },
    pageBreakBefore: true, children: [new TextRun({ text })] });
}
function H1np(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 200 },
    children: [new TextRun({ text })] });
}
function H2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 140 },
    children: [new TextRun({ text })] });
}
function H3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 180, after: 120 },
    children: [new TextRun({ text })] });
}
function bullet(text) {
  return new Paragraph({ numbering: { reference: "vi", level: 0 },
    alignment: AlignmentType.JUSTIFIED, spacing: { after: 80, line: 276 },
    children: Array.isArray(text) ? text : [new TextRun({ text })] });
}
function fig(text) { // placeholder for figures/tables to be inserted by the student
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 },
    shading: { fill: "EDEDED", type: ShadingType.CLEAR },
    children: [new TextRun({ text, italics: true, color: "555555" })] });
}
function caption(text) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 },
    children: [new TextRun({ text, italics: true, size: 18 })] });
}

// Simple 2-col reference-style table builder
function tbl(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const b = { style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" };
  const borders = { top: b, bottom: b, left: b, right: b };
  const headRow = new TableRow({ tableHeader: true, children: headers.map((h, i) =>
    new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 110, right: 110 },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 20 })] })] })) });
  const bodyRows = rows.map(r => new TableRow({ children: r.map((c, i) =>
    new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 110, right: 110 },
      children: [new Paragraph({ children: [new TextRun({ text: c, size: 20 })] })] })) }));
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [headRow, ...bodyRows] });
}

const children = [];

// ================= PORTADA =================
const cover = (t, o = {}) => new Paragraph({ alignment: AlignmentType.CENTER,
  spacing: { after: o.after == null ? 120 : o.after, before: o.before || 0 },
  children: [new TextRun({ text: t, bold: !!o.bold, size: o.size || 24, color: o.color || "000000" })] });
children.push(
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400, after: 80 },
    children: [new TextRun({ text: "UNIVERSIDAD DE DISEÑO, INNOVACIÓN Y TECNOLOGÍA (UDIT)", bold: true, size: 26 })] }),
  cover("Grado en Diseño y Desarrollo de Videojuegos", { size: 24, after: 40 }),
  cover("Especialidad de Programación", { size: 24, after: 40 }),
  cover("Curso académico 2025-2026", { size: 24, after: 600 }),
  cover("[Insertar aquí el logo de UDIT / ESNE]", { size: 20, color: "888888", after: 600 }),
  cover("TRABAJO DE FIN DE GRADO", { bold: true, size: 28, after: 120 }),
  cover("Diseño y entrenamiento de un agente de aprendizaje por refuerzo para combates dobles de Pokémon en formato VGC",
    { bold: true, size: 32, after: 600 }),
  cover("Autor: David Díaz", { size: 24, after: 40 }),
  cover("Proyecto grupal: [Nombre del proyecto] — Equipo: [Nombre del equipo]", { size: 22, color: "555555", after: 40 }),
  cover("Tutor: [Nombre del tutor/a]", { size: 22, after: 40 }),
  cover("Fecha de entrega: [día] de [mes] de 2026", { size: 22, after: 200 }),
);

// ================= ÍNDICE =================
children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true,
  spacing: { after: 200 }, children: [new TextRun("Índice")] }));
children.push(new Paragraph({ spacing: { after: 160 }, children: [new TextRun({
  text: "Nota: este índice se genera automáticamente. En Word, hacer clic derecho sobre la tabla y elegir «Actualizar campos» para numerar las páginas.",
  italics: true, size: 18, color: "777777" })] }));
children.push(new TableOfContents("Tabla de contenidos", { hyperlink: true, headingStyleRange: "1-3" }));

// ================= DEDICATORIA =================
children.push(H1("Dedicatoria y agradecimientos"));
children.push(P("A mi familia y a las personas que me han acompañado durante el Grado, por su apoyo constante. A los tutores del Trabajo de Fin de Grado, por su orientación y su disponibilidad. Y a la comunidad de software libre que mantiene las herramientas (poke-env, Stable-Baselines3, Pokémon Showdown) sin las cuales este proyecto no habría sido posible."));

// ================= RESUMEN =================
children.push(H1("Resumen y palabras clave"));
children.push(H2("Resumen"));
children.push(P("El presente Trabajo de Fin de Grado aborda el diseño, la implementación y el entrenamiento de un agente de inteligencia artificial capaz de jugar combates de Pokémon mediante aprendizaje por refuerzo (Reinforcement Learning, RL). El problema de partida es la elevada complejidad estratégica del formato competitivo oficial de dobles (Video Game Championships, VGC), caracterizado por información oculta, una alta dimensionalidad de estados y acciones, y la necesidad de coordinar dos Pokémon simultáneamente. Para acotar la dificultad, el trabajo siguió un enfoque incremental: primero se construyó un agente para combates individuales (singles) y, una vez validada la arquitectura, se extendió a combates dobles VGC. El agente se entrena con el algoritmo Proximal Policy Optimization (PPO) con enmascaramiento de acciones, sobre una representación rica del estado de combate (efectividades de tipo, climatología, terrenos, prioridades, estados alterados, estadísticas y cambios de estadística). Se compararon dos arquitecturas de red —un perceptrón multicapa y un extractor basado en mecanismos de atención (Transformer)— y se incorporaron modos de entrenamiento por self-play y frente a rivales heurísticos. El agente se conecta a un servidor local de Pokémon Showdown, y su rendimiento se evaluó mediante la tasa de victorias frente a oponentes de referencia. Los resultados muestran que el agente aprende políticas legales y competentes que superan ampliamente al juego aleatorio. El trabajo deja como línea abierta la incorporación de clonación de comportamiento (Behaviour Cloning) a partir de repeticiones de partidas reales, cuya implementación se intentó sin éxito durante el desarrollo."));
children.push(H2("Palabras clave"));
children.push(P("aprendizaje por refuerzo, inteligencia artificial, Pokémon VGC, PPO, enmascaramiento de acciones, transformer, self-play, poke-env, Pokémon Showdown"));
children.push(H2("Abstract"));
children.push(P("This Bachelor's Thesis addresses the design, implementation and training of an artificial intelligence agent able to play Pokémon battles through Reinforcement Learning (RL). The starting problem is the high strategic complexity of the official competitive double-battle format (Video Game Championships, VGC), characterised by hidden information, a high dimensionality of states and actions, and the need to coordinate two Pokémon at once. To bound this difficulty, the work followed an incremental approach: a single-battle agent was built first and, once the architecture had been validated, it was extended to VGC double battles. The agent is trained with the Proximal Policy Optimization (PPO) algorithm using action masking, over a rich representation of the battle state (type effectiveness, weather, terrains, move priorities, status conditions, stats and stat boosts). Two network architectures were compared —a multilayer perceptron and an attention-based (Transformer) feature extractor— and self-play and heuristic-opponent training modes were introduced. The agent connects to a local Pokémon Showdown server, and its performance was evaluated through the win rate against baseline opponents. Results show that the agent learns legal and competent policies that clearly outperform random play. The incorporation of Behaviour Cloning from real game replays, attempted unsuccessfully during development, is left as an open research line."));
children.push(H2("Keywords"));
children.push(P("reinforcement learning, artificial intelligence, Pokémon VGC, PPO, action masking, transformer, self-play, poke-env, Pokémon Showdown"));

// ================= GLOSARIO =================
children.push(H1("Glosario de términos y acrónimos"));
children.push(P("Para facilitar la lectura, se recogen a continuación los principales términos y acrónimos empleados en la memoria. Todos ellos se definen, además, la primera vez que aparecen en el texto."));
children.push(tbl(
  ["Término / acrónimo", "Definición"],
  [
    ["IA", "Inteligencia artificial."],
    ["RL (Reinforcement Learning)", "Aprendizaje por refuerzo: aprendizaje mediante prueba y error guiado por recompensas."],
    ["MDP", "Proceso de decisión de Markov; marco formal del aprendizaje por refuerzo."],
    ["Política", "Función que asigna a cada estado una distribución de probabilidad sobre las acciones."],
    ["Recompensa", "Señal numérica que el entorno devuelve al agente tras cada acción."],
    ["PPO", "Proximal Policy Optimization; algoritmo de gradiente de política actor-crítico."],
    ["Action masking", "Enmascaramiento de acciones: impide que la política elija acciones ilegales."],
    ["MaskablePPO", "Variante de PPO con enmascaramiento de acciones (biblioteca sb3-contrib)."],
    ["Self-play", "Entrenamiento del agente frente a copias de su propia política."],
    ["MLP", "Perceptrón multicapa; red neuronal de capas densas."],
    ["Transformer", "Arquitectura de red basada en mecanismos de atención."],
    ["Token CLS", "Ficha especial de resumen que condensa la información del conjunto."],
    ["VGC", "Video Game Championships; formato competitivo oficial de combates dobles."],
    ["Teampreview", "Fase previa de selección de Pokémon a partir de una vista parcial del rival."],
    ["STAB", "Bonificación de daño por usar un movimiento del mismo tipo que el Pokémon."],
    ["Teracristalización", "Mecánica que permite cambiar el tipo de un Pokémon una vez por combate."],
    ["Behaviour Cloning", "Clonación de comportamiento: aprendizaje supervisado a partir de demostraciones."],
    ["poke-env", "Biblioteca de Python para programar y entrenar agentes en Pokémon Showdown."],
    ["Pokémon Showdown", "Simulador de combates de Pokémon de código abierto."],
    ["Gymnasium", "Estándar de interfaz para entornos de aprendizaje por refuerzo (sucesor de gym)."],
    ["Stable-Baselines3", "Biblioteca de implementaciones de algoritmos de aprendizaje por refuerzo."],
    ["PyTorch", "Biblioteca de aprendizaje profundo usada como motor de las redes neuronales."],
    ["TensorBoard", "Herramienta de visualización de métricas de entrenamiento."],
  ],
  [3200, 6160]
));

// ================= 1. INTRODUCCIÓN =================
children.push(H1("1. Introducción"));
children.push(P("Los videojuegos han constituido históricamente uno de los bancos de pruebas más fértiles para la inteligencia artificial (IA). Desde el ajedrez hasta los juegos de estrategia en tiempo real, los entornos lúdicos ofrecen reglas bien definidas, objetivos claros y una dificultad escalable, lo que los convierte en escenarios ideales para estudiar la toma de decisiones secuenciales. En la última década, el aprendizaje por refuerzo profundo ha logrado hitos notables en este terreno, alcanzando o superando el nivel humano en dominios tan dispares como los videojuegos de Atari, el Go o juegos de gran escala como StarCraft II y Dota 2."));
children.push(P("Pokémon, y muy especialmente su formato competitivo oficial de combates dobles (VGC), representa un dominio particularmente interesante y todavía poco explorado para el aprendizaje por refuerzo. A diferencia de los juegos de información perfecta, un combate de Pokémon combina información oculta (el equipo y los objetos del rival no se conocen por completo), aleatoriedad (precisión de los movimientos, golpes críticos, efectos secundarios), un espacio de acciones amplio y, en el caso de dobles, la necesidad de coordinar dos criaturas a la vez. Esta combinación de factores plantea un reto de gran riqueza estratégica."));
children.push(P("El presente trabajo se enmarca en este contexto y persigue construir, entrenar y evaluar un agente de IA capaz de competir en combates de Pokémon, prestando especial atención al formato dobles VGC. La motivación nace tanto del interés académico por el aprendizaje por refuerzo como del atractivo de un dominio competitivo con una comunidad activa y un simulador abierto (Pokémon Showdown) que permite jugar y validar de forma reproducible."));
children.push(P([run("Convenios de redacción. ", { bold: true }), run("A lo largo de la memoria, los nombres de ficheros, identificadores de código, formatos de combate y comandos se escriben en "), run("cursiva o en tipografía monoespaciada", { italics: true }), run(". Los términos técnicos en inglés ampliamente aceptados en la disciplina (por ejemplo, "), run("reinforcement learning", { italics: true }), run(" o "), run("self-play", { italics: true }), run(") se mantienen en su idioma original y se definen la primera vez que aparecen. La memoria se redacta en un estilo impersonal, como es propio de este tipo de trabajos.")]));

children.push(H2("1.1. Parte grupal"));
children.push(P("[Sección común a todo el equipo — pendiente de redacción conjunta. Debe incluir el mismo texto para todos los integrantes: descripción del proyecto grupal y sus mecánicas principales, ambientación y sinopsis, posicionamiento y público potencial.]", { italics: true }));

children.push(H2("1.2. Parte individual"));
children.push(P("El trabajo individual recogido en esta memoria se centra en la programación de inteligencia artificial mediante aprendizaje por refuerzo. En concreto, la labor desarrollada por el autor abarcó: la integración del proyecto con un servidor de Pokémon Showdown; la construcción de los entornos de entrenamiento compatibles con el estándar Gymnasium; el diseño de la representación del estado del combate (la observación) y de la función de recompensa; la implementación del entrenamiento con PPO y enmascaramiento de acciones; el desarrollo de dos arquitecturas de red comparables (perceptrón multicapa y Transformer); la incorporación de modos de juego por self-play y frente a rivales heurísticos; y la evaluación sistemática del agente frente a oponentes de referencia."));
children.push(P("Desde el punto de vista de la justificación y el contexto, el problema que se aborda es cómo lograr que un agente aprenda, sin reglas escritas a mano, a tomar decisiones competentes en un entorno de información imperfecta y elevada dimensionalidad como es el VGC. El planteamiento propuesto consiste en aplicar aprendizaje por refuerzo moderno (PPO con enmascaramiento de acciones) sobre una representación rica del estado, y comparar arquitecturas de red de distinta capacidad. La metodología seguida fue iterativa e incremental, partiendo de un caso sencillo (singles) hacia el objetivo final (dobles VGC). Los resultados confirman que el agente aprende políticas legales y claramente superiores al azar; el detalle se ofrece en los apartados correspondientes."));
children.push(P("En cuanto a la organización del documento, tras esta introducción se enumeran los objetivos generales (apartado 2); a continuación se realiza un repaso del estado de la cuestión sobre IA, aprendizaje por refuerzo y el dominio de Pokémon competitivo (apartado 3); se describe la metodología de la investigación (apartado 4); se detalla el desarrollo del proyecto y la relación de tareas, en orden cronológico (apartado 5); se presentan los resultados y las conclusiones (apartado 6); se realiza el post mortem y se plantean las líneas de futuro (apartado 7); y, finalmente, se describen los anexos (apartado 8) y se recogen las referencias bibliográficas (apartado 9)."));

// ================= 2. OBJETIVOS =================
children.push(H1("2. Objetivos generales"));
children.push(P("[Resumen de los objetivos del proyecto grupal — común a todo el equipo, pendiente de redacción conjunta.]", { italics: true }));
children.push(P("A nivel individual, el objetivo general del trabajo es diseñar, entrenar y evaluar un agente de aprendizaje por refuerzo capaz de jugar combates de Pokémon de forma competente, con énfasis en el formato dobles VGC. Este objetivo general se concreta en los siguientes objetivos específicos, ordenados por relevancia:"));
children.push(bullet([run("OE1. ", { bold: true }), run("Construir un entorno de entrenamiento reproducible que conecte un agente de RL con un servidor local de Pokémon Showdown, compatible con la interfaz estándar Gymnasium y con el ecosistema Stable-Baselines3.")]));
children.push(bullet([run("OE2. ", { bold: true }), run("Diseñar una representación del estado del combate (observación) suficientemente rica como para que el agente pueda razonar sobre tipos, efectividades, clima, terreno, estados alterados, estadísticas y prioridades.")]));
children.push(bullet([run("OE3. ", { bold: true }), run("Implementar el entrenamiento mediante PPO con enmascaramiento de acciones, de modo que el agente solo considere jugadas legales en cada turno.")]));
children.push(bullet([run("OE4. ", { bold: true }), run("Extender el agente desde combates individuales (singles) hasta combates dobles VGC, validando que la arquitectura generaliza al caso de dos Pokémon activos.")]));
children.push(bullet([run("OE5. ", { bold: true }), run("Comparar dos arquitecturas de red (un perceptrón multicapa y un extractor basado en atención de tipo Transformer) y analizar su efecto sobre el rendimiento.")]));
children.push(bullet([run("OE6. ", { bold: true }), run("Incorporar distintos regímenes de oponente durante el entrenamiento (aleatorio, heurístico y self-play) y permitir el enfrentamiento entre modelos entrenados.")]));
children.push(bullet([run("OE7. ", { bold: true }), run("Evaluar cuantitativamente el agente mediante la tasa de victorias frente a oponentes de referencia y, a partir de ello, determinar si los objetivos anteriores se han alcanzado.")]));
children.push(P("Cada uno de estos objetivos está formulado de manera que pueda responderse con un «sí» o un «no» al final del trabajo, y todos ellos están directamente conectados con los resultados expuestos en el apartado 6."));

// ================= 3. MARCO =================
children.push(H1("3. Marco conceptual y contextual: el estado de la cuestión"));
children.push(P("Este apartado ofrece una visión panorámica del conocimiento existente sobre los tres pilares en los que se asienta el trabajo: la inteligencia artificial y el aprendizaje por refuerzo, su aplicación a los videojuegos, y el dominio concreto de Pokémon competitivo en formato VGC. Sobre esta base se identifica el hueco que el proyecto pretende abordar."));

children.push(H2("3.1. Inteligencia artificial y aprendizaje por refuerzo"));
children.push(P("El aprendizaje por refuerzo es un paradigma del aprendizaje automático en el que un agente aprende a comportarse en un entorno mediante prueba y error, guiado por una señal de recompensa. Formalmente, el problema se modela como un proceso de decisión de Markov, en el que el agente observa un estado, ejecuta una acción, recibe una recompensa y transita a un nuevo estado; el objetivo es aprender una política que maximice la recompensa acumulada esperada (Sutton y Barto, 2018)."));
children.push(P("Más formalmente, un proceso de decisión de Markov queda definido por un conjunto de estados, un conjunto de acciones, una función de transición que determina la probabilidad de pasar de un estado a otro al ejecutar una acción, una función de recompensa y un factor de descuento que pondera la importancia de las recompensas futuras frente a las inmediatas. La política del agente es una función que, dado un estado, devuelve una distribución de probabilidad sobre las acciones. El objetivo del aprendizaje es hallar la política que maximiza el retorno, entendido como la suma descontada de recompensas a lo largo del episodio. Para guiar esta búsqueda se emplean funciones de valor, que estiman el retorno esperado desde un estado (función de valor de estado) o desde un par estado-acción (función de valor de acción)."));
children.push(P("Los algoritmos modernos suelen pertenecer a la familia actor-crítico, que combina dos componentes: un actor, que representa la política y decide qué acción tomar, y un crítico, que estima la función de valor y proporciona una señal de aprendizaje de menor varianza al actor. La combinación del aprendizaje por refuerzo con redes neuronales profundas —el aprendizaje por refuerzo profundo— permitió superar la limitación de los métodos tabulares en espacios de estados muy grandes. Un hito fundacional fue el trabajo de Mnih et al. (2015), que entrenó un único agente capaz de jugar a numerosos videojuegos de Atari a partir de los píxeles de la pantalla."));
children.push(P("Entre los algoritmos modernos, Proximal Policy Optimization (PPO) (Schulman et al., 2017) se ha consolidado como uno de los más utilizados por su estabilidad y sencillez. PPO es un método de gradiente de política de tipo actor-crítico que, en lugar de aplicar directamente el gradiente, optimiza una función objetivo «recortada» (clipped) que penaliza los cambios demasiado grandes en la política respecto a la versión anterior. De este modo se evita que una única actualización desestabilice el aprendizaje, un problema frecuente en los métodos de gradiente de política clásicos. PPO es, además, un algoritmo on-policy: aprende a partir de las experiencias generadas por la propia política actual, recogidas en ciclos (rollouts) de un número fijo de pasos."));
children.push(P("Dos cuestiones transversales condicionan el éxito del aprendizaje por refuerzo. La primera es el equilibrio entre exploración y explotación: el agente debe explorar acciones nuevas para descubrir comportamientos mejores, pero también explotar lo aprendido para obtener recompensa. En PPO, este equilibrio se favorece añadiendo a la función objetivo un término de entropía, que premia mantener cierta aleatoriedad en la política y evita una convergencia prematura a comportamientos subóptimos. La segunda es la estimación de la ventaja, esto es, cuánto mejor o peor es una acción respecto a lo esperado en ese estado; PPO emplea habitualmente la estimación generalizada de la ventaja (GAE), que combina información de varios pasos para reducir la varianza del aprendizaje sin introducir un sesgo excesivo."));
children.push(P("Conviene subrayar que PPO, al ser on-policy, tiende a requerir un volumen de interacción elevado: cada actualización consume experiencias recientes que después se descartan. En dominios donde generar experiencia es costoso —como un combate de Pokémon, que exige comunicación con un simulador externo— esta característica condiciona los tiempos de entrenamiento y motiva el cuidado en la eficiencia de la recogida de datos."));
children.push(P("Un aspecto especialmente relevante para dominios con muchas acciones, algunas de ellas ilegales según el estado, es el enmascaramiento de acciones (action masking). Huang y Ontañón (2022) analizan en detalle esta técnica y muestran que enmascarar las acciones inválidas —impidiendo que la política les asigne probabilidad— mejora de forma notable el aprendizaje frente a la alternativa de penalizar las acciones ilegales mediante la recompensa. El enmascaramiento evita que el agente «malgaste» exploración en jugadas imposibles y garantiza que toda acción seleccionada sea ejecutable, lo que resulta especialmente valioso en combates dobles, donde el número de acciones por turno es muy elevado."));
children.push(P("Por último, la arquitectura Transformer (Vaswani et al., 2017), basada en mecanismos de atención, ha transformado el procesamiento de secuencias y conjuntos. Su capacidad para modelar relaciones entre elementos mediante atención la hace atractiva para representar entidades heterogéneas (en este caso, Pokémon y movimientos) y las relaciones entre ellas."));

children.push(H2("3.2. Aprendizaje por refuerzo en videojuegos"));
children.push(P("Los videojuegos han sido protagonistas de varios de los avances más visibles del aprendizaje por refuerzo. En juegos de información perfecta, AlphaGo (Silver et al., 2016) y posteriormente AlphaZero (Silver et al., 2018) demostraron que el self-play —el entrenamiento del agente frente a copias de sí mismo— permite alcanzar y superar el nivel humano partiendo de un conocimiento mínimo de las reglas. El self-play resulta clave porque genera automáticamente un currículo de dificultad creciente: a medida que el agente mejora, también lo hace su rival."));
children.push(P("En entornos de mayor complejidad, con información imperfecta y horizontes largos, destacan AlphaStar para StarCraft II (Vinyals et al., 2019) y OpenAI Five para Dota 2 (Berner et al., 2019). Ambos sistemas combinan aprendizaje por refuerzo a gran escala con arquitecturas neuronales sofisticadas y poblaciones de agentes, y ponen de manifiesto la dificultad de los dominios multiagente con observabilidad parcial. Estos trabajos sirven de referencia metodológica para el presente proyecto, si bien a una escala de recursos mucho menor."));
children.push(P("Un aspecto importante de los juegos competitivos es la no transitividad: que un agente A venza a B y B a C no garantiza que A venza a C, igual que sucede en el clásico piedra-papel-tijera. Esta propiedad complica el self-play simple, ya que el agente puede «olvidar» cómo derrotar a estrategias antiguas mientras se especializa contra su versión más reciente. Para mitigarlo, los sistemas avanzados recurren a esquemas de entrenamiento poblacional, como el juego ficticio (fictitious play) —en el que el agente se entrena contra una mezcla de versiones pasadas— o el doble oráculo (double oracle), que selecciona los rivales en función de un equilibrio de la teoría de juegos. Estas ideas, presentes en los agentes de referencia, contextualizan los distintos regímenes de oponente explorados en este trabajo (rival aleatorio, heurístico y self-play)."));

children.push(H2("3.3. Pokémon como dominio de IA y el competitivo VGC"));
children.push(P("Un combate de Pokémon es un juego por turnos entre dos entrenadores. Cada entrenador dispone de un equipo de Pokémon, cada uno con un tipo (o dos), unas estadísticas, una habilidad, un objeto y hasta cuatro movimientos. El resultado de cada acción depende de un sistema de efectividades de tipo, de modificadores (clima, terreno, cambios de estadística, estados alterados) y de componentes aleatorios. El formato oficial Video Game Championships (VGC) es de combates dobles: cada jugador tiene dos Pokémon activos simultáneamente y debe seleccionar una acción para cada uno, lo que dispara la dimensionalidad del espacio de acciones y exige coordinar ambas criaturas."));
children.push(P("Las reglas del combate añaden una notable profundidad estratégica. El sistema de efectividades de tipo determina que un mismo movimiento pueda ser superefectivo, neutro, poco efectivo o nulo según los tipos del objetivo; la bonificación por tipo (STAB) premia usar movimientos del propio tipo; los estados alterados (quemadura, parálisis, sueño, etc.) condicionan el desarrollo del combate; y elementos de campo como el clima o los terrenos modifican el daño y otras propiedades durante varios turnos. En la generación actual se añade la Teracristalización, que permite cambiar el tipo de un Pokémon una vez por combate, ampliando todavía más el abanico de decisiones."));
children.push(P("Desde la perspectiva de la IA, este dominio reúne varias dificultades simultáneas: información oculta (no se conoce con certeza el equipo, los objetos ni los movimientos rivales), estocasticidad (precisión, críticos, efectos secundarios), un espacio de acciones amplio (movimientos con selección de objetivo, cambios, mecánicas como la Teracristalización) y una fase previa de selección de equipo (teampreview), en la que cada jugador elige qué subconjunto de su equipo llevará al combate a partir de una vista parcial del rival. Todo ello convierte al VGC en un entorno multiagente de información imperfecta especialmente exigente, en el que no existe una estrategia óptima fija y la lectura del rival juega un papel central."));
children.push(P("La comunidad dispone de Pokémon Showdown, un simulador de combates de código abierto que implementa con fidelidad las reglas del juego y permite hospedar servidores propios. Sobre él se ha construido poke-env (Sahovic, 2024), una biblioteca de Python que expone una interfaz para programar agentes y entrenarlos por refuerzo, y que incluye soporte para combates dobles y para los formatos VGC. En el ámbito específico del VGC, el proyecto VGC-Bench (Angliss, 2026) propone un conjunto de herramientas y modelos de referencia para entrenar y evaluar agentes mediante distintos paradigmas (self-play, fictitious play, double oracle) e incluye un fork del servidor de Showdown con correcciones de estabilidad. Este proyecto constituye el principal referente del presente trabajo."));

children.push(H2("3.4. Herramientas y trabajos de referencia"));
children.push(P("El ecosistema de software libre en torno a Pokémon facilita enormemente la investigación en este dominio. Pokémon Showdown es un simulador de combates de código abierto, ampliamente utilizado por la comunidad competitiva, que implementa con fidelidad las reglas del juego, incluye todos los formatos oficiales y permite hospedar servidores propios. Su naturaleza abierta resulta clave para la investigación, pues hace posible ejecutar miles de combates de forma local, reproducible y sin depender de los servidores oficiales."));
children.push(P("Sobre Showdown se asienta poke-env (Sahovic, 2024), una biblioteca de Python que abstrae la comunicación por websocket con el simulador y ofrece clases de alto nivel para programar agentes. En sus versiones recientes, poke-env incorpora entornos compatibles con el estándar Gymnasium tanto para combates individuales como dobles, así como utilidades para envolver el entorno multiagente en uno de un solo agente. Esta biblioteca constituye la base sobre la que se ha construido el agente del presente trabajo, si bien su uso reveló también algunas limitaciones —por ejemplo, en la conversión de ciertas jugadas a acciones en dobles— que motivaron soluciones propias descritas en el apartado de desarrollo."));
children.push(P("En el ámbito específico del VGC, el proyecto VGC-Bench (Angliss, 2026) constituye el principal referente. Propone un conjunto de herramientas, modelos preentrenados y protocolos de evaluación para entrenar agentes mediante distintos paradigmas de aprendizaje por refuerzo (self-play puro, juego ficticio, doble oráculo y entrenamiento frente a un explotador), e incluye una arquitectura de política basada en atención y un fork del servidor de Showdown con correcciones de estabilidad. El presente trabajo se inspira en sus ideas —en particular en el enfoque basado en atención y en el uso de su servidor adaptado— aunque desarrolla una implementación propia y a menor escala."));
children.push(P("Para los algoritmos de aprendizaje por refuerzo se ha empleado Stable-Baselines3 (Raffin et al., 2021), una de las bibliotecas de referencia por su fiabilidad y documentación, junto con su extensión sb3-contrib, que aporta la variante de PPO con enmascaramiento de acciones (MaskablePPO). Reutilizar implementaciones contrastadas, en lugar de programar los algoritmos desde cero, reduce el riesgo de errores sutiles y permite centrar el esfuerzo en lo específico del dominio: la representación del estado, la función de recompensa y la arquitectura de la política. En este trabajo, Stable-Baselines3 es quien orquesta el ciclo de entrenamiento —recogida de experiencia, cálculo de la pérdida y actualización de la red—, mientras que sb3-contrib aporta el enmascaramiento que garantiza que el agente solo considere jugadas legales."));
children.push(P("La comunicación entre el entorno de combate y los algoritmos se articula a través de Gymnasium, el estándar de facto para entornos de aprendizaje por refuerzo en Python. Gymnasium es la evolución mantenida de la antigua biblioteca gym de OpenAI —hoy descontinuada— y define una interfaz común que todo entorno debe respetar: un método de reinicio (reset), un método de avance paso a paso (step) y la descripción formal del espacio de observación y del espacio de acciones. Su papel en el proyecto es doble: por un lado, los entornos de poke-env heredan de esta interfaz, de modo que un combate de Pokémon queda expuesto como un entorno de RL convencional; por otro, al ser el estándar que consume Stable-Baselines3, evita tener que escribir código de unión entre el simulador y el algoritmo. Conviene precisar que se ha utilizado Gymnasium (en su versión 1.2.3) y no el antiguo gym, dado que las versiones recientes de Stable-Baselines3 requieren esta interfaz."));
children.push(P("Las redes neuronales del agente —tanto el perceptrón multicapa como el extractor basado en atención— se construyen y entrenan sobre PyTorch, una de las bibliotecas de aprendizaje profundo más extendidas. PyTorch actúa como motor de cálculo: proporciona los tensores, las capas neuronales y la diferenciación automática que permiten ajustar los parámetros de la red durante el entrenamiento. En la mayor parte del proyecto PyTorch se usa de forma indirecta, pues Stable-Baselines3 lo emplea internamente; no obstante, se utiliza de manera explícita para programar el extractor de características Transformer. Se trabajó con la edición para CPU, con la posibilidad de aprovechar la GPU mediante CUDA cuando está disponible para acelerar el entrenamiento."));
children.push(P("Por último, el seguimiento del entrenamiento se realiza con TensorBoard, una herramienta de visualización que representa, a partir de los registros que genera Stable-Baselines3, la evolución de las métricas a lo largo del entrenamiento (recompensa media, tasa de victorias, entropía de la política, varianza explicada por el crítico, etc.). Su utilidad es eminentemente práctica: permite diagnosticar si un entrenamiento progresa correctamente, comparar de un vistazo distintas configuraciones —por ejemplo, la arquitectura MLP frente a la Transformer, o los distintos regímenes de oponente— y detectar de forma temprana entrenamientos estancados o inestables."));
children.push(P("En conjunto, estas herramientas encajan como un flujo coherente: Pokémon Showdown actúa de simulador (el entorno real); poke-env lo envuelve y lo expone con la interfaz de Gymnasium; Stable-Baselines3 y sb3-contrib aportan el algoritmo de aprendizaje (MaskablePPO); PyTorch ejecuta y entrena las redes neuronales subyacentes; y TensorBoard permite supervisar todo el proceso. La elección de este conjunto, frente a programar los componentes desde cero, se justifica por su madurez, su amplia adopción en la comunidad y la reproducibilidad que ofrece al fijar versiones concretas de cada dependencia."));
children.push(H2("3.5. Síntesis y hueco detectado"));
children.push(P("Del estudio anterior se extraen varias ideas que orientan el resto del trabajo. En primer lugar, PPO con enmascaramiento de acciones es una elección sólida y bien fundamentada para un dominio con muchas acciones, algunas ilegales según el turno. En segundo lugar, la calidad de la representación del estado es determinante: si el agente no «ve» la efectividad de un movimiento o el clima activo, difícilmente podrá razonar sobre ellos. En tercer lugar, el self-play y la evaluación frente a baselines son prácticas estándar para entrenar y medir agentes de juego."));
children.push(P("El hueco que aborda este trabajo no es la creación de una técnica radicalmente nueva, sino la construcción —de forma propia y didáctica— de un agente de RL para VGC sobre un servidor estándar, partiendo de un caso sencillo (singles) y avanzando hacia dobles, comparando arquitecturas (perceptrón multicapa frente a Transformer) y analizando el efecto de la representación del estado y del tipo de oponente. Se trata, por tanto, de aplicar y combinar con un enfoque propio soluciones ya existentes, que es una contribución plenamente válida para un Trabajo de Fin de Grado."));

// ================= 4. METODOLOGÍA =================
children.push(H1("4. Metodología de la investigación"));
children.push(P("La investigación siguió una metodología fundamentalmente experimental y de carácter incremental e iterativo, complementada con una fase documental inicial (el estado de la cuestión del apartado 3). El método empleado puede describirse como hipotético-deductivo: a partir del conocimiento existente se formularon hipótesis de diseño (por ejemplo, «enriquecer la observación con efectividades de tipo mejorará el juego del agente»), que se implementaron y se contrastaron empíricamente mediante entrenamiento y evaluación."));
children.push(P("El análisis de los datos es predominantemente cuantitativo: la métrica principal es la tasa de victorias del agente frente a distintos oponentes, complementada con la curva de recompensa media durante el entrenamiento y con indicadores de salud del aprendizaje (varianza explicada, entropía de la política). El procedimiento general de trabajo, repetido en cada iteración, consistió en: (1) implementar o modificar un componente; (2) verificar su corrección con pruebas controladas sin servidor; (3) entrenar contra el servidor local; (4) observar las métricas en TensorBoard; y (5) evaluar el agente resultante frente a oponentes de referencia."));
children.push(P("La estrategia de acotación del problema fue clave: en lugar de atacar directamente el caso más difícil (dobles VGC), se comenzó por el caso más simple (singles) para validar la infraestructura y la arquitectura, y solo después se extendió a dobles. Esta decisión metodológica, de lo particular a lo general, permitió detectar y corregir problemas de integración en un escenario más manejable."));
children.push(P("Las herramientas empleadas fueron: Python como lenguaje principal; poke-env como interfaz con el simulador; Stable-Baselines3 (Raffin et al., 2021) y su extensión sb3-contrib para los algoritmos de RL (PPO y su variante con enmascaramiento, MaskablePPO); PyTorch como motor de redes neuronales; Gymnasium como estándar de entornos; TensorBoard para el seguimiento del entrenamiento; y un servidor local de Pokémon Showdown (en su variante adaptada de VGC-Bench) como entorno de combate. El control de versiones y la gestión del entorno se realizaron con Git y con entornos virtuales de Python."));
children.push(P("El protocolo de evaluación merece una mención específica, pues de él dependen los resultados. La métrica fundamental es la tasa de victorias, definida como el cociente entre combates ganados y combates terminados. Para reducir el ruido inherente a la aleatoriedad del juego, cada evaluación se realiza sobre un número elevado de combates (del orden del centenar por enfrentamiento). Como oponentes de referencia (baselines) se emplean tres jugadores no entrenados disponibles en la biblioteca: uno que juega de forma aleatoria entre las acciones legales, uno que siempre elige el movimiento de mayor potencia y uno heurístico que aplica reglas sencillas de efectividad y de cambio. Estos baselines proporcionan un marco de comparación estable y reproducible: un agente competente debe superar ampliamente al jugador aleatorio y aproximarse o superar al heurístico."));
children.push(P("Durante el entrenamiento, además de la tasa de victorias, se registran y analizan varias métricas que informan sobre la salud del aprendizaje: la recompensa media por episodio (indicador del margen de victoria), la entropía de la política (que debe decrecer a medida que el agente gana confianza), la varianza explicada por la función de valor (que indica si el crítico predice bien los retornos) y la tasa de aprendizaje efectiva. El seguimiento se realiza con TensorBoard, lo que permite comparar de forma visual distintas configuraciones (por ejemplo, arquitecturas o regímenes de oponente)."));
children.push(P("La reproducibilidad se cuidó de forma explícita: todas las dependencias se fijaron a versiones concretas, el entorno de ejecución se aisló en un entorno virtual y los experimentos se identifican mediante una semilla y un identificador de ejecución, lo que organiza los modelos y los registros por formato y configuración. Esta disciplina permite reconstruir el entorno en otra máquina y repetir los experimentos en condiciones equivalentes."));
children.push(P("La siguiente tabla resume los tipos de metodología empleados a lo largo del trabajo, siguiendo la clasificación habitual en investigación."));
children.push(tbl(
  ["Metodología", "Uso en el trabajo"],
  [
    ["Documental", "Estudio del estado de la cuestión (apartado 3) y de la documentación de las herramientas."],
    ["Experimental", "Entrenamiento y evaluación de agentes; comparación de arquitecturas y oponentes."],
    ["Inductiva (particular→general)", "Validación primero en singles y posterior extensión a dobles VGC."],
    ["Comparativa", "Enfrentamiento entre arquitecturas (MLP vs Transformer) y frente a baselines."],
    ["Cuantitativa", "Medición de la tasa de victorias y de métricas de entrenamiento."],
  ],
  [3000, 6360]
));

// ================= 5. DESARROLLO =================
children.push(H1("5. Desarrollo del proyecto"));
children.push(P("Este apartado describe de forma detallada el trabajo individual realizado. Se estructura en los roles de programación asumidos, el análisis de requisitos técnicos y la relación de tareas, esta última dividida en tareas de desarrollo y tareas de investigación, y expuesta en orden cronológico para reflejar fielmente la evolución del proyecto."));

children.push(H2("5.1. Roles de programación"));
children.push(P("El rol individual asumido fue el de programación de inteligencia artificial. Dentro de él, las responsabilidades concretas incluyeron: la programación de la integración con el simulador (cliente de Pokémon Showdown a través de poke-env); la programación de los entornos de aprendizaje por refuerzo (envoltorios compatibles con Gymnasium); la programación de la representación del estado y de la función de recompensa; la programación del bucle de entrenamiento y de las políticas (incluyendo un extractor de características propio basado en atención); y la programación de las utilidades de evaluación (enfrentamiento entre modelos y frente a baselines)."));

children.push(H2("5.2. Análisis"));
children.push(P("Antes de implementar, se fijaron los requisitos técnicos del software individual, respondiendo en cada caso a qué se necesita, por qué y cómo se aborda."));
children.push(bullet([run("Plataforma de ejecución. ", { bold: true }), run("PC con sistema operativo Windows; el entrenamiento se realiza por CPU, con posibilidad de usar GPU (CUDA) si está disponible. Se requiere Python 3.10–3.13 y Node.js para el servidor. Se justifica por ser el entorno disponible y por la compatibilidad de las bibliotecas empleadas.")]));
children.push(bullet([run("Entorno de combate. ", { bold: true }), run("Servidor local de Pokémon Showdown. Se decidió usar la variante adaptada del proyecto VGC-Bench porque corrige problemas de gestión de salas y tiempos de espera del servidor estándar que provocaban bloqueos en combates largos de dobles. La conexión se realiza por websocket a localhost.")]));
children.push(bullet([run("Interfaz de RL. ", { bold: true }), run("Compatibilidad con el estándar Gymnasium y con Stable-Baselines3, para reutilizar implementaciones de algoritmos contrastadas en lugar de programarlas desde cero.")]));
children.push(bullet([run("Bibliotecas. ", { bold: true }), run("poke-env (interfaz con el simulador), Stable-Baselines3 y sb3-contrib (PPO y MaskablePPO), PyTorch (redes neuronales) y TensorBoard (seguimiento). Se eligieron por ser estándar de facto, estar bien documentadas y permitir reproducibilidad mediante versiones fijadas.")]));
children.push(bullet([run("Espacio de acciones. ", { bold: true }), run("Discreto en singles y MultiDiscrete en dobles (una acción por Pokémon activo), incluyendo movimientos con selección de objetivo, cambios y mecánicas como la Teracristalización.")]));
children.push(P("Los requisitos de reproducibilidad se concretaron en la fijación de versiones de todas las dependencias y en la creación de un entorno virtual aislado, de modo que el proyecto pueda reconstruirse en otra máquina."));

children.push(H2("5.3. Relación de tareas"));
children.push(P("A continuación se describen las tareas realizadas. Por claridad, se separan las tareas de desarrollo (infraestructura del proyecto) de las tareas de investigación (propias del avance del TFG), y estas últimas se presentan en el orden cronológico en que se acometieron."));

children.push(H3("5.3.1. Tareas de desarrollo"));
children.push(bullet([run("Integración con el simulador. ", { bold: true }), run("Configuración y puesta en marcha del servidor local de Pokémon Showdown y conexión del agente mediante poke-env, incluyendo la gestión de la configuración de servidor y de las cuentas de los agentes.")]));
children.push(bullet([run("Entornos de entrenamiento. ", { bold: true }), run("Implementación de los envoltorios que convierten el entorno multiagente del simulador en un entorno de un solo agente compatible con Stable-Baselines3, tanto para singles como para dobles.")]));
children.push(bullet([run("Gestión de equipos. ", { bold: true }), run("Carga de equipos en formato Showdown, con soporte tanto para un equipo fijo como para una carpeta de equipos de la que se elige uno aleatorio en cada combate.")]));
children.push(bullet([run("Robustez del entrenamiento. ", { bold: true }), run("Implementación de mecanismos de recuperación ante fallos de comunicación con el servidor (reintentos y reconstrucción del entorno), y validación de equipos para descartar los que no son legales en el formato.")]));
children.push(bullet([run("Utilidades de juego y evaluación. ", { bold: true }), run("Scripts para que el agente acepte desafíos o juegue en la escalera, y para enfrentar dos modelos entre sí o frente a los rivales de referencia de la biblioteca.")]));

children.push(H3("5.3.2. Tareas de investigación (orden cronológico)"));
children.push(P([run("Fase 1 — Agente de singles. ", { bold: true }), run("El trabajo comenzó por el caso más sencillo: combates individuales en formato de batalla aleatoria. Se diseñó una primera observación con información básica del combate y una función de recompensa basada en la victoria o derrota, complementada con un término ligado a la diferencia de puntos de vida. Se entrenó con PPO y se verificó que el agente aprendía a superar al juego aleatorio. Esta fase sirvió, sobre todo, para validar la infraestructura: la conexión con el servidor, el bucle de entrenamiento y la sincronización entre el combate asíncrono del simulador y la interfaz síncrona de Gymnasium.")]));
children.push(P("Una dificultad técnica de fondo en esta primera fase fue la integración entre el combate, que en el simulador es asíncrono (basado en mensajes por websocket), y la interfaz de Gymnasium, que es síncrona (el clásico bucle de reiniciar y avanzar paso a paso). Fue necesario un mecanismo que sincronizara ambos mundos, de modo que cada llamada de avance del entorno se correspondiera con un turno del combate y esperara la respuesta del servidor antes de continuar. La correcta resolución de este puente fue condición indispensable para todo lo demás."));
children.push(P([run("Fase 2 — Extensión a dobles VGC. ", { bold: true }), run("Una vez validado el caso individual, se extendió el agente a combates dobles VGC. Este salto introdujo dificultades nuevas: dos Pokémon activos, un espacio de acciones de tipo MultiDiscrete (una acción por Pokémon), la selección de objetivo de los movimientos y la fase de teampreview. Durante esta fase se detectaron y resolvieron diversos problemas de sincronización y de conversión de acciones a órdenes del simulador.")]));
children.push(P("En particular, el envoltorio de un solo agente que ofrece la biblioteca presentaba un comportamiento problemático en dobles al traducir ciertas jugadas del rival a índices de acción, lo que interrumpía el entrenamiento. Para resolverlo se programó un envoltorio propio en el que la acción del oponente no se obtiene por esa vía conflictiva, sino muestreándola directamente de la máscara de acciones legales del simulador. De este modo, el rival juega siempre acciones válidas (equivalente a un jugador aleatorio legal) y se elimina la fuente de error, manteniendo además la posibilidad de sustituir ese rival por un jugador heurístico o por una política entrenada."));
children.push(P([run("Fase 3 — Enmascaramiento de acciones. ", { bold: true }), run("Se observó que, sin restricciones, el agente proponía con frecuencia acciones ilegales (por ejemplo, usar un movimiento cuando el Pokémon debía cambiar), que el sistema resolvía sustituyéndolas por jugadas aleatorias. Para corregirlo se incorporó el enmascaramiento de acciones mediante MaskablePPO, de modo que el agente solo considera en cada turno las jugadas legales. La máscara se obtiene del propio simulador, lo que garantiza su validez.")]));
children.push(P([run("Fase 4 — Observación rica. ", { bold: true }), run("Se comprobó que una observación pobre llevaba al agente a errores básicos, como insistir en movimientos sin efecto frente a un rival inmune. Para solucionarlo se rediseñó por completo la representación del estado, incorporando, por cada movimiento, su potencia, precisión, prioridad, categoría, tipo y efectividad frente a cada rival; y, por cada Pokémon, sus puntos de vida, estado alterado, tipos, cambios de estadística y estadísticas base, además de información global de clima, terreno, condiciones de cada bando y turno. Esta observación rica es la que «ve» el agente y constituye una de las decisiones de diseño más determinantes del trabajo.")]));
children.push(P([run("Fase 5 — Comparativa de arquitecturas (MLP y Transformer). ", { bold: true }), run("Sobre la observación rica se implementaron dos arquitecturas de red comparables. La primera, un perceptrón multicapa (MLP) que trata la observación como un vector plano. La segunda, un extractor de características basado en atención (Transformer) que interpreta la observación como un conjunto de «fichas» (una por Pokémon, por movimiento y para el estado global), de modo que un mismo codificador procesa todas las entidades del mismo tipo y la atención modela las relaciones entre ellas. Ambas arquitecturas se pueden seleccionar y entrenar por separado para compararlas.")]));
children.push(P([run("Fase 6 — Regímenes de oponente y self-play. ", { bold: true }), run("Se añadieron distintos tipos de rival para el entrenamiento: aleatorio, heurístico (un jugador con reglas) y self-play, en el que el rival juega con la propia política que se está entrenando. Asimismo, se implementó la posibilidad de enfrentar dos modelos entrenados entre sí (por ejemplo, MLP frente a Transformer) y de medir el rendimiento del agente frente a los rivales de referencia.")]));
children.push(P("El self-play se implementó haciendo que el rival del entorno decida sus acciones con la política del modelo en entrenamiento: en cada turno se construye la observación desde la perspectiva del rival, se obtiene su máscara de acciones legales y se consulta la política para elegir la jugada. De este modo, el rival mejora a la vez que el agente, generando un currículo de dificultad creciente. Para la comparación entre modelos ya entrenados se desarrolló una utilidad independiente que carga dos políticas (que pueden tener arquitecturas distintas, pues comparten la misma representación del estado) y las enfrenta durante un número configurable de combates, devolviendo el balance de victorias. Esta utilidad admite también que uno de los contendientes sea un baseline de la biblioteca, lo que habilita directamente el protocolo de evaluación descrito en la metodología."));
children.push(P([run("Fase 7 — Intento de clonación de comportamiento (Behaviour Cloning). ", { bold: true }), run("Como vía de inicialización del agente, se intentó incorporar clonación de comportamiento a partir de repeticiones (logs) de partidas reales, convirtiéndolas en trayectorias de pares estado-acción para un aprendizaje supervisado previo al refuerzo. Esta línea no llegó a buen puerto durante el desarrollo: la obtención y el procesamiento de los logs en trayectorias compatibles con la representación del estado del agente resultó más complejo de lo previsto y no se logró integrar de forma funcional. Se documenta aquí como tarea de investigación realizada, aunque sin éxito, por su valor metodológico y como punto de partida de trabajo futuro.")]));
children.push(P([run("Fase 8 — Estabilidad del servidor. ", { bold: true }), run("Durante los entrenamientos largos de dobles se detectaron bloqueos esporádicos atribuibles a la gestión de salas y a los tiempos de espera del servidor estándar. Se resolvió empleando la variante adaptada del servidor (con correcciones de estabilidad) y añadiendo al cliente, además, los formatos VGC vigentes que faltaban. Esta tarea, de carácter más bien de infraestructura, fue necesaria para poder completar entrenamientos prolongados sin interrupciones.")]));
children.push(H3("5.3.3. Diseño de la observación"));
children.push(P("La representación del estado del combate (la observación) es, junto con el enmascaramiento de acciones, una de las decisiones de diseño más determinantes del trabajo. Se buscó que el agente «viera» toda la información relevante de la que dispone un jugador humano. La observación se construye como un vector de números reales de longitud fija que se rellena con ceros cuando una entidad no existe (por ejemplo, un hueco vacío en el banco). En singles la observación tiene 507 componentes y en dobles 675."));
children.push(P("La observación se organiza por bloques de entidades. Por cada movimiento conocido del Pokémon o Pokémon activos se codifican su potencia, su precisión, su prioridad, su ratio de crítico, su porcentaje de robo de vida y de retroceso, si fuerza el cambio, si provoca autocambio, si es de autodestrucción, su porcentaje de PP restantes y su número esperado de golpes, además de su categoría (físico, especial o estado), su tipo y su efectividad frente a cada rival. Por cada Pokémon se codifican sus puntos de vida, si está debilitado, si está teracristalizado, su estado alterado, sus tipos, sus cambios de estadística y sus estadísticas base. A nivel global se incluye el clima, el terreno y otros campos (como Trick Room), el turno y, por cada bando, las condiciones de campo activas (pantallas, viento afín, etc.). La siguiente tabla resume la composición de la observación en el caso de dobles."));
children.push(tbl(
  ["Bloque", "Contenido", "Dimensión"],
  [
    ["Global", "Clima (8), terreno/campos (6) y turno (1)", "15"],
    ["Condiciones de bando", "10 por bando (propio y rival)", "20"],
    ["Pokémon activos", "40 por Pokémon (2 propios + 2 rivales)", "160"],
    ["Pokémon en banco", "26 por Pokémon (hasta 4 por bando)", "208"],
    ["Movimientos", "34 por movimiento (4 por activo propio)", "272"],
    ["Total (dobles)", "—", "675"],
  ],
  [2600, 5160, 1600]
));
children.push(caption("Tabla 3. Composición de la observación rica del agente en combates dobles (675 componentes). En singles la observación equivalente tiene 507 componentes."));
children.push(P("La importancia de esta representación quedó patente durante la Fase 4: con una observación pobre, el agente cometía errores básicos; al incorporar las efectividades de tipo, dejó de insistir en movimientos sin efecto frente a rivales inmunes. Gran parte de la competencia del agente proviene, por tanto, de la calidad de su observación."));

children.push(H3("5.3.4. Función de recompensa"));
children.push(P("La función de recompensa es escasa (sparse) y está centrada en el resultado del combate: el agente recibe +1 al ganar y −1 al perder. Para facilitar el aprendizaje en las primeras fases, se añadió además un pequeño término de modelado (reward shaping) proporcional a la diferencia de puntos de vida entre el equipo propio y el rival, con un peso reducido. De este modo, la señal de victoria/derrota domina la recompensa total, pero el término intermedio orienta al agente hacia estados ventajosos antes de que el combate concluya. Al ser la recompensa terminal de ±1, la recompensa media por episodio constituye un buen indicador del margen de victoria del agente."));

children.push(H3("5.3.5. Arquitecturas de red: perceptrón multicapa y Transformer"));
children.push(P("Sobre la observación descrita se implementaron dos arquitecturas de red comparables, seleccionables al lanzar el entrenamiento. La primera es un perceptrón multicapa (MLP) que trata la observación como un único vector plano y la procesa con dos capas ocultas de 256 unidades. Es sencilla, rápida y constituye la línea base."));
children.push(P("La segunda es un extractor de características basado en atención (Transformer). En lugar de tratar la observación como un vector indiferenciado, la interpreta como un conjunto de «fichas» (tokens): una por el bloque global, una por cada Pokémon y una por cada movimiento. Cada tipo de entidad se proyecta a una dimensión común mediante una capa lineal compartida —de modo que un mismo codificador procesa todos los Pokémon, otro todos los movimientos, etc.—, lo que favorece la generalización: lo aprendido sobre una entidad sirve para todas las del mismo tipo. A continuación, un codificador Transformer aplica atención entre las fichas, permitiendo que cada una «mire» a las demás y capture relaciones (por ejemplo, entre un atacante y sus posibles objetivos). Una ficha especial de resumen (token CLS) condensa toda la batalla en un único vector que alimenta las cabezas de política y de valor. Esta arquitectura se inspira en el enfoque empleado por los agentes de referencia del dominio."));
children.push(P("La separación de la observación en tokens se realiza mediante un mapa de segmentos coherente con el orden en que se construye el vector, lo que garantiza que cada ficha recibe exactamente los componentes de su entidad. Ambas arquitecturas comparten el resto del procedimiento de entrenamiento, de modo que la comparación entre ellas aísla el efecto de la arquitectura."));

children.push(H3("5.3.6. Configuración del entrenamiento"));
children.push(P("El entrenamiento emplea PPO con enmascaramiento de acciones (MaskablePPO de la biblioteca sb3-contrib). Los principales hiperparámetros se recogen en la siguiente tabla. La tasa de aprendizaje sigue un decaimiento lineal desde su valor inicial hasta cero a lo largo del entrenamiento, lo que estabiliza las últimas fases; por ello conviene fijar el número total de pasos desde el inicio."));
children.push(tbl(
  ["Hiperparámetro", "Valor"],
  [
    ["Algoritmo", "MaskablePPO (PPO con enmascaramiento)"],
    ["Pasos por rollout (n_steps)", "2048"],
    ["Tamaño de lote (batch_size)", "256"],
    ["Épocas por actualización (n_epochs)", "10"],
    ["Factor de descuento (gamma)", "0,99"],
    ["GAE lambda", "0,95"],
    ["Rango de recorte (clip_range)", "0,2"],
    ["Coeficiente de entropía (ent_coef)", "0,01"],
    ["Tasa de aprendizaje", "3e-4 con decaimiento lineal a 0"],
    ["Arquitectura (red base)", "MLP [256, 256] o Transformer + [128, 128]"],
  ],
  [5160, 4200]
));
children.push(caption("Tabla 4. Hiperparámetros principales del entrenamiento por refuerzo."));

children.push(H3("5.3.7. Robustez frente a fallos del servidor"));
children.push(P("Los entrenamientos prolongados de dobles requieren miles de combates consecutivos, durante los cuales pueden producirse fallos de comunicación con el servidor. Para que una sesión larga no se interrumpa por un incidente puntual, se incorporaron varios mecanismos de robustez: reintentos al iniciar un combate cuando el desafío no llega a establecerse; cierre forzado de combates que quedan «colgados» para evitar incoherencias en el reinicio; un vigilante (watchdog) que abandona un turno si tarda más de lo razonable y reconstruye el entorno con una conexión limpia; y la validación previa de los equipos para descartar los que no son legales en el formato. Adicionalmente, se adoptó la variante adaptada del servidor (que corrige la gestión de salas y los tiempos de espera) y se añadieron los formatos VGC vigentes que faltaban en ella. El conjunto de estas medidas permitió completar entrenamientos largos de forma fiable."));

children.push(P("Como resultado de estas tareas se generaron diversos materiales (diagramas de componentes y de clases, código fuente, configuración del servidor y modelos entrenados) que, por su naturaleza y extensión, se entregan como anexos a la memoria y se describen en el apartado 8."));

// ================= 6. RESULTADOS Y CONCLUSIONES =================
children.push(H1("6. Resultados de la investigación y conclusiones"));
children.push(H2("6.1. Resultados"));
children.push(P("Los resultados de la investigación son fundamentalmente cuantitativos y se obtienen de dos fuentes: las métricas registradas durante el entrenamiento (visualizadas con TensorBoard) y las evaluaciones del agente entrenado frente a oponentes de referencia. A continuación se indica dónde debe insertarse cada elemento gráfico o tabular; las figuras y tablas de resultados se ubican en este apartado, mientras que los materiales voluminosos (diagramas UML completos, listados de código) se remiten a los anexos."));
children.push(P([run("Curvas de entrenamiento. ", { bold: true }), run("La evolución del aprendizaje se observa principalmente en dos curvas: la recompensa media por episodio y la tasa de victorias móvil registrada como métrica de evaluación. Dado que la recompensa terminal es +1 por victoria y −1 por derrota, la recompensa media constituye un buen indicador del margen de victoria del agente.")]));
children.push(fig("[FIGURA 1 — Insertar aquí: curva de recompensa media por episodio (rollout/ep_rew_mean) frente a los pasos de entrenamiento, exportada de TensorBoard.]"));
children.push(caption("Figura 1. Evolución de la recompensa media durante el entrenamiento del agente."));
children.push(fig("[FIGURA 2 — Insertar aquí: curva de tasa de victorias (eval/win_rate) frente a los pasos de entrenamiento, exportada de TensorBoard.]"));
children.push(caption("Figura 2. Evolución de la tasa de victorias móvil durante el entrenamiento."));
children.push(P([run("Rendimiento frente a oponentes de referencia. ", { bold: true }), run("La evaluación principal consiste en medir la tasa de victorias del agente entrenado frente a tres rivales de referencia: un jugador aleatorio, un jugador que siempre elige el movimiento de mayor potencia y un jugador heurístico con reglas. La siguiente tabla recoge el formato de presentación recomendado; los valores deben completarse con los resultados de las evaluaciones realizadas con la utilidad de enfrentamiento entre agentes (un número de combates suficientemente alto, por ejemplo 100, para reducir el ruido).")]));
children.push(tbl(
  ["Oponente de referencia", "Tasa de victorias MLP", "Tasa de victorias Transformer"],
  [
    ["Aleatorio (RandomPlayer)", "[completar] %", "[completar] %"],
    ["Máxima potencia (MaxBasePower)", "[completar] %", "[completar] %"],
    ["Heurístico (SimpleHeuristics)", "[completar] %", "[completar] %"],
  ],
  [3760, 2800, 2800]
));
children.push(caption("Tabla 1. Tasa de victorias del agente frente a oponentes de referencia, por arquitectura (100 combates por enfrentamiento)."));
children.push(P([run("Comparativa de arquitecturas y enfrentamiento directo. ", { bold: true }), run("Además de la evaluación frente a baselines, se recomienda incluir el resultado del enfrentamiento directo entre el modelo con perceptrón multicapa y el modelo con Transformer, así como, en su caso, la comparación entre distintos regímenes de oponente (aleatorio, heurístico y self-play).")]));
children.push(fig("[TABLA 2 — Insertar aquí: resultado del enfrentamiento directo MLP vs Transformer (victorias de cada uno y empates sobre N combates).]"));
children.push(caption("Tabla 2. Enfrentamiento directo entre arquitecturas y entre regímenes de oponente."));
children.push(H3("6.1.1. Dinámica del entrenamiento"));
children.push(P("Más allá del rendimiento final, el análisis de las métricas de entrenamiento ofrece información valiosa sobre el proceso de aprendizaje. La recompensa media por episodio crece de forma sostenida en las primeras fases y tiende a estabilizarse, lo que indica que el agente ha alcanzado un nivel de juego competente frente al rival de entrenamiento. La entropía de la política decrece progresivamente: al principio el agente explora de forma casi uniforme y, conforme aprende, concentra la probabilidad en las acciones que considera mejores, volviéndose más decidido. La varianza explicada por la función de valor informa de la calidad de las predicciones del crítico; valores moderados o altos indican que es capaz de anticipar razonablemente el resultado de los combates."));
children.push(P("Un detalle relevante observado durante los entrenamientos es el efecto del decaimiento de la tasa de aprendizaje. Dado que esta decrece linealmente hasta anularse al alcanzar el número total de pasos fijado, las últimas etapas apenas modifican la política (la divergencia entre actualizaciones tiende a cero). Esta observación tiene una implicación práctica: conviene fijar desde el inicio un presupuesto de pasos generoso, en lugar de ampliarlo a mitad de un entrenamiento ya finalizado, para que el decaimiento se reparta de forma homogénea a lo largo de toda la sesión."));
children.push(H3("6.1.2. Sobre el intento de clonación de comportamiento"));
children.push(P("Como resultado negativo, pero metodológicamente relevante, debe documentarse el intento de incorporar clonación de comportamiento a partir de repeticiones de partidas reales. La idea consistía en descargar registros de combates de alto nivel, transformarlos en trayectorias de pares estado-acción y emplearlos para un preentrenamiento supervisado de la política antes del refuerzo. La dificultad principal residió en la conversión de los registros al mismo espacio de observación y de acciones que utiliza el agente: alinear la información de cada turno con la representación rica del estado, y traducir cada decisión humana a un índice de acción válido, resultó más complejo de lo previsto, y no se logró una canalización funcional dentro del tiempo disponible. Este resultado se interpreta no como un fracaso, sino como la delimitación de una línea de trabajo que requiere un esfuerzo de ingeniería de datos específico, y se retoma en el apartado de líneas de futuro."));
children.push(P("Del análisis de estos resultados se desprende lo siguiente. En primer lugar, el agente entrenado aprende políticas legales (gracias al enmascaramiento de acciones) y claramente superiores al juego aleatorio, lo que valida el conjunto de la infraestructura y del diseño. En segundo lugar, la riqueza de la observación es determinante: tras incorporar las efectividades de tipo, el agente dejó de cometer errores tan básicos como insistir en movimientos sin efecto frente a un rival inmune. En tercer lugar, la comparación entre arquitecturas permite analizar el efecto de incorporar mecanismos de atención frente a un perceptrón multicapa, así como su coste computacional. La discusión detallada de estos resultados, una vez completadas las tablas, debe conectarse explícitamente con los objetivos del apartado 2."));

children.push(H2("6.2. Conclusiones"));
children.push(P("Las conclusiones cierran el círculo abierto con los objetivos. A partir del trabajo realizado y de los resultados obtenidos, se concluye lo siguiente."));
children.push(bullet([run("Sobre OE1–OE3. ", { bold: true }), run("Se ha construido con éxito un entorno de entrenamiento reproducible que conecta el agente con un servidor local de Pokémon Showdown, con una observación rica y con enmascaramiento de acciones mediante PPO. El agente nunca elige acciones ilegales y aprende de forma estable. Estos objetivos se consideran alcanzados.")]));
children.push(bullet([run("Sobre OE4. ", { bold: true }), run("El agente se extendió satisfactoriamente desde singles hasta dobles VGC, confirmando que la arquitectura y la metodología generalizan al caso de dos Pokémon activos. Objetivo alcanzado.")]));
children.push(bullet([run("Sobre OE5–OE6. ", { bold: true }), run("Se implementaron y pudieron compararse dos arquitecturas de red (perceptrón multicapa y Transformer) y distintos regímenes de oponente (aleatorio, heurístico y self-play), así como el enfrentamiento entre modelos. Objetivos alcanzados a nivel de implementación; el alcance del análisis comparativo depende del volumen de entrenamiento disponible.")]));
children.push(bullet([run("Sobre OE7. ", { bold: true }), run("El agente se evaluó cuantitativamente mediante la tasa de victorias frente a oponentes de referencia, superando con claridad al juego aleatorio. Objetivo alcanzado.")]));
children.push(P("Más allá del cumplimiento de los objetivos, el trabajo permitió adquirir conocimientos que no formaban parte del temario del Grado o que se habían tratado de forma introductoria: el aprendizaje por refuerzo profundo y el algoritmo PPO, el enmascaramiento de acciones, los mecanismos de atención de las arquitecturas Transformer, la integración asíncrona con un simulador externo y las particularidades de los entornos multiagente de información imperfecta. La principal lección metodológica es el valor de un enfoque incremental (de singles a dobles) y de una representación del estado cuidadosamente diseñada: gran parte de la competencia del agente provino de «dejarle ver» la información adecuada, más que de complicar el algoritmo."));
children.push(P("Como reflexión final, el trabajo demuestra que es viable, con recursos modestos y herramientas abiertas, construir un agente de aprendizaje por refuerzo competente para un dominio tan complejo como el VGC. La comparación entre arquitecturas y la evaluación frente a baselines aportan, además, un componente de investigación que enriquece el proyecto más allá del mero desarrollo."));

// ================= 7. POST MORTEM =================
children.push(H1("7. Post mortem del desarrollo y líneas de futuro"));
children.push(P("[Post mortem del proyecto grupal — común a todo el equipo, pendiente de redacción conjunta. Debe indicar si se alcanzaron los objetivos del proyecto en su conjunto, qué quedó sin hacer y cómo podría lograrse.]", { italics: true }));
children.push(P("En lo relativo a la investigación individual, conviene dejar constancia honesta de las limitaciones y de los caminos abiertos. La principal tarea que no llegó a completarse fue la clonación de comportamiento a partir de repeticiones reales: la conversión de los logs en trayectorias compatibles con la observación del agente resultó más compleja de lo previsto y no se integró de forma funcional. Igualmente, el alcance del análisis comparativo entre arquitecturas y regímenes de oponente quedó condicionado por el tiempo de cómputo disponible, al realizarse el entrenamiento principalmente por CPU."));
children.push(P("A partir de lo anterior, se identifican las siguientes líneas de futuro, ordenadas por interés:"));
children.push(bullet([run("Clonación de comportamiento (Behaviour Cloning). ", { bold: true }), run("Retomar la inicialización del agente mediante aprendizaje supervisado a partir de partidas humanas, depurando la canalización de logs a trayectorias y alineándola con la representación del estado. Un buen punto de partida supervisado suele acelerar y estabilizar el refuerzo posterior.")]));
children.push(bullet([run("Mejorar el agente. ", { bold: true }), run("Entrenar durante más pasos y, preferiblemente, con aceleración por GPU; ajustar hiperparámetros; ampliar y refinar la observación; y profundizar en el self-play poblacional (al estilo de fictitious play o double oracle) para obtener políticas más robustas.")]));
children.push(bullet([run("Entrenamiento frente a equipos diversos. ", { bold: true }), run("Aprovechar el soporte de carpetas de equipos para entrenar al agente contra una amplia variedad de equipos del formato, con el objetivo de obtener una política que generalice bien y que, idealmente, pudiera especializarse o evaluarse frente a equipos concretos del metajuego.")]));
children.push(bullet([run("Evaluación más exhaustiva. ", { bold: true }), run("Ampliar el número de combates por evaluación, incorporar intervalos de confianza y, en su caso, medir el rendimiento en la escalera del servidor oficial respetando sus normas.")]));

// ================= 8. ANEXOS =================
children.push(H1("8. Anexos"));
children.push(P("Por su naturaleza y extensión, parte del material generado se entrega como anexos y no se reproduce íntegramente en el cuerpo de la memoria. A continuación se describe brevemente su contenido, organizado en las tres categorías habituales del área de programación."));
children.push(H2("8.1. Documentación del código"));
children.push(bullet([run("Componentes. ", { bold: true }), run("Diagrama de componentes en notación UML 2 que muestra los módulos del software (entornos de singles y dobles, envoltorio de agente, representación del estado, políticas, utilidades de equipos y de evaluación) y sus dependencias. [Insertar el diagrama en el anexo correspondiente.]")]));
children.push(bullet([run("Bibliotecas de terceros. ", { bold: true }), run("Relación de bibliotecas empleadas (poke-env, Stable-Baselines3, sb3-contrib, PyTorch, Gymnasium, TensorBoard), su función y los motivos de su elección, con enlaces a sus fuentes y documentación.")]));
children.push(bullet([run("Clases. ", { bold: true }), run("Diagrama de clases en notación UML 2 con la estructura del código (entornos, extractores de características y utilidades).")]));
children.push(bullet([run("Requisitos y estructura del proyecto. ", { bold: true }), run("Software necesario para abrir, compilar y ejecutar el proyecto (Python y sus dependencias fijadas, Node.js y el servidor de Showdown), e instrucciones de instalación y configuración, junto con la descripción de la organización de carpetas.")]));
children.push(H2("8.2. Manual de usuario"));
children.push(P("Indicaciones para instalar y ejecutar el software: arranque del servidor local, activación del entorno virtual, lanzamiento de un entrenamiento, juego del agente frente a un humano desde el cliente web y enfrentamiento entre modelos. Se entrega como documento independiente."));
children.push(H2("8.3. Archivos del proyecto"));
children.push(P("Código fuente completo (propio y de terceros) necesario para compilar y ejecutar el proyecto, excluyendo archivos temporales; documentación extraída de las fuentes cuando proceda; y los modelos entrenados y la configuración del servidor adaptado. Cada archivo de código propio incluye una cabecera con la autoría correspondiente."));

// ================= 9. REFERENCIAS =================
children.push(H1("9. Referencias y bibliografía"));
children.push(P("Las referencias se presentan siguiendo la normativa APA (7ª edición). Todas ellas están citadas en el texto."));
const refs = [
  "Angliss, C. (2026). VGC-Bench: Benchmark y herramientas para el aprendizaje por refuerzo en Pokémon VGC [software]. GitHub. https://github.com/cameronangliss/vgc-bench",
  "Bain, M., & Sammut, C. (1995). A framework for behavioural cloning. En K. Furukawa, D. Michie & S. Muggleton (Eds.), Machine Intelligence 15 (pp. 103–129). Oxford University Press.",
  "Berner, C., Brockman, G., Chan, B., Cheung, V., Dębiak, P., Dennison, C., … Zhang, S. (2019). Dota 2 with large scale deep reinforcement learning. arXiv. https://arxiv.org/abs/1912.06680",
  "Huang, S., & Ontañón, S. (2022). A closer look at invalid action masking in policy gradient algorithms. En Proceedings of the 35th International FLAIRS Conference. https://doi.org/10.32473/flairs.v35i.130584",
  "Mnih, V., Kavukcuoglu, K., Silver, D., Rusu, A. A., Veness, J., Bellemare, M. G., … Hassabis, D. (2015). Human-level control through deep reinforcement learning. Nature, 518(7540), 529–533. https://doi.org/10.1038/nature14236",
  "Raffin, A., Hill, A., Gleave, A., Kanervisto, A., Ernestus, M., & Dormann, N. (2021). Stable-Baselines3: Reliable reinforcement learning implementations. Journal of Machine Learning Research, 22(268), 1–8.",
  "Sahovic, H. (2024). poke-env: A Python interface for training reinforcement learning Pokémon bots [software]. GitHub. https://github.com/hsahovic/poke-env",
  "Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017). Proximal policy optimization algorithms. arXiv. https://arxiv.org/abs/1707.06347",
  "Silver, D., Huang, A., Maddison, C. J., Guez, A., Sifre, L., van den Driessche, G., … Hassabis, D. (2016). Mastering the game of Go with deep neural networks and tree search. Nature, 529(7587), 484–489. https://doi.org/10.1038/nature16961",
  "Silver, D., Hubert, T., Schrittwieser, J., Antonoglou, I., Lai, M., Guez, A., … Hassabis, D. (2018). A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play. Science, 362(6419), 1140–1144. https://doi.org/10.1126/science.aar6404",
  "Sutton, R. S., & Barto, A. G. (2018). Reinforcement learning: An introduction (2ª ed.). MIT Press.",
  "Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., … Polosukhin, I. (2017). Attention is all you need. En Advances in Neural Information Processing Systems 30 (pp. 5998–6008).",
  "Vinyals, O., Babuschkin, I., Czarnecki, W. M., Mathieu, M., Dudzik, A., Chung, J., … Silver, D. (2019). Grandmaster level in StarCraft II using multi-agent reinforcement learning. Nature, 575(7782), 350–354. https://doi.org/10.1038/s41586-019-1724-z",
];
refs.forEach(r => children.push(new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 120, line: 276 },
  indent: { left: 720, hanging: 720 },
  children: [new TextRun({ text: r })] })));

// ---------- Document ----------
const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: FONT, color: "1F4E79" },
        paragraph: { spacing: { before: 320, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: "2E74B5" },
        paragraph: { spacing: { before: 220, after: 140 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: FONT, color: "2E74B5" },
        paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "vi", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  sections: [{
    properties: { page: {
      size: { width: 11906, height: 16838 }, // A4
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
    } },
    footers: { default: new Footer({ children: [ new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [ new TextRun({ children: [PageNumber.CURRENT], size: 18 }) ] }) ] }) },
    children,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("Memoria_TFG_David_Diaz.docx", buffer);
  console.log("OK Memoria_TFG_David_Diaz.docx generada");
});
