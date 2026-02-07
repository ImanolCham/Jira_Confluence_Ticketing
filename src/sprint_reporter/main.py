from crew import sprint_crew
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    result = sprint_crew.kickoff(
        inputs={
            "sprint_id": os.getenv("SPRINT_ID", "Sprint 15"),  # Añade SPRINT_ID a .env
            "space_key": os.getenv("CONFLUENCE_SPACE", "DEV")   # Añade CONFLUENCE_SPACE a .env
        }
    )
    print("Resultado:", result)
