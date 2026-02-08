import os
import sys
sys.path.insert(0, 'src')
from dotenv import load_dotenv
load_dotenv()

from sprint_reporter.tools import query_jira_tasks

print("Testing Jira tool...")
result = query_jira_tasks.run(sprint_id="2")
print(result)