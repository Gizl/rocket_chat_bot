import sqlite3

from settings import DB_PATH

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()


def add_developer(channel, username, project_id, impact):
    # channel
    cursor.execute("""SELECT * FROM channel WHERE channel.name = ?""", (channel, ))
    if len(cursor.fetchall()) == 0:
        cursor.execute("""INSERT INTO channel (name) VALUES (?)""", (channel, ))
        connection.commit()
    # developer
    cursor.execute("""SELECT * FROM developer WHERE developer.username = ?""", (username, ))
    if len(cursor.fetchall()) == 0:
        cursor.execute("""INSERT INTO developer (username) VALUES (?)""", (username,))
        connection.commit()
    # project
    cursor.execute("""SELECT * FROM project WHERE project.project_id = ?""", (project_id, ))
    if len(cursor.fetchall()) == 0:
        # TODO: search by project name
        cursor.execute("""INSERT INTO project (project_id, channel) VALUES (?, ?)""", (project_id, channel, ))
        connection.commit()
    # developer_project
    cursor.execute("""SELECT * FROM developer_project WHERE project = ? and developer = ?""", (project_id, username, ))
    if len(cursor.fetchall()) == 0:
        cursor.execute("""INSERT INTO developer_project (developer, project, impact) 
        VALUES (?, ?, ?)""", (username, project_id, impact, ))
        connection.commit()
    # TODO: add else with update

if __name__ == '__main__':
    add_developer("connect", "lev", "23f23f23f23f23f", "1")