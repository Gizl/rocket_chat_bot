import sqlite3

from settings import DB_PATH

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()
cursor.execute("""CREATE TABLE channel
                  (name char (255) PRIMARY KEY)
               """)
cursor.execute("""CREATE TABLE developer
                  (username char (255) PRIMARY KEY)
               """)
cursor.execute("""CREATE TABLE project
                  (
                  project_id char (255) PRIMARY KEY,
                  channel INTEGER REFERENCES channel(name) ON DELETE CASCADE
                  )
               """)
cursor.execute("""CREATE TABLE developer_project
                  (
                  developer INTEGER REFERENCES developer(username) ON DELETE CASCADE,
                  project INTEGER REFERENCES project(project_id) ON DELETE CASCADE,
                  impact smallint 
                  )
               """)

connection.commit()