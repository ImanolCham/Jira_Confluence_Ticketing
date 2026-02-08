import os
import base64
import requests
from crewai.tools import tool
from atlassian import Jira

@tool("Query Jira Closed Tasks")
def query_jira_tasks(sprint_id: str) -> str:
    """Extrae INFO DETALLADA tarea por tarea del sprint: objetivo, comments timeline, resolución, subtareas, assignee, historia."""
    
    jira_url = os.getenv("JIRA_BASE_URL")
    user = os.getenv("JIRA_USER")
    token = os.getenv("JIRA_TOKEN")
    
    jira = Jira(url=jira_url, username=user, password=token, cloud=True)
    
    jql = f'project="SCRUM" AND status = Done AND statusCategory = Done AND Sprint = {sprint_id} ORDER BY created DESC'
    print(f"DEBUG JQL: {jql}")
    
    data = jira.jql(jql)
    issues = data.get('issues', [])
    
    print(f"DEBUG: {len(issues)} issues encontradas")
    
    tasks_info = []
    for issue in issues:
        key = issue['key']
        summary = issue['fields'].get('summary', 'Sin summary')
        
        # === INFO BASE ===
        status_raw = issue['fields'].get('status', {})
        status = status_raw.get('name', 'N/A') if status_raw else 'N/A'
        
        assignee_raw = issue['fields'].get('assignee')
        assignee = assignee_raw.get('displayName', 'No asignada') if assignee_raw else 'No asignada'
        
        created = issue['fields'].get('created', 'N/A')[:10]
        updated = issue['fields'].get('updated', 'N/A')[:10]
        
        # === OBJETIVO COMPLETO ===
        desc_raw = issue['fields'].get('description', '')
        if isinstance(desc_raw, dict) and desc_raw.get('text'):
            objetivo = desc_raw['text'].strip()
        else:
            objetivo = str(desc_raw).strip() if desc_raw else 'Sin descripción'
        
        # === RESOLUCIÓN ===
        resolucion_raw = issue['fields'].get('resolution')
        if resolucion_raw:
            resolucion = resolucion_raw.get('name', 'Sin resolución')
            resolucion_desc = resolucion_raw.get('description', '')[:150]
        else:
            resolucion = 'Sin resolución'
            resolucion_desc = ''
        
        # === COMMENTS: TIMELINE COMPLETA (FIX TOTAL body str/dict) ===
        comments_timeline = []
        comments_data = issue['fields'].get('comment', {})
        all_comments = comments_data.get('comments', [])
        for i, c in enumerate(all_comments, 1):
            author_raw = c.get('author', {})
            author = author_raw.get('displayName', 'Anónimo') if author_raw else 'Anónimo'
            created_c = c.get('created', 'N/A')[:16]
            
            # FIX: body maneja str O dict → siempre texto seguro
            body_raw = c.get('body', '')
            if isinstance(body_raw, dict) and body_raw.get('text'):
                body = body_raw['text'][:200].strip()
            else:
                body = str(body_raw)[:200].strip()
            
            comments_timeline.append(f"{i}. [{created_c}] {author}: {body}")
        comments_full = '\n'.join(comments_timeline) if comments_timeline else 'Sin comentarios'
        
        # === SUBTAREAS ===
        subtareas = 'Sin subtareas detectadas'
        issuelinks = issue['fields'].get('issuelinks', [])
        for link in issuelinks:
            link_type = link.get('type', {}).get('name', '')
            if 'sub-task' in link_type.lower():
                if 'outwardIssue' in link and link['outwardIssue']:
                    subtareas = f"Subtarea: {link['outwardIssue']['key']}"
                    break
                elif 'inwardIssue' in link and link['inwardIssue']:
                    subtareas = f"Subtarea: {link['inwardIssue']['key']}"
                    break
        
        # === DEPENDENCIAS ===
        links = []
        for link in issuelinks:
            if 'outwardIssue' in link and link['outwardIssue']:
                links.append(f"→ {link['outwardIssue']['key']}")
            elif 'inwardIssue' in link and link['inwardIssue']:
                links.append(f"← {link['inwardIssue']['key']}")
        deps = '\n'.join(links) if links else 'Sin dependencias'
        
        # === BLOQUE TAREA ===
        task_detail = f"""
### {key}: {summary}

**Estado**: {status} | **Asignado**: {assignee} | **Creada**: {created} | **Actualizada**: {updated}

**OBJETIVO COMPLETO**:
{objetivo}

**RESOLUCIÓN**:
{resolucion}
{resolucion_desc}

**TIMELINE COMMENTS** (completa):
{comments_full}

**SUBTAREAS**:
{subtareas}

**DEPENDENCIAS**:
{deps}

---
        """
        tasks_info.append(task_detail.strip())
    
    if not tasks_info:
        return f"No tasks cerradas en sprint {sprint_id}"
    
    titulo = f"## REPORTE DETALLADO: Sprint {sprint_id} - {len(tasks_info)} Tasks Cerradas\n\n"
    output = titulo + ''.join(tasks_info)
    
    print(f"DEBUG Preview: {output[:800]}...")
    return output


@tool("Publish to Confluence")
def publish_confluence_page(space_key: str, title: str, body: str) -> str:
    """Publica en Confluence (idéntico)."""
    url = f"{os.getenv('CONFLUENCE_URL', 'https://ichamorroarias.atlassian.net/wiki')}/rest/api/content"
    user = os.getenv("JIRA_USER")
    token = os.getenv("JIRA_TOKEN")
    auth = base64.b64encode(f"{user}:{token}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    
    search_url = f"{url}/search?cql=space='{space_key}' AND title='{title}'"
    r = requests.get(search_url, headers=headers)
    results = r.json().get('results', [])
    
    if results:
        page_id = results[0]['id']
        page_info = requests.get(f"{url}/{page_id}?expand=version,body.storage", headers=headers).json()
        version = page_info['version']['number'] + 1
        data = {
            "id": page_id, "type": "page", "title": title,
            "body": {"storage": {"value": body, "representation": "storage"}},
            "version": {"number": version}
        }
        requests.put(f"{url}/{page_id}", json=data, headers=headers)
        return f"✅ ACTUALIZADA: https://ichamorroarias.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}"
    else:
        data = {
            "type": "page", "title": title, "space": {"key": space_key},
            "body": {"storage": {"value": body, "representation": "storage"}}
        }
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 201:
            page_id = r.json()['id']
            return f"✅ CREADA: https://ichamorroarias.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}"
        else:
            return f"❌ Error: {r.text}"
