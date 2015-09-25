import tp

"""
  TODO:

  - Entry point needs to take class factory

"""

def get_project(project_acid, tp_url, auth=None):
  """Entry point into API, returned Project object
     user can query for entities
  """
  client = tp.TPClient(tp_url,auth)
  return tp.Project(project_acid,client)
