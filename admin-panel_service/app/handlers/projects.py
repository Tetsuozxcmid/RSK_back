from clients.projects.projects_client import ProjectsClient

project_client = ProjectsClient()

async def handle(data: dict):
    action = data.get("action")
    project_id = data.get("id")
    payload = data.get("data", {})

    if action == "get_all":
        return await project_client.get_all_projects(project_id)
