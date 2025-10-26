from pydantic_ai import Agent
# from pydantic_ai.models.gemini import GeminiModel
import openai
import os
from dotenv import load_dotenv
import subprocess
from pymongo import MongoClient
from app.vector_store import retrieve_relevant_docs
from PyPDF2 import PdfReader
from fastapi import FastAPI, WebSocket
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

# MongoDB setup
client = MongoClient("mongodb+srv://sneha_db_user:Sneha_9841@cluster0.dadlcej.mongodb.net/?retryWrites=true&w=majority")

faq_db = client["testdb"]
business_db = client["bussiness_db"]

    
def run_mongo_query(db_name: str = "testdb", collection_name: str = "faq_vector_store", query: dict = {}) -> str:
    
    try:
        
        target_db = client[db_name]
        coll = target_db[collection_name]

        new_query = {}
        for key, value in query.items():
            if isinstance(value, str):
                new_query[key] = {"$regex": f"^{value}$", "$options": "i"}
            else:
                new_query[key] = value

        result = list(coll.find(new_query, {"_id": 0}))

        if not result:
            return f"No records found in '{collection_name}' for {new_query}"
        return f"Found {len(result)} records: {result}"

    except Exception as e:
        return f"MongoDB error: {str(e)}"

def rag_query(question: str) -> str:
    docs = retrieve_relevant_docs(question)
    if not docs:
        return "No relevant FAQs found."
    context = "\n\n".join(docs)
    return f"Question: {question}\n\nContext from FAQs:\n{context}"
    
system_prompt = """
You are a friendly and intelligent company support AI assistant. Your job is to decide which tool to call based on the *meaning* of the user's question (not only exact words or casing), then call that tool with an appropriate, normalized query.
   Rules:
   a. There are two databases: 'testdb'(which has only one collection 'faq_vector_store') and 'business_db'(which has four collections: 'sales', 'products','employees'and 'tasks').
   b. If the question is about company info, policies, or general FAQs → first select 'faq_vector_store' as the collection_name from 'testdb' and then use rag_query tool on 'testdb'.
   2. If it's about business data or think of it as all the data involved in business analyst process(such as everything relating to product, stock, sales, employees,customers revenue, etc.) then first among the four collections you have to choose one of them and then use 'run_mongo_query' on the 'business_db'. 
       - Choose the correct collection_name based on user's query(and dont just see the word try to understand the meaning): 
             - "products" → price, stock, category, inventory and everything related to products
             - "sales" → revenue, total sales, transactions,revenue, total sales and every detail records involved in sale of a product including customers
             - "employees" → employee details, attendance, salary, roles 
             - "tasks" → pending tasks, assignments,status, and whatever that describes or relates to tasks
             - Example: If user asks "What is the price of jeans(or any product)?", query 'business_db.products' for price info.
   3. For greetings or small talk (hi, hello, how are you) → reply conversationally. 
   4. Never ask the user for database code or collection names — infer intelligently. 
   5. Respond naturally and concisely with helpful details.
Think carefully before choosing the right tool
"""


# Registering  the tool with the agent

model = "gpt-3.5-turbo"

agent = Agent(model, tools=[ run_mongo_query,  rag_query], system_prompt = system_prompt)


