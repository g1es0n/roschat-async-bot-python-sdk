import socketio
import json
import aiohttp
import asyncio
import inspect
from .constants import START_BOT, SEND_BOT_MESSAGE, BOT_MESSAGE_RECEIVED, BOT_MESSAGE_WATCHED, DELETE_BOT_MESSAGE, SET_BOT_KEYBOARD


# sio = socketio.AsyncClient(ssl_verify=False, logger=True, engineio_logger=True)
sio = socketio.AsyncClient(ssl_verify=False)

AUTH_TIMEOUT = 30
AUTH_DELAY_MIN = 2 
AUTH_DELAY_MAX = 60

CONFIG_TIMEOUT = 30
CONNECT_DELAY_MIN = 2
CONNECT_DELAY_MAX = 60

@sio.event
async def disconnect():
    print("Socket соединение разорвано")

def cb_start_bot(res):
    if not isinstance(res, dict) or res.get('error'):
        print('Ошибка при инициализации: ', res)
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
        self.auth_task = None
        self.authorized = False
    

    async def start(self, on_start=cb_start_bot):
        self.on_start = on_start
        if sio.connected:
            print('Бот уже подключён к серверу')
            return

        sio.on('connect', self.on_connected)
        delay = CONNECT_DELAY_MIN
        while True:
            try:
                socket_url = await self.get_socket_url()
                await sio.connect(socket_url, headers=self.socket_options)
                return
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, socketio.exceptions.ConnectionError) as e:
                print('Не удалось подключиться к серверу, повтор через', delay, 'сек: ', repr(e))
            await asyncio.sleep(delay)
            delay = min(delay * 2, CONNECT_DELAY_MAX)


    async def get_socket_url(self):
        server_url = self.base_url + '/ajax/config.json'
        timeout = aiohttp.ClientTimeout(total=CONFIG_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(server_url, ssl=False) as r:
                text = await r.text()
        server_config = json.loads(text)
        web_sockets_port = server_config.get('webSocketsPortVer4')
        if not web_sockets_port:
            return str(self.base_url)
        return str(self.base_url) + ':' + str(web_sockets_port)


    async def on_connected(self):
        print("Соединился с socket сервером...")

        self.authorized = False
        if self.auth_task and not self.auth_task.done():
            self.auth_task.cancel()
        self.auth_task = asyncio.create_task(self.start_bot())


    async def start_bot(self):
        delay = AUTH_DELAY_MIN
        while True:
            await asyncio.sleep(delay)
            if not sio.connected:
                return

            print("Стартую бота...")
            try:
                res = await sio.call(
                    START_BOT,
                    {
                        'token': self.token,
                        'name': self.bot_name
                    },
                    timeout=AUTH_TIMEOUT
                )
            except socketio.exceptions.TimeoutError:
                res = {'error': 'timeout'}
            except Exception as e:
                print('Не удалось отправить start-bot: ', e)
                return

            success = isinstance(res, dict) and not res.get('error')
            if success:
                self.authorized = True

            await self.call_on_start(res)

            if success:
                return

            delay = min(delay * 2, AUTH_DELAY_MAX)
            print('Авторизация не удалась, повтор через', delay, 'сек: ', res)


    async def call_on_start(self, res):
        if not self.on_start:
            return
        try:
            result = self.on_start(res)
            if inspect.isawaitable(result):
                await result
        except Exception as e:
            print('Ошибка в on_start: ', e)


    @property
    def is_ready(self):
        return self.authorized and sio.connected


    def on(self, event_name, callback):
        sio.on(event_name, handler=callback)

    async def emit(self, event_name, data, callback=None):
        await sio.emit(event_name, data=data, callback=callback)
    
    async def send_message(self, params, data, callback=cb_send_message):
        if not params:
            print('Для отправки сообщения необходим, как минимум cid пользователя')
            return
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
    
    async def send_message_received(self, msg_id, callback=None):
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
    