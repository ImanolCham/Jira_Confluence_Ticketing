import os
from crewai_tools import tool
from atlassian import Jira, Confluence

@tool("Query Jira Closed Tasks")
def query_jira_tasks(sprint_id: str) -> str:
    """Extrae tareas cerradas de un sprint en Jira con detalles de dependencias."""
    jira = Jira(
        url=os.getenv("JIRA_BASE_URL"),
        username=os.getenv("JIRA_USER"),
        password=os.getenv("JIRA_TOKEN")
    )
    jql = f'sprint="{sprint_id}" AND status in (Done, "Done", Closed) ORDER BY updated DESC'
    issues = jira.issue_search(jql, max_results=50)
    tasks = []
    for issue in issues.get('issues', []):
        key = issue['key']
        summary = issue['fields']['summary']
        links = [link['destination']['key'] for link in issue['fields'].get('issuelinks', []) if 'destination' in link]
        epic = issue['fields'].get('customfield_10010', 'N/A')  # Ajusta customfield para epic
        tasks.append(f"{key}: {summary}\nDependencias/Impactos: {', '.join(links) or 'Ninguna'}\nEpic: {epic}")
    return "\n\n".join(tasks) or "No hay tareas cerradas."

@tool("Publish to Confluence")
def publish_confluence_page(space_key: str, title: str, body: str) -> str:
    """Crea o actualiza página en Confluence con el resumen del sprint."""
    conf = Confluence(
        url=os.getenv("CONFLUENCE_URL"),
        username=os.getenv("CONFLUENCE_USER"),
        password=os.getenv("CONFLUENCE_TOKEN")
    )
    page_id = conf.get_page_id(space_key, title)  # Busca si existe
    if page_id:
        conf.update_page(page_id, title, body)
        return f"Página actualizada: {title} (ID: {page_id})"
    else:
        conf.create_page(space=space_key, title=title, body=body)
        return f"Página creada: {title}"
