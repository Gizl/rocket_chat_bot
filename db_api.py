import sqlite3
import settings
from chat_web_socket import RocketChatReader, Message
from rocketchat_API.rocketchat import RocketChat


class DBApi:
    def __init__(self, connection: sqlite3.Connection, cursor: sqlite3.Cursor):
        self.__connection = connection
        self.__cursor = cursor
        self.__commands = \
            "All bot commands:\n" \
            "$bot_api create_new_user username gitlab_username\n" \
            "$bot_api delete_user username\n" \
            "$bot_api add_user_to_project username project_id impact\n" \
            "$bot_api delete_user_from_project username project_id\n" \
            "$bot_api ger_users_from_project project_id\n" \
            "$bot_api ping"

    def help(self) -> str:
        return self.__commands

    def __create_new_user(self, username: str, gitlab_username: str) -> str:

        if not self.__find_user(username):
            self.__cursor.execute("""INSERT INTO developer (username, gitlab) VALUES (?, ?)""",
                                  (username, gitlab_username))
            self.__connection.commit()
            return f"User {username} created"
        else:
            return f"User {username} already exists"

    def __add_user_to_project(self, username: str, project_id: str, impact: str) -> str:

        try:
            impact_int = int(impact)
        except:
            return "Impact must be an integer"

        if not self.__find_user(username):
            return f"User {username} not found"

        if not self.__find_project(project_id):
            return f"Project {project_id} not found"

        self.__cursor.execute("""SELECT * FROM developer_project WHERE developer = ? AND project = ?""",
                              (username, project_id))
        if len(self.__cursor.fetchall()) != 0:
            return f"User {username} already in this project({project_id})"

        self.__cursor.execute("""INSERT INTO developer_project (developer, project, impact)VALUES (?, ?, ?)""",
                              (username, project_id, impact_int))
        self.__connection.commit()
        return f"User {username} added to project {project_id}"

    def __delete_user(self, username: str) -> str:

        if not self.__find_user(username):
            return f"User {username} not found"
        self.__cursor.execute("""DELETE FROM developer WHERE developer.username = ?""", [username])
        self.__cursor.execute("""DELETE FROM developer_project WHERE developer = ?""", [username])
        self.__connection.commit()
        return f"User {username} removed"

    def __delete_user_from_project(self, username: str, project_id: str) -> str:

        if not self.__find_user(username):
            return f"User {username} not found"

        if not self.__find_project(project_id):
            return f"Project {project_id} not found"

        self.__cursor.execute("""DELETE FROM developer_project WHERE developer = ? AND
                                                                        project = ?""", (username, project_id))
        self.__connection.commit()
        return f"User {username} removed from {project_id} project"

    def __ger_users_from_project(self, project_id: str) -> str:

        if not self.__find_project(project_id):
            return f"Project {project_id} not found"

        self.__cursor.execute("""SELECT developer FROM developer_project WHERE project = ?""", [project_id])
        users = self.__cursor.fetchall()
        response = "".join([user[0] + "\n" for user in users])
        response = f"Users in the project {project_id}:\n{response}"
        return response


    def get_all_project_ids(self) -> list:

        self.__cursor.execute("""SELECT project_id FROM project""")
        records = self.__cursor.fetchall()
        return [record[0] for record in records]

    def __find_user(self, username: str) -> bool:

        self.__cursor.execute("""SELECT * FROM developer WHERE developer.username = ?""", [username])
        if len(self.__cursor.fetchall()) == 0:
            return False
        else:
            return True

    def __find_project(self, project_id: str) -> bool:

        self.__cursor.execute("""SELECT * FROM project WHERE project.project_id = ?""", [project_id])
        if len(self.__cursor.fetchall()) == 0:
            return False
        else:
            return True

    def process(self, msg: list) -> str:
        try:
            if msg[1] == "create_new_user":
                return self.__create_new_user(msg[2], msg[3])
            elif msg[1] == "add_user_to_project":
                return self.__add_user_to_project(msg[2], msg[3], msg[4])
            elif msg[1] == "delete_user":
                return self.__delete_user(msg[2])
            elif msg[1] == "delete_user_from_project":
                return self.__delete_user_from_project(msg[2], msg[3])
            elif msg[1] == "ger_users_from_project":
                return self.__ger_users_from_project(msg[2])
            elif msg[1] == "ping":
                return "pong"
            else:
                return "Request error\n" + self.help()
        except:
            return "Request error\n" + self.help()


class Main:
    def __init__(self, chat_server: str):
        self.__rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
        self.__connection = sqlite3.connect(settings.DB_PATH)
        self.__cursor = self.__connection.cursor()
        self.__db_api = DBApi(self.__connection, self.__cursor)
        self.__reader = RocketChatReader(chat_server, self.__get_channels())

    def start(self) -> None:
        self.__reader.connect()
        while True:
            request: Message = self.__reader.get_messages_queue().get()
            try:
                message = request.get_message().split(" ")
                if message[0] == "$bot_api":
                    message = [msg for msg in message if msg != ""]
                    response = self.__db_api.process(message)
                    self.__rocket.chat_post_message(response, room_id=request.get_channel_id(),
                                                    alias='BOT NOTIFICATION')
            except:
                self.__rocket.chat_post_message("Oops. Server error.",
                                                room_id=request.get_channel_id(),
                                                alias='BOT NOTIFICATION')

    def __get_channels(self) -> list:
        self.__cursor.execute("""SELECT name FROM channel""")
        return [channel[0] for channel in self.__cursor.fetchall()]


if __name__ == "__main__":
    Main(settings.ROCKET_URL).start()
