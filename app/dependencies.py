from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
import os
from dotenv import load_dotenv

load_dotenv()
# Gemini reads key from environment variable
model = GeminiModel("gemini-1.5-flash")
agent = Agent(model)




