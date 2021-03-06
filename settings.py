import os
from urllib.parse import urljoin

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# JIRA
JIRA_NAME = os.getenv("JIRA_NAME")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")
JIRA_TASK_STATUS = os.getenv("JIRA_TASK_STATUS")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_PROJECT = os.getenv("JIRA_PROJECT")
JIRA_TASK_PREVIOUS_STATUS = os.getenv("JIRA_TASK_PREVIOUS_STATUS")
# DATABASE
DB_PATH = os.getenv("DB_PATH")
# GITLAB
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
GITLAB_URL = "https://gitlab.com/api/v4/"
# ROCKET CHAT
ROCKET_URL = os.getenv("ROCKET_URL")
ROCKET_USERNAME = os.getenv("ROCKET_USERNAME")
ROCKET_PASSWORD = os.getenv("ROCKET_PASSWORD")
ROCKET_TOKEN = os.getenv("ROCKET_TOKEN")
ROCKET_ID = os.getenv("ROCKET_ID")
# ADDITIONAL PARAMETERS
TIME_WINDOW_IN_HOURS = 24
REGULAR_STRING = urljoin(JIRA_BASE_URL, 'browse/.*')
REGULAR_STRING_TASK = urljoin(JIRA_BASE_URL, 'browse/(.*)')

CREATE_MR_JIRA_TASKS_PARAMS = [os.getenv('GITLAB_PROJECT_ID'), os.getenv('JIRA_PROJECT'), os.getenv('JIRA_USER')]
