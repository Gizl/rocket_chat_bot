import math
import sqlite3
from operator import itemgetter
from random import randint
from typing import List
import datetime

import requests
from rocketchat_API.rocketchat import RocketChat

import settings
import utils


class Notifier:
    rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    request_params = {"private_token": settings.GITLAB_TOKEN, "state": "opened"}

    def get_data(self):
        self.cursor.execute("""SELECT  pr.project_id, d.username, d.gitlab, channel.name, dp.impact FROM channel 
                            JOIN project pr ON channel.name = pr.channel
                            JOIN developer_project dp on pr.project_id = dp.project
                            JOIN developer d on dp.developer = d.username""")
        projects = self.cursor.fetchall()
        channels_relations = {}
        for project_id, username, gitlab, channel_name, impact in projects:
            channels_relations.setdefault(channel_name, {}).setdefault(project_id, []).append([username, gitlab, impact])
        return channels_relations

    def send(self):
        channels_relations = self.get_data()
        for channel_name, project_relations in channels_relations.items():
            channel_message = {}
            all_for_merge = []
            all_conflicts = {}
            projects = {}
            for project_id, developers in project_relations.items():
                total_impact = sum([x[2] for x in developers])
                approvers_number = 2 if len(developers) > 3 else 1
                projects[project_id] = approvers_number
                merge_requests, for_merge, conflicts = self.get_merge_requests(approvers_number, project_id)
                all_for_merge.extend(for_merge)
                developers_dict = {y:x for x, y, _ in developers}
                for conflict in conflicts:
                    all_conflicts.setdefault(developers_dict.get(conflict.get('author').get('username')), []).append(conflict.get('web_url'))
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
                        channel_message.setdefault(developer, []).append(merge_request[0])
                        merge_requests[i][1] -= 1
                        counter += 1
                channel_message = self.set_leftovers(channel_message, developers, merge_requests)
            self.send_notifications(channel_name, channel_message, all_for_merge, all_conflicts, projects)

    def get_merge_requests(self, approvers_number, project_id):
        for_merge = []
        conflicts = []
        formatted_mr = []
        url = f"{settings.GITLAB_URL}projects/{project_id}/merge_requests"
        merge_requests = requests.get(url, params=self.request_params).json()
        for merge_request in merge_requests:
            if merge_request.get('work_in_progress'):
                continue
            if merge_request.get('merge_status') == 'cannot_be_merged':
                conflicts.append(merge_request)
                continue
            discussions = requests.get(f"{url}/{merge_request.get('iid')}/discussions", params=self.request_params).json()
            can_be_merged = True
            for discussion in discussions:
                for note in discussion.get('notes'):
                    if note.get('resolvable') and note.get('resolved') is False:
                        can_be_merged = False
                        break
            pipelines = requests.get(f"{url}/{merge_request.get('iid')}/pipelines", params=self.request_params).json()
            if len(pipelines) and pipelines[0].get('status') != 'success':
                can_be_merged = False
            if not can_be_merged:
                conflicts.append(merge_request)
                continue
            if merge_request.get('upvotes') >= approvers_number:
                for_merge.append(merge_request.get('web_url'))
            else:
                formatted_mr.append([merge_request, approvers_number])
        return formatted_mr, for_merge, conflicts

    def send_notifications(self, channel_name, channel_message, for_merge, conflicts, projects):
        utils.check_merged_requests_for_upvotes(channel_name, projects)
        nl = "\n"
        if channel_message:
            channel_message = "\n".join(
                [f"\n{f'@{key}' if key else '*Unknown Users*'}: \n{f'{nl}'.join([str(x.get('web_url')) for x in values])}" for key, values in
                 channel_message.items()])
            channel_message = f"Please, review those MRs today (you need to press thumb up/upvote):\n{channel_message}\n"
            self.rocket.chat_post_message(channel_message, channel=channel_name, alias='BOT NOTIFICATION')
        if for_merge:
            for_merge = '\n'.join(for_merge)
            for_merge = f'MRs are ready to be merged:\n{for_merge}'
            self.rocket.chat_post_message(for_merge, channel=channel_name, alias='BOT NOTIFICATION')
        if conflicts:
            conflicts = "\n".join(
                [f"\n{f'@{key}' if key else '*Unknown Users*'}: \n{f'{nl}'.join([x for x in values])}" for key, values in conflicts.items()])
            conflicts = f"Please, check MRs for conflicts, unresolved discussions or failed pipelines:\n{conflicts}\n"
            self.rocket.chat_post_message(conflicts, channel=channel_name, alias='BOT NOTIFICATION')

    def set_leftovers(self, channel_message, developers, merge_requests):
        while [x for x in merge_requests if x[1] > 0]:
            mr = [x for x in merge_requests if x[1] > 0][0][0]
            developer = developers[randint(0, len(developers) - 1)]
            if mr.get('author').get('username') == developer[1]:
                continue
            channel_message.setdefault(developer[0], []).append(mr)
            i = [i for i, e in enumerate(merge_requests) if e[0]['id'] == mr.get('id')]
            merge_requests[i[0]][1] -= 1
        return channel_message


if __name__ == '__main__':
    Notifier().send()
