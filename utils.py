import datetime
import settings
import requests
from rocketchat_API.rocketchat import RocketChat


def check_merged_requests_for_upvotes(channels_name: str, projects: dict):
    rocket = RocketChat(settings.ROCKET_USERNAME, settings.ROCKET_PASSWORD, server_url=settings.ROCKET_URL)
    request_params = {"private_token": settings.GITLAB_TOKEN, "state": "merged",
                      "created_after": datetime.date.today() - datetime.timedelta(days=1)}

    for project_id, approvers_number in projects.items():
        url = f"{settings.GITLAB_URL}projects/{project_id}/merge_requests"
        merge_requests = requests.get(url, params=request_params).json()

        channel_message = f"Unapproved MRs:\n"

        flag = False

        for merge_request in merge_requests:
            if merge_request.get('upvotes') < approvers_number:
                flag = True
                channel_message += merge_request.get('web_url') + '\n'

        if flag:
            rocket.chat_post_message(channel_message, channel=channels_name, alias='BOT NOTIFICATION')
        else:
            continue
