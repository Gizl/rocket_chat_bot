import math
import sqlite3
from operator import itemgetter
from random import randint

import requests
from rocketchat_API.rocketchat import RocketChat

import settings

rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)

conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
cursor = conn.cursor()

request_params = {"private_token": settings.GITLAB_TOKEN, "state": "opened"}
cursor.execute("""SELECT  pr.project_id, d.username, d.username, channel.name, dp.impact FROM channel 
                    JOIN project pr ON channel.name = pr.channel
                    JOIN developer_project dp on pr.project_id = dp.project
                    JOIN developer d on dp.developer = d.username""")
projects = cursor.fetchall()
channels_relations = {}
for project_id, username, gitlab, channel_name, impact in projects:
    channels_relations.setdefault(channel_name, {}).setdefault(project_id, []).append([username, gitlab, impact])

for channel_name, project_relations in channels_relations.items():
    channel_message = {}
    for project_id, developers in project_relations.items():
        total_impact = sum([x[2] for x in developers])
        approvers_number = 2 if len(developers) > 3 else 1
        url = "{}projects/{}/merge_requests".format(settings.GITLAB_URL, project_id)
        merge_requests = [[x, approvers_number] for x in requests.get(url, params=request_params).json()]
        total_approvals = len(merge_requests) * approvers_number
        developers = sorted(developers, key=itemgetter(2), reverse=True)
        for developer, gitlab_username, impact in developers:
            percent = impact/total_impact
            mr_for_developer = math.ceil(total_approvals * percent)
            counter = 0
            for i, merge_request in enumerate(merge_requests):
                if counter >= mr_for_developer:
                    break
                if merge_request[1] <= 0 or merge_request[0].get('author').get('username') == gitlab_username:
                    continue
                counter += 1
                channel_message.setdefault(developer, []).append(merge_request[0])
                merge_requests[i][1] -= 1
        while [x for x in merge_requests if x[1] > 0]:
            mr = [x for x in merge_requests if x[1] > 0][0][0]
            developer = developers[randint(0, len(developers)-1)]
            if mr.get('author').get('username') == developer[1]:
                continue
            channel_message.setdefault(developer[0], []).append(mr)
            i = [i for i, e in enumerate(merge_requests) if e[0]['id']==mr.get('id')]
            merge_requests[i[0]][1] -= 1

    channel_message = "\n".join([f"\n@{key}: \n{', '.join([str(x.get('web_url')) for x in values])}" for key, values in channel_message.items()])
    channel_message = f"Please, review those MRs today:\n{channel_message}\n"
    rocket.chat_post_message(channel_message, channel=channel_name, alias='BOT NOTIFICATION')

