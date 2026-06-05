from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [추가] HTML 화면을 서버가 직접 제공 ---

@app.get("/driver", response_class=HTMLResponse)
def get_driver_page():
    # 이전에 만든 기사님용 HTML 코드 파일(index.html) 내용을 읽어서 반환
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/viewer", response_class=HTMLResponse)
def get_viewer_page():
    # 이전에 만든 학생용 HTML 코드 파일(viewer.html) 내용을 읽어서 반환
    with open("viewer.html", "r", encoding="utf-8") as f:
        return f.read()

# --- 기존 웹소켓 로직 유지 ---

class ViewerManager:
    def __init__(self):
        self.active_viewers = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_viewers.append(websocket)
        print(f"👥 [학생 접속] 현재 대기 중인 학생 수: {len(self.active_viewers)}명")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_viewers:
            self.active_viewers.remove(websocket)
            print(f"👥 [학생 퇴장] 현재 대기 중인 학생 수: {len(self.active_viewers)}명")

    async def broadcast_bus_location(self, message: str):
        for connection in self.active_viewers:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ViewerManager()

@app.websocket("/ws/bus")
async def websocket_bus(websocket: WebSocket):
    await websocket.accept()
    print("🚌 [기사님 연결 완료]")
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_bus_location(data)
    except WebSocketDisconnect:
        print("🛑 [기사님 연결 종료]")

@app.websocket("/ws/viewer")
async def websocket_viewer(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)