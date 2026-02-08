import os
from crewai.tools import tool
from atlassian import Jira
import base64
import requests
import json

@tool("Query Jira Closed Tasks")
def query_jira_tasks(sprint_id: str) -> str:
    """Extrae tasks cerradas del sprint en SCRUM usando JQL exacta."""
    
    jira_url = os.getenv("JIRA_BASE_URL")
    user = os.getenv("JIRA_USER")
    token = os.getenv("JIRA_TOKEN")
    
    jira = Jira(url=jira_url, username=user, password=token, cloud=True)
    
    jql = f'project="SCRUM" AND status = Done AND statusCategory = Done AND Sprint = {sprint_id} ORDER BY created DESC'
    print(f"DEBUG JQL: {jql}")
    
    # CORRECTO: Solo JQL - devuelve dict con 'issues'
    data = jira.jql(jql)
    issues = data.get('issues', [])
    
    print(f"DEBUG: {len(issues)} issues encontradas")
    
    tasks = []
    for issue in issues:
        key = issue['key']
        summary = issue['fields'].get('summary', 'Sin summary')
        links = []
        issuelinks = issue['fields'].get('issuelinks', [])
        for link in issuelinks:
            if 'outwardIssue' in link and link['outwardIssue']:
                links.append(link['outwardIssue']['key'])
            elif 'inwardIssue' in link and link['inwardIssue']:
                links.append(link['inwardIssue']['key'])
        tasks.append(f"{key}: {summary}\nDependencias: {', '.join(links) if links else 'Ninguna'}")
    
    return "\n\n".join(tasks) or f"No tasks en sprint {sprint_id}"


@tool("Publish to Confluence")
def publish_confluence_page(space_key: str, title: str, body: str) -> str:
    """Crea o actualiza página en Confluence usando REST API."""
    url = f"{os.getenv('CONFLUENCE_URL', 'https://ichamorroarias.atlassian.net/wiki')}/rest/api/content"
    user = os.getenv("JIRA_USER")  # Reusa para Atlassian
    token = os.getenv("JIRA_TOKEN")
    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    
    # Busca página existente
    search_url = f"{url}/search?cql=space='{space_key}' AND title='{title}'"
    r = requests.get(search_url, headers=headers)
    results = r.json().get('results', [])
    
    if results:
        page_id = results[0]['id']
        # Obtiene versión para update
        page_info = requests.get(f"{url}/{page_id}?expand=version,body.storage", headers=headers).json()
        version = page_info['version']['number'] + 1
        data = {
            "id": page_id,
            "type": "page",
            "title": title,
            "body": {"storage": {"value": body, "representation": "storage"}},
            "version": {"number": version}
        }
        requests.put(f"{url}/{page_id}", json=data, headers=headers)
        return f"✅ ACTUALIZADA: https://ichamorroarias.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}"
    else:
        # Crea nueva
        data = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {"storage": {"value": body, "representation": "storage"}}
        }
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 201:
            page_id = r.json()['id']
            return f"✅ CREADA: https://ichamorroarias.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}"
        else:
            return f"❌ Error: {r.text}"
