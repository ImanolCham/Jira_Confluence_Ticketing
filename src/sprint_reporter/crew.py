from crewai import Agent, Crew, Process, Task
from .tools import query_jira_tasks, publish_confluence_page
import os

# Agentes
jira_extractor = Agent(
    role="Jira Data Extractor",
    goal="Extraer todas las tareas cerradas de la iteración especificada con detalles completos",
    backstory="""Eres un experto en Jira que conoce JQL avanzado. Extraes datos precisos sobre "
                "tareas completadas, sus descripciones, dependencias y epics relacionados.""",
    tools=[query_jira_tasks],
    verbose=True,
    allow_delegation=False
)

sprint_analyzer = Agent(
    role="Sprint Retrospective Analyst",
    goal="Analizar tareas completadas para generar un resumen ejecutivo con impactos y dependencias",
    backstory="""Eres un analista ágil senior. Identificas patrones, qué se entregó, áreas afectadas, "
                "dependencias bloqueantes resueltas y lecciones aprendidas.""",
    verbose=True,
    allow_delegation=False
)

confluence_publisher = Agent(
    role="Confluence Technical Writer",
    goal="Formatear el análisis en una página Confluence profesional y publicarla",
    backstory="""Eres un redactor técnico experto en Confluence y markdown. Creas páginas claras "
                "con tablas, headings y resúmenes accionables.""",
    tools=[publish_confluence_page],
    verbose=True,
    allow_delegation=False
)

# Tareas
extract_task = Task(
    description="Extrae las tareas cerradas del sprint {sprint_id} usando la herramienta Jira.",
    expected_output="Lista detallada de todas las tareas cerradas con summaries, dependencias y epics.",
    agent=jira_extractor
)

analyze_task = Task(
    description="""Analiza los datos extraídos:
    - Qué se ha completado (agrupa por tipo/epic).
    - Impactos: qué áreas/productos afecta.
    - Dependencias: links resueltos o pendientes.
    - Métricas: total tareas, tiempo estimado vs real si disponible.
    - Resumen ejecutivo y recomendaciones.""",
    expected_output="Reporte estructurado en markdown listo para Confluence.",
    agent=sprint_analyzer,
    context=[extract_task]
)

publish_task = Task(
    description="""Publica el análisis en Confluence:
    - Space: {space_key}
    - Title: Resumen Sprint {sprint_id} - Cerradas
    - Body: Usa headings, tablas para tareas/dependencias, colores si posible.""",
    expected_output="Confirmación de página creada/actualizada con URL.",
    agent=confluence_publisher,
    context=[analyze_task]
)

# Crew
sprint_crew = Crew(
    agents=[jira_extractor, sprint_analyzer, confluence_publisher],
    tasks=[extract_task, analyze_task, publish_task],
    process=Process.sequential,
    verbose=2,
    memory=True
)
