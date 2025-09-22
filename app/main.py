from fastapi import FastAPI, WebSocket
from app.dependencies import agent
from fastapi.responses import HTMLResponse
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
        <h1>WebSocket Chat</h1>
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
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                console.log(input.value)
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
            data = await websocket.receive_text()
            print("Received from client:", data)
            try:
                result = await agent.run(data)
                print("AI response:", getattr(result, 'data', result))
                await websocket.send_text(getattr(result, 'data', str(result)))
            except Exception as agent_exc:
                print("Agent error:", agent_exc)
                await websocket.send_text(f"Agent error: {agent_exc}")
        except Exception as e:
            
            print("WebSocket error:", e)
            traceback.print_exc()
            await websocket.close()
            break

    
