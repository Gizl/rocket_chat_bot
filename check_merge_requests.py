from datetime import datetime, timedelta
import re
import logging
from urllib.parse import urlparse, urlunparse

import gitlab
from jira import JIRA, exceptions as jira_exceptions

from settings import GITLAB_TOKEN, GITLAB_URL, JIRA_NAME, JIRA_PASSWORD, JIRA_BASE_URL, JIRA_TASK_STATUS, JIRA_TASK_PREVIOUS_STATUS, \
                        TIME_WINDOW_IN_HOURS, REGULAR_STRING, REGULAR_STRING_TASK
import db_api

def proceed_gitlab_merge_requests():
    """
    The function return a list of urls of jira tasks, which should be processed.
    :return: list of URLS of Jira tasks, which should be closed
    """
    regular_expression = re.compile(REGULAR_STRING)
    gitlab_url_parsed = urlparse(GITLAB_URL)
    base_url = urlunparse((gitlab_url_parsed.scheme, gitlab_url_parsed.netloc, '', '', '', ''))
    try:
        my_gitlab = gitlab.Gitlab(base_url, private_token=GITLAB_TOKEN)
        my_gitlab.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabHttpError):
        logging.error("Unable to login with provided token.")
        return set()

    merges = list()
    project_ids = db_api.DBApi().get_all_project_ids()
    for project_id in project_ids:
        try:
            project = my_gitlab.projects.get(project_id)
            merges += project.mergerequests.list()
        except (gitlab.exceptions.GitlabHttpError,
                gitlab.exceptions.GitlabListError,
                gitlab.exceptions.GitlabGetError):  # Missing rights to check project or unable to find it
            pass

    jira_urls = set()
    t_now = datetime.now()
    t_edge = t_now - timedelta(hours=TIME_WINDOW_IN_HOURS)

    for merge in merges:
        urls = re.findall(regular_expression, merge.description)
        for url in urls:
            t_updated = datetime.strptime(merge.updated_at, "%Y-%m-%dT%H:%M:%S.%fZ")
            if t_updated > t_edge:
                jira_urls.add(url)
    return jira_urls


def proceed_jira_tasks(jira_urls):
    """
    The function will close the provided tasks in JIRA, if they actually exists.
    :param jira_urls: set of urls
    :return: None
    """

    options = {"server": JIRA_BASE_URL}
    jira = JIRA(options, basic_auth=(JIRA_NAME, JIRA_PASSWORD))
    regular_expression = re.compile(REGULAR_STRING_TASK)

    for url in jira_urls:
        try:
            task_id = re.findall(regular_expression, url)[0]
        except IndexError:
            logging.error("Couldn't find task ID in URL {0}".format(url))
            continue
        try:
            previous_status = jira.issue(task_id).fields.status.name
            if previous_status == JIRA_TASK_PREVIOUS_STATUS and previous_status != JIRA_TASK_STATUS:
                for action in jira.transitions(task_id):
                    if action.get('name', '') == JIRA_TASK_STATUS:
                        transition_id = int(action['id'])
                        jira.transition_issue(task_id, transition_id)
                        logging.info("Task {0} was updated to '{1}' status".format(task_id, JIRA_TASK_STATUS))
                        break
        except jira_exceptions.JIRAError:
            logging.error("Couldn't proceed provided task {0}".format(task_id))


logging.basicConfig(filename="logs.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)-10s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    urls = proceed_gitlab_merge_requests()
    proceed_jira_tasks(urls)
