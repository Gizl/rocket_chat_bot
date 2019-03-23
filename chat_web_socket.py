import websocket
import threading
import time
import queue
from typing import List
from rocketchat_API.rocketchat import RocketChat
import settings
import traceback


class RocketChatReader(threading.Thread):
    """Создать инстанс со списком имен каналов в конструкторе"""
    """Вызвать connect(), подключиться к ридеру get_messages_queue() и слушать сообщения из чатов"""
    """Для закрытия соединения у ридера вызвать close_connection()"""

    def __init__(self, channel_names: List[str]):
        threading.Thread.__init__(self, daemon=True)
        self.__rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
        self.__ws = websocket.WebSocket()
        self.__messages_queue = queue.Queue()
        self.__channel_ids = list()
        self.__get_channel_ids(channel_names)

    def __get_channel_ids(self, channel_names: List[str]) -> None:
        for name in channel_names:
            self.__channel_ids.append(self.__rocket.rooms_info(room_name=name).json().get('room').get('_id'))

    def connect(self) -> None:
        self.__ws.connect("wss://open.rocket.chat/websocket")

        self.__ws.send("{\"msg\": \"connect\","
                       " \"version\": \"1\","
                       " \"support\": [\"1\"]}")

        self.__ws.send("{\"msg\": \"method\",\"method\": \"login\",\"id\": \"42\",\"params\":[{ \"resume\": "
                       "\"" + settings.ROCKET_TOKEN + "\" }]}")

        for channel_id in self.__channel_ids:
            self.__ws.send(
                "{\"msg\": \"sub\",\"id\": \"" + settings.ROCKET_ID + "\",\"name\": \"stream-room-messages\","
                                                                      "\"params\": [\"" + channel_id + "\",true]}")

        self.start()

    def close_connection(self) -> None:
        self.__ws.close()

    def get_messages_queue(self) -> queue:
        return self.__messages_queue

    # TODO
    def add_channels(self, channel_names: List[str]) -> None:
        pass

    # TODO
    def delete_channels(self, channel_names: List[str]) -> None:
        pass

    def run(self):
        while True:
            try:
                data = self.__ws.recv()
            except:
                print(traceback.format_exc())
                break
            else:
                if "ping" in data:
                    # требование апи
                    self.__ws.send("{\"msg\": \"pong\"}")
                # небольшой временный велосипед, для чтения только тела сообщения
                elif "changed" in data and "stream-room-messages" in data:
                    elements = data.split(',')
                    msg = [elem for elem in elements if "msg" in elem]
                    msg = msg[1][7:-1]
                    self.__messages_queue.put(msg)


if __name__ == "__main__":
    names: List[str] = list()
    reader = RocketChatReader(names)
    reader.connect()
    while True:
        print(reader.get_messages_queue().get())
        print(reader.get_messages_queue().get())
        time.sleep(5)
        reader.close_connection()
        break
