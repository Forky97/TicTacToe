

from typing import List
from fastapi import FastAPI, WebSocket, status
from starlette.websockets import WebSocketDisconnect
import json


app = FastAPI()


def init_board():
    # create empty board
    return [
        None, None, None,
        None, None, None,
        None, None, None,
    ]


board = init_board()


def is_draw():
    # checks if a draw
    global board
    for cell in board:
        if not cell:
            return False
    board = init_board()
    return True


def if_won():
    # check if some player has just won the game
    global board
    if board[0] == board[1] == board[2] != None or \
            board[3] == board[4] == board[5] != None or \
            board[6] == board[7] == board[8] != None or \
            board[0] == board[3] == board[6] != None or \
            board[1] == board[4] == board[7] != None or \
            board[2] == board[5] == board[8] != None or \
            board[0] == board[4] == board[8] != None or \
            board[6] == board[4] == board[2] != None:
        board = init_board()
        return True
    return False


async def update_board(manager, data):
    ind = int(data['cell']) - 1
    data['init'] = False
    if not board[ind]:
        # cell is empty
        board[ind] = data['player']
        if is_draw():
            data['message'] = "draw"
        elif if_won():
            data['message'] = "won"
        else:
            data['message'] = "move"
    else:
        data['message'] = "choose another one"

    await manager.broadcast(data)

    if data['message'] in ['draw', 'won']:
        manager.connections = []


class ConnectionManager:
    ''' Создание менеджера для игры в крестики-нолики в 2 игрока '''
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        if len(self.connections) >= 2:
            await websocket.accept()
            await websocket.close(4000)
        else:
            await websocket.accept()
            self.connections.append(websocket)
            if len(self.connections) == 1:
                await websocket.send_json({
                    'init': True,
                    'player': 'X',
                    'message': 'Waiting for another player',
                })
            else:
                await websocket.send_json({
                    'init': True,
                    'player': 'O',
                    'message': 'Lets goo ' ,
                })
                await self.connections[0].send_json({
                    'init': True,
                    'player': 'X',
                    'message': 'Your turn!',
                })

    async def disconnect(self, websocket: WebSocket):
        ''' дисконект пользователя когда выходит из браузерам'''
        self.connections.remove(websocket)

    async def broadcast(self, data: str):
        # broadcasting data to all connected clients
        for connection in self.connections:
            await connection.send_json(data)


manager = ConnectionManager()


@app.websocket("/tictactoe")
async def websocket_endpoint(websocket: WebSocket):
    ''' Создание эндпоинта для вебсоетка,пока нет остоеденения , будет бесконечный цикл'''

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            await update_board(manager, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except:
        pass
