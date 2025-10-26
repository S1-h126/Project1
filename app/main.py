from fastapi import FastAPI, WebSocket
from app.dependencies import agent
from fastapi.responses import HTMLResponse
from app.vector_store import retrieve_relevant_docs
import traceback
import asyncio

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>Company Support Agent</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                message.innerHTML = "<span class='agent'>Agent:</span> " + event.data
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                var messages = document.getElementById("messages")

                var userMsg = document.createElement('li')
                userMsg.innerHTML = "<span class='user'>You:</span> " + input.value
                messages.appendChild(userMsg)

                
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)
    
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            question = await websocket.receive_text()
            print("User asked:", question)

            # ⚙️ Send raw question directly to the agent
            result = await agent.run(question)
            answer = getattr(result, "output", str(result))
            formatted_answer = answer.replace("\n", "<br>")

            print("Agent replied:", answer)
            await websocket.send_text(formatted_answer)

        except Exception as e:
            print("Agent error:", e)
            traceback.print_exc()
            await websocket.send_text(f"Agent error: {e}")
            break

    
