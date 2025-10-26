import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from docx import Document
from PyPDF2 import PdfReader

client = MongoClient("mongodb+srv://sneha_db_user:Sneha_9841@cluster0.dadlcej.mongodb.net/?retryWrites=true&w=majority")
faq_db = client["testdb"]
faq_collections = faq_db["faq_vector_store"]

model =  SentenceTransformer("all-MiniLM-L6-v2")


def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = f"Unsupported file format: {ext}. Only PDF, DOCX, and TXT files are supported."
    return text

def chunk_text(text, max_length=500, overlap=100):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] + " " + sentence
        else:
            current_chunk += " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def load_faqs(folder_path = "faqs"):
    print(f"Loading files from: {os.path.abspath(folder_path)}")
    for filename in os.listdir(folder_path):
       path = os.path.join(folder_path, filename)
       text = extract_text(path)
       if not text:
          print(f"Skipped empty file: {filename}")
          continue
       
       chunks = chunk_text(text, max_length=500, overlap=100)
       for i, chunk in enumerate(chunks):
         embedding = model.encode(chunk).tolist()
         doc = {
                "source": filename,
                "chunk_id": i,
                "text": chunk,
                "embedding": embedding
            }
         faq_collections.insert_one(doc) 
         print(f"Inserted chunk {i} from {filename}")

def retrieve_relevant_docs(query, limit=3):
    query_vector = model.encode(query).tolist()
    pipeline = [
        {"$vectorSearch": {
            "queryVector": query_vector,
            "index": "faq_vector_index",
            "path": "embedding",
            "numCandidates": 100,
            "limit": limit
        }},
        {"$project": {"text": 1, "_id": 0}}
    ]
    results = list(faq_collections.aggregate(pipeline))
    return [r["text"] for r in results]
