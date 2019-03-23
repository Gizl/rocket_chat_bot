import os

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

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
