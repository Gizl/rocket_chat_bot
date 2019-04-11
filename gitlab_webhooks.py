from flask import Flask, request, Response
import settings
from jira import JIRA


class GitlabWebHook:
    app = Flask(__name__)
    jira_project = None
    jira_user = None
    options = {"server": settings.JIRA_BASE_URL}
    jira = JIRA(options, basic_auth=(settings.JIRA_NAME, settings.JIRA_PASSWORD))

    @staticmethod
    def start(jira_project: str = None, jira_user: str = None) -> None:
        if jira_project and jira_user:
            GitlabWebHook.jira_project = jira_project
            GitlabWebHook.jira_user = jira_user
        else:
            GitlabWebHook.jira_project = settings.JIRA_PROJECT
            GitlabWebHook.jira_user = settings.JIRA_USER
            if not GitlabWebHook.jira_project and not GitlabWebHook.jira_user:
                raise Exception("missing jira options")

        GitlabWebHook.app.run(debug=False, host="0.0.0.0")

    @staticmethod
    @app.route("/gitlab", methods=["POST"])
    def index():
        data = request.get_json()
        if data.get("event_type") == "merge_request":
            if data.get("object_attributes").get("state") == "merged":
                new_issue = GitlabWebHook.jira.create_issue(project=GitlabWebHook.jira_project,
                                                            summary="OE2 %s" % data.get("object_attributes").get("title"),
                                                            description=data.get("object_attributes").get("url"), issuetype={'name': "Task"})
                new_issue.update(assignee={"name": GitlabWebHook.jira_user})
        return Response(status=201)


if __name__ == "__main__":
    GitlabWebHook.start()
