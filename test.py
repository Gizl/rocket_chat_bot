import sqlite3

from settings import DB_PATH

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
for x in range(10):
    cursor.execute("""INSERT INTO channel (name)
                          VALUES (?)""", (f"channel_{x}", ))
    cursor.execute("""INSERT INTO project (project_id, channel)
                          VALUES (?, ?)""", (f"project_{x}", f"channel_{x}", ))
    cursor.execute("""INSERT INTO developer (username)
                            VALUES (?)""", (f"developer_{x}", ))
    cursor.execute("""INSERT INTO developer_project (developer, project, impact)
                        VALUES (?, ?, ?)""", (f"developer_{x}", f"project_{x}", x))
    conn.commit()
cursor.execute("""SELECT project_id, username, channel.name, impact
                    FROM project
                    INNER JOIN channel
                    LEFT OUTER JOIN developer_project dp on project.project_id = dp.project
                    LEFT OUTER JOIN developer d on dp.developer = d.username

""")
projects = cursor.fetchall()
channels_relations = {}
for project_id, username, channel_name, impact in projects:
    channels_relations.setdefault(channel_name, {}).setdefault(project_id, []).append([username, impact])

print(channels_relations)
