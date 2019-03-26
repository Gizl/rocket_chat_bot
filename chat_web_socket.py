import websocket
import threading
import time
import queue
from typing import List
from rocketchat_API.rocketchat import RocketChat
import settings
import traceback


class RocketChatReader(threading.Thread):
    """Создать инстанс со списком имен каналов в конструкторе(имена должны быть уникальны)"""
    """Вызвать connect(), подключиться к ридеру get_messages_queue() и слушать сообщения из чатов"""
    """Для динамического добавления/удаления подпиcок на каналы 
        (только после вызова connect()) вызвать add_channels()/delete_channels()"""
    """Для закрытия соединения у ридера вызвать close_connection()"""

    def __init__(self, channel_names: List[str]):
        threading.Thread.__init__(self, daemon=True)
        self.__rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
        self.__ws = websocket.WebSocket()
        self.__is_closed = True
        self.__is_started = False
        self.__messages_queue = queue.Queue()
        self.__channels = dict()
        self.__channels = {name: self.__get_channel_id(name) for name in channel_names}

    def connect(self) -> None:
        try:
            self.__ws.connect("wss://open.rocket.chat/websocket")

            self.__ws.send("{\"msg\": \"connect\","
                           " \"version\": \"1\","
                           " \"support\": [\"1\"]}")

            self.__ws.send("{\"msg\": \"method\",\"method\": \"login\",\"id\": \"42\",\"params\":[{ \"resume\": "
                           "\"" + settings.ROCKET_TOKEN + "\" }]}")

            for channel_id in self.__channels.values():
                self.__subscribe(channel_id)

            if not self.__is_started:
                self.start()
                self.__is_started = True

            self.__is_closed = False

            print("RocketChatReader has started")
        except:
            time.sleep(1)
            self.connect()

    def close_connection(self) -> None:
        self.__is_closed = True
        self.__ws.close()

    def get_messages_queue(self) -> queue:
        return self.__messages_queue

    def add_channels(self, channel_names: List[str]) -> None:
        for name in channel_names:
            if name not in self.__channels:
                channel_id = self.__get_channel_id(name)
                self.__subscribe(channel_id)
                self.__channels[name] = channel_id

    def delete_channels(self, channel_names: List[str]) -> None:
        [self.__unsubscribe(name) for name in channel_names]

    def __get_channel_id(self, channel_name) -> str:
        return self.__rocket.rooms_info(room_name=channel_name).json().get('room').get('_id')

    def __subscribe(self, channel_id) -> None:
        self.__ws.send(
            "{\"msg\": \"sub\",\"id\": \"" + channel_id + "\",\"name\": \"stream-room-messages\","
                                                          "\"params\": [\"" + channel_id + "\",true]}")

    def __unsubscribe(self, channel_name):
        self.__ws.send("{\"msg\": \"unsub\",\"id\": \"" + self.__channels.get(channel_name) + "\"}")
        del self.__channels[channel_name]

    def run(self):
        while True:
            try:
                data = self.__ws.recv()
                print(data)
            except:
                # если ошибка не после вызова close_connection (разрыв соединения, timeout), то конектим обратно
                if not self.__is_closed:
                    print("Connection lost")
                    self.__ws.close()
                    self.connect()
                    time.sleep(1)
                else:
                    break
            else:
                if "ping" in data:
                    # требование апи
                    # self.__ws.send("{\"msg\": \"pong\"}")
                    pass
                # небольшой временный велосипед, для чтения только тела сообщения
                elif "changed" in data and "stream-room-messages" in data:
                    elements = data.split(',')
                    msg = [elem for elem in elements if "msg" in elem]
                    msg = msg[1][7:-1]
                    self.__messages_queue.put(msg)


if __name__ == "__main__":
    names: List[str] = list()
    names.append("channel_name")
    reader = RocketChatReader(names)
    reader.connect()
    while True:
        print(reader.get_messages_queue().get())
        print(reader.get_messages_queue().get())
        time.sleep(5)
        reader.close_connection()
        break
