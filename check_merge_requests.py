from datetime import datetime, timedelta
import re
import sys
import logging

import gitlab
from jira import JIRA, exceptions as jira_exceptions

from settings1 import GITLAB_TOKEN, JIRA_NAME, JIRA_PASSWORD, JIRA_BASE_URL, JIRA_TASK_STATUS, TIME_WINDOW_IN_HOURS, \
                        REGULAR_STRING, REGULAR_STRING_TASK

def proceed_gitlab_merge_requests():
    """
    The function return a list of url of jira tasks, which should be closed
    :param token: personal token from Gitlab profile
    :param t: how many hours to the past to proceed Gitlab merges
    :return: list of URLS of Jira tasks, which should be closed
    """
    regular_expression = re.compile(REGULAR_STRING)
    try:
        user = gitlab.Gitlab("https://gitlab.com", private_token=GITLAB_TOKEN)
        user.auth()
        merges = user.mergerequests.list()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabHttpError) as error:
        now = datetime.now().replace(microsecond=0)
        logging.error("Unable to login with provided token. {0}".format(now))
        sys.exit(1)

    jira_urls = set()
    t_now = datetime.now()
    t_edge = t_now - timedelta(hours=TIME_WINDOW_IN_HOURS)

    for merge in merges:
        urls = re.findall(regular_expression, merge.description)
        for url in urls:
            t_updated = datetime.strptime(merge.updated_at[:19], "%Y-%m-%dT%H:%M:%S")
            if t_updated > t_edge:
                jira_urls.add(url)
    return jira_urls


def proceed_jira_tasks(jira_urls):
    """
    The function will close the provided tasks in JIRA, if they actually exists.
    :param jira_urls: set of urls
    :param name: You login name in JIRA. For example, itursunov.
    :param pw: You password in JIRA. Be careful! If you provided incorrect password, it might triggering capture and you won't be able to turn it off after.
    :return: None
    """
    options = {"server" : JIRA_BASE_URL}
    jira = JIRA(options, basic_auth=(JIRA_NAME, JIRA_PASSWORD))
    regular_expression = re.compile(REGULAR_STRING_TASK)
    now = datetime.now().replace(microsecond=0)

    for url in jira_urls:
        try:
            task_id = re.findall(regular_expression, url)[0][1]
            for action in jira.transitions(task_id):
                if action.get('name','') == JIRA_TASK_STATUS:
                    transition_id = int(action['id'])
                    jira.transition_issue(task_id, transition_id)
                    logging.info("Task {0} was updated to '{1}' status {2}".format(task_id, JIRA_TASK_STATUS, now))
                    break
        except IndexError:
            logging.error("Couldn't find task ID in URL {0} {1}".format(url, now))
        except jira_exceptions.JIRAError:
            logging.error("Couldn't proceed provided task {0} {1}".format(task_id, now))


if __name__ == "__main__":
    logging.basicConfig(filename="logs.log", level=logging.INFO)
    urls = proceed_gitlab_merge_requests()
    proceed_jira_tasks(urls)