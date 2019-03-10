import sqlite3
from pprint import pprint

import requests
from rocketchat_API.rocketchat import RocketChat

import settings

# rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
# pprint(rocket.me().json())
# pprint(rocket.channels_list().json())

conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
cursor = conn.cursor()

request_params = {"private_token": settings.GITLAB_TOKEN, "state": "opened"}
cursor.execute("""SELECT project_id, username, channel.name, impact
                    FROM project
                    INNER JOIN channel
                    LEFT OUTER JOIN developer_project dp on project.project_id = dp.project
                    LEFT OUTER JOIN developer d on dp.developer = d.username""")
projects = cursor.fetchall()
for project_id, username, channel_name,  in projects:

    url = "{}projects/{}/merge_requests".format(settings.GITLAB_URL, project_id)
    response = requests.get(url, params=request_params).json()

    # for merge_request in response:
    #     if merge_request.get("work_in_progress"):
    #         continue
