import math
import sqlite3
from operator import itemgetter

import requests
from rocketchat_API.rocketchat import RocketChat

import settings

rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)

conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
cursor = conn.cursor()

request_params = {"private_token": settings.GITLAB_TOKEN, "state": "opened"}
cursor.execute("""SELECT project_id, username, channel.name, impact
                    FROM project
                    INNER JOIN channel
                    LEFT OUTER JOIN developer_project dp on project.project_id = dp.project
                    LEFT OUTER JOIN developer d on dp.developer = d.username""")
projects = cursor.fetchall()
channels_relations = {}
for project_id, username, channel_name, impact in projects:
    channels_relations.setdefault(channel_name, {}).setdefault(project_id, []).append([username, impact])

for channel_name, project_relations in channels_relations.items():
    channel_message = {}
    for project_id, developers in project_relations.items():
        total_impact = sum([x[1] for x in developers])
        url = "{}projects/{}/merge_requests".format(settings.GITLAB_URL, project_id)
        merge_requests = [[x, 2] for x in requests.get(url, params=request_params).json()]
        total_approvals = len(merge_requests) * 2 # TODO: 2 is number of revievers, add this to DB
        developers = sorted(developers, key=itemgetter(1), reverse=True)
        for developer, impact in developers:
            percent = impact/total_impact
            mr_for_developer = math.ceil(total_approvals * percent)
            counter = 0
            for i, merge_request in enumerate(merge_requests):
                if merge_request[1] <= 0:
                    continue
                counter += 1
                channel_message.setdefault(developer, []).append(merge_request[0])
                merge_requests[i][1] -= 1
                if counter >= mr_for_developer:
                    break
    channel_message = "\n".join([f"\n*{key}:* \n{', '.join([str(x.get('web_url')) for x in values])}" for key, values in channel_message.items()])
    channel_message = f"Please, review those MRs today:\n{channel_message}"
    rocket.chat_post_message(channel_message, channel=channel_name, alias='BOT NOTIFICATION')
