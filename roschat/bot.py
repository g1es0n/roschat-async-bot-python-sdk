import socketio
import json
import sys
import aiohttp
import asyncio
from .constants import START_BOT, SEND_BOT_MESSAGE, BOT_MESSAGE_RECEIVED, BOT_MESSAGE_WATCHED, SEND_BOT_MESSAGE, SEND_BOT_MESSAGE, DELETE_BOT_MESSAGE, SET_BOT_KEYBOARD


# sio = socketio.AsyncClient(ssl_verify=False, logger=True, engineio_logger=True)
sio = socketio.AsyncClient(ssl_verify=False)

@sio.event
async def disconnect():
    print("Socket соединение разорвано")

async def cb_start_bot(res):
    if 'error' in res:
        print('Ошибка при инициализации: ', res)
        await sio.disconnect()
    else:
        print('Бот успешно инициализирован')

def cb_send_message(res):
    if not res.get('id'):
        print('Не удался отправить сообщение: ', res)

class Roschat_Bot:
    def __init__(self, token, base_url, bot_name, socket_options={'query': 'type-bot', 'rejectUnauthorized': 'false'}):
        self.token = token
        self.base_url = base_url
        self.bot_name = bot_name
        self.socket_options = socket_options
    

    async def start(self, on_start):
        self.on_start = on_start
        server_url = self.base_url + '/ajax/config.json'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(server_url, ssl=False) as r:
                    text = await r.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(e)
            sys.exit(1)
        server_config = json.loads(text)
        web_sockets_port = server_config.get('webSocketsPortVer4')
        socket_url = str(self.base_url) + ':' + str(web_sockets_port)
        try:
            sio.on('connect', self.on_connected)
            await sio.connect(socket_url, headers=self.socket_options)
        
        except ValueError:
            print(ValueError)

        
    async def on_connected(self):
        print("Соединился с socket сервером...")

        await asyncio.sleep(2)

        print("Стартую бота...")
        
        await self.start_bot()


    async def start_bot(self):
        await sio.emit(
            START_BOT, 
            {
                'token': self.token,
                'bot_name': self.bot_name
            }, 
            callback=self.on_start
        )
    

    def on(self, event_name, callback):
        sio.on(event_name, handler=callback)

    async def emit(self, event_name, data, callback=None):
        await sio.emit(event_name, data=data, callback=callback)
    
    async def send_message(self, params, data, callback=cb_send_message):
        if not params:
            print('Для отправки сообщения необходим, как минимум cid пользователя')
        if type(params) is int:
            cid = params
            params = {
                'cid': cid,
                'data': data
            }
        elif type(params) is dict:
            if not params.get('cid'):
                print('Для отправки сообщения необходим cid пользователя')
                return
        params['data'] = data if isinstance(data, str) else json.dumps(data)
        await sio.emit(SEND_BOT_MESSAGE, data=params, callback=callback)
    
    async def send_message_recieved(self, msg_id, callback=None):
        if not msg_id:
            print('Обязательный параметр msg_id не предоставлен')
            return
        await sio.emit(BOT_MESSAGE_RECEIVED, data={'id': msg_id}, callback=callback)
    
    async def send_message_watched(self, msg_id, callback=None):
        if not msg_id:
            print('Обязательный параметр msg_id не предоставлен')
            return
        await sio.emit(BOT_MESSAGE_WATCHED, data={'id': msg_id}, callback=callback)
    
    async def delete_bot_message(self, msg_id, callback=None):
        if not msg_id:
            print('Обязательный параметр msg_id не предоставлен')
            return 
        await sio.emit(DELETE_BOT_MESSAGE, data={'id': msg_id}, callback=callback)

    async def set_bot_keyboard(self, data):
        if not data.get('cid'):
            print('Обязательное поле cid не предоставлено')
            return
        await sio.emit(SET_BOT_KEYBOARD, data=data)
    