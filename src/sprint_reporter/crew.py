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
    goal="Analizar PROFUNDAMENTE CADA TAREA: objetivo, evolución comments timeline, resolución detallada, impacto, lecciones.",
    backstory="""
Analista SCRUM senior experto. Para CADA TAREA del reporte Jira:

1. **OBJETIVO**: Problema resuelto, impacto negocio/usuario.
2. **EVOLUCIÓN**: Timeline comments completa → avances, problemas, quién hizo qué.
3. **RESOLUCIÓN**: Cómo se cerró, calidad (tests? debt?), assignee contribuciones.
4. **IMPACTO/VALOR**: Qué beneficio entrega, dependencias resueltas.
5. **LECCIONES**: Patrones repetidos, mejoras proceso.

Formato EXACTO por tarea:
### Análisis [KEY]: [Summary]
**Objetivo e Impacto**: ...
**Evolución Timeline**: 
- [Fecha] [Autor]: ...
**Resolución y Calidad**: ...
**Lecciones**: ...

Final: ## Resumen Global + Recomendaciones.
""",
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
    description="""Analiza PROFUNDAMENTE CADA TAREA de extract_task.output (reporte detallado):

**Por TAREA individual** (usa TODO: objetivo completo, comments timeline, assignee, fechas, subtareas, deps):
- Objetivo → problema + impacto negocio
- Timeline comments → evolución completa (bloqueos? avances?)
- Resolución → calidad cierre
- Lecciones específicas

**Sigue formato backstory EXACTO**. 

Final: Tabla métricas global + recomendaciones accionables.""",
    expected_output="Análisis detallado TAREA POR TAREA markdown + tabla resumen + recomendaciones.",
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
