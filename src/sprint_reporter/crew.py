from crewai import Agent, Crew, Process, Task
from .tools import query_jira_tasks, publish_confluence_page
import os

# Agentes
jira_extractor = Agent(
    role="Jira Data Extractor",
    goal="Extraer tasks cerradas Sprint {sprint_id} con query_jira_tasks.run(sprintid='{sprint_id}')",
    backstory="""Experto JQL. SIEMPRE usa tool query_jira_tasks(sprintid='{sprint_id}'); no asumas datos ni memory.""",
    tools=[query_jira_tasks],
    verbose=False,  # Reduce memory bias
    allow_delegation=False
)

sprint_analyzer = Agent(
    role="Sprint Retrospective Analyst",
    goal="Analizar tasks de {sprint_id} para resumen ejecutivo",
    backstory="""Analista ágil senior. Usa datos de Jira extractor para métricas, patrones, impactos.""",
    verbose=False,
    allow_delegation=False
)

confluence_publisher = Agent(
    role="Confluence Technical Writer",
    goal="Publicar análisis Sprint {sprint_id} en {space_key}",
    backstory="""Redactor Confluence. Formatea markdown con tablas/URL de página publicada.""",
    tools=[publish_confluence_page],
    verbose=True,
    allow_delegation=False
)

# Tareas - Explícitas
extract_task = Task(
    description="""Ejecuta EXACTO: query_jira_tasks.run(sprintid='{sprint_id}')
Output esperado: SCRUM-1: Tarea 1\nSCRUM-2: Tarea 2\n... (4 tasks)""",
    expected_output="Lista tasks: key: summary, dependencias (ej SCRUM-1: Tarea 1, Ninguna).",
    agent=jira_extractor,
    context=[]  # Sin contexto, fuerza tool
)

analyze_task = Task(
    description="""Analiza output extract_task:
- Total: 4 tasks completadas Sprint {sprint_id}
- Agrupar: tipos/epics
- Dependencias/métricas
- Recomendaciones""",
    expected_output="Markdown: # Resumen Sprint {sprint_id}\n## Métricas\n| Task | Summary |\n... \n## Insights...",
    agent=sprint_analyzer,
    context=[extract_task]
)

publish_task = Task(
    description="""Llama publish_confluence_page(space_key='{space_key}', title='Resumen Sprint {sprint_id} - Cerradas', body=analyze_task.output)""",
    expected_output="URL página creada: https.../pages/...",
    agent=confluence_publisher,
    context=[analyze_task]
)

# Crew
sprint_crew = Crew(
    agents=[jira_extractor, sprint_analyzer, confluence_publisher],
    tasks=[extract_task, analyze_task, publish_task],
    process=Process.sequential,
    verbose=1,
    memory=False  # Fuerza tools frescos
)
