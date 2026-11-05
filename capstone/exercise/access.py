"""Authorization helpers. Keep EVERY "who may touch what" rule here so routers stay thin and consistent.

TODO:
  get_project_for_member(db, project_id, user) -> Project   404 if missing OR user isn't a member
  require_owner(project, user) -> None                       403 unless user owns the project
  get_task_for_member(db, task_id, user) -> Task             404 if missing OR user isn't a member of its project
  validate_assignee(project, assignee_id) -> None            422 unless assignee_id is None or a member
"""
