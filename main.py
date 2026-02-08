#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from src.sprint_reporter.crew import sprint_crew
from src.sprint_reporter.tools import query_jira_tasks

if __name__ == "__main__":
    sprint_id = os.getenv("SPRINTID", "2")
    space_key = os.getenv("CONFLUENCESPACE", "SPRINTREP")
    
    # Test tool CORRECTO: posicional, no kwarg
    print("Test tool:", query_jira_tasks.run(sprint_id))  # sprint_id directo
    
    result = sprint_crew.kickoff(inputs={
        "sprint_id": sprint_id,
        "space_key": space_key
    })
    print("Crew resultado:", result)
