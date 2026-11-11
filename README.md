# roschat-async-bot-python-sdk
Асинхронный Python SDK для написания ботов для сервера РОСЧАТ. [Описание протокола](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api) ботов.

SDK построен на `asyncio`: соединение с сервером работает через `socketio.AsyncClient`, HTTP-запросы — через `aiohttp`. Это асинхронный аналог [roschat-bot-python-sdk](https://github.com/roschat/roschat-bot-python-sdk) с теми же именами методов и событий, поэтому существующего бота можно перенести, добавив `async`/`await`.

## Установка
Перед запуском убедитесь, что у вас уже установлены:
* python 3.8 или новее
* pip
* python3-venv

Скопируйте репозиторий
```bash
git clone https://github.com/g1es0n/roschat-async-bot-python-sdk
cd roschat-async-bot-python-sdk
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Начало работы
Создайте файл `main.py` рядом с папкой `roschat`:
```py
import asyncio
from roschat.bot import Roschat_Bot
from roschat.constants import BOT_MESSAGE_EVENT

bot = Roschat_Bot(
    token="YOUR_BOT_TOKEN",
    base_url="YOUR_ROSCHAT_SERVER_ADDRESS",  # например https://roschat.example.com — без порта и без / в конце
    bot_name="YOUR_BOT_NAME"
)


async def on_bot_start(res):
    if res and res.get('error'):
        print('Ошибка при инициализации:', res)
    else:
        print('Бот готов принимать и отправлять сообщения')


async def main():
    await bot.start(on_bot_start)
    await asyncio.Event().wait()  # не даём программе завершиться, пока бот работает


asyncio.run(main())
```

Запустите скрипт командой:
```bash
python main.py
```

Порт сокет-сервера SDK узнаёт сам из `<base_url>/ajax/config.json`, поэтому в `base_url` его указывать не нужно.

## Пример работы с API
Обработка входящего события от сервера
```py
async def on_bot_message(data):
    await bot.send_message_received(data['id'])                 # сообщение получено
    await bot.send_message_watched(data['id'])                  # сообщение просмотрено
    await bot.send_message(data['cid'], 'Тестовое сообщение')   # отправка сообщения


async def main():
    bot.on(BOT_MESSAGE_EVENT, on_bot_message)  # прослушивание входящего сообщения
    await bot.start(on_bot_start)
    await asyncio.Event().wait()
```

Клавиатура и обработка нажатий:
```py
from roschat.constants import BOT_BUTTON_EVENT

async def show_keyboard(cid):
    await bot.set_bot_keyboard({
        'cid': cid,
        'keyboard': [[
            {'text': 'Шутка', 'callbackData': 'joke'},
            {'text': 'Новости', 'callbackData': 'news'}
        ]],
        'action': 'show'
    })


async def on_button(data):
    if data['callbackData'] == 'joke':
        await bot.send_message(data['cid'], 'Сейчас будут шутки')

bot.on(BOT_BUTTON_EVENT, on_button)
```

## Отличия от синхронной версии
* Все методы, которые обращаются к серверу, — корутины, их нужно вызывать через `await`. Исключение — `on()`, это обычный метод.
* Обработчики событий и `callback` могут быть как `async def`, так и обычными функциями. Обычная функция выполняется прямо в цикле событий, поэтому в ней не должно быть блокирующих вызовов (`time.sleep`, `requests` и т. п.) — используйте `asyncio.sleep`, `aiohttp`.
* Вместо цикла `while True: sleep(1)` программу удерживает `await asyncio.Event().wait()` внутри `main()`.
* Несколько сообщений можно отправлять параллельно: `await asyncio.gather(bot.send_message(cid1, 'A'), bot.send_message(cid2, 'B'))`.

## Методы Roschat_Bot
### Инициализация
__`Roschat_Bot(token, base_url, bot_name)`__

Создание объекта бота: токен, адрес сервера РОСЧАТ и уникальное имя бота

__`await start(on_start)`__

Создание сокет соединения с сервером и начало работы бота ([описание](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-session-start-bot)). `on_start(res)` вызывается с ответом сервера на `start-bot`; при ошибке авторизации в ответе будет поле `error`

### Работа с сообщениями
__`on(BOT_MESSAGE_EVENT, event_handler)`__

Прослушивание события `bot-message-event` - входящее сообщение от пользователя

__`await send_message({cid, dataType}, data[, callback])`__

или

__`await send_message(cid, data[, callback])`__ - для отправки текстового сообщения

Отправить сообщение пользователю ([описание](
https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-send-bot-message
)). Если `data` — не строка, она сериализуется в JSON

__`await send_message_received(id[, callback])`__

Сообщить о получении сообщения пользователя ([описание](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-bot-message-received))

__`await send_message_watched(id[, callback])`__

Сообщить о просмотре сообщения пользователя ([описание](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-bot-message-watched))

__`await delete_bot_message(id[, callback])`__

Удалить сообщение в чате ([описание](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-delete-bot-message))

### Работа с клавиатурой
__`on(BOT_BUTTON_EVENT, function)`__

Событие `bot-button-event` - нажатие кнопки пользователем ([описание](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-bot-button-event))

__`await set_bot_keyboard({cid, keyboard[, action]})`__

Установить клавиатуру в чате с пользователем ([описание](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api-set-bot-keyboard))

### Остальные события протокола
__`await emit(event_name, data[, callback])`__

Отправить на сервер любое событие [протокола ботов](https://github.com/roschat/roschat-docs/wiki/roschat-bot-api), для которого в SDK нет отдельного метода (например, `get-bot-messages`)

## Константы
Имена событий лежат в `roschat.constants`: `START_BOT`, `SEND_BOT_MESSAGE`, `BOT_MESSAGE_EVENT`, `BOT_MESSAGE_RECEIVED`, `BOT_MESSAGE_WATCHED`, `DELETE_BOT_MESSAGE`, `SET_BOT_KEYBOARD`, `BOT_BUTTON_EVENT`.
