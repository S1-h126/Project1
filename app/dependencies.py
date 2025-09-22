from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

model = GeminiModel("gemini-1.5-flash")
agent = Agent(model)


def run_command(command: str) -> str:
    
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"Execution error: {str(e)}"

# Registering  the tool with the agent

agent = Agent(model, tools=[run_command])


