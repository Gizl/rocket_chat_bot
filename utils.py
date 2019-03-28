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

        channel_message = f"MRs where upvotes are less than {approvers_number}:\n"

        flag = False

        for merge_request in merge_requests:
            if merge_request.get('upvotes') < approvers_number:
                flag = True
                channel_message += merge_request.get('web_url') + '\n'

        if flag:
            rocket.chat_post_message(channel_message, channel=channels_name, alias='BOT NOTIFICATION')
        else:
            continue


def ignore_wip_mr(project_id: str, mr_id: str, mr_link: str) -> bool:
    print(f"WIP MR without <bot_ignore> detected!\n{mr_link}")
    answer = input("Add <bot_ignore>? y/n:")
    if answer == "y":
        url = f"{settings.GITLAB_URL}projects/{project_id}/merge_requests/{mr_id}"
        params = {"private_token": settings.GITLAB_TOKEN, "labels": "bot_ignore"}
        requests.put(url, params=params)
        return True
    else:
        return False
