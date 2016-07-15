import collections
import itertools
import client

ENDPOINTS = [
"Assignables","AssignedEfforts","Assignments","Attachments","Bugs","Builds","Comments","Companies","Context","CustomActivities","CustomRules","EntityStates","EntityTypes","Epics","Features","Generals","GeneralFollowers","GeneralUsers","GlobalSettings","Impediments","InboundAssignables","Iterations","Messages","MessageUids","Milestones","OutboundAssignables","Priorities","Processs","Programs","Projects","ProjectAllocations","ProjectMembers","Relations","RelationTypes","Releases","Requests","Requesters","RequestTypes","Revisions","RevisionFiles","Roles","RoleEfforts","Severities","Tags","Tasks","Teams","TeamAssignments","TeamIterations","TeamMembers","TeamProjects","TeamProjectAllocations","Terms","TestCases","TestCaseRuns","TestPlans","TestPlanRuns","TestRunItemHierarchyLinks","TestSteps","TestStepRuns","Times","Users","UserProjectAllocations","UserStories","Workflows",
] 

"""
Example use:

TP()
p = TP.get('Projects',Id=1)
p.get('Bugs')
p.Id 
p.Name
p.EndData
p.get('Bugs',where="ids=[1,2,3]")
p.get('Releases')

"""
# API BEGINS 
class Query(object):
  """Adapter class for putting requests to TPClients
  """
  def __init__(self, tp_client,**kwargs):
    """
    :param tp.TPClient tp_client: TPclient object
    """
    self._client = tp_client
    self.default_params = kwargs
  
  def create(self,entity_type,data):
    """Create a new entity within TargetProcess Project

    :param data: extra keyword argurments that are used to set entity properties 
    """
    assert entity_type in ENDPOINTS

    params = self.default_params.copy()
    return self._client.create_entity(
      entity_endpoint = entity_type,
      params = params,
      data = data,
    )

  def get(self,entity_type,Id='',limit=25,**kwargs):
    """ Returns an iterator over any matching entities to query within TargetProcess Project

    :param int entity_id: (Optional) If provided, return specific TargetProcess Entity
    :param int entity_max: (Optional) Max number of entities to return
    :param kwargs: extra keyword arguments to be passed as query args
    """
    assert entity_type in ENDPOINTS

    params = self.default_params.copy()
    params.update(kwargs)
    e = self._client.get_entities(
      entity_endpoint= '/'.join([entity_type,str(Id)]),
      params = params,
      return_limit = limit,
    )
    # if Id was specified, return single entity not iter
    if Id:
      return next(e)
    else: return e


class ProjectProxy(Query):
  """ Queries within specific project, automatically localises
  query gets to only include project entities via acid param 
  and auto inserts project entitiy into create data
  """
  def __init__(self, tp_client,project_entity):
    super(ProjectProxy,self).__init__(tp_client)
    # Can pass id or entity 
    self._entity = project_entity

  def setup_default_params(self):
    "Project queries require acid value as param"
    context = super(ProjectProxy,self).get(
      ids=self._entity.Id,entity_type='Context'
    )
    project_acid = next(context.__iter__()).Acid
    self.default_params['acid'] = project_acid    

  def get(self,entity_type,Id='',limit=25,**kwargs):
    # Lazily acquire acid value otherwise listing projects
    # would create too many requests
    if 'acid' not in self.default_params:
      self.setup_default_params()
    return super(ProjectProxy,self).get(entity_type,Id,limit,**kwargs)

  # Not sure if this is good idea yet...
  #def create(self,entity_type,data):
  #  if 'Project' not in data:
  #    data['Project'] = self._entity
  #  return super(ProjectProxy,self).create(entity_type,data)

  def __getattr__(self,name):
    "If attribute doesn't exist, look it up in wrapped entity object"
    entity = super(ProjectProxy,self).__getattribute__("_entity")
    return getattr(entity,name)

class TP(Query):
  def __init__(self, url, auth=None, tp_client=client.ObjectMappingClient,**kwargs):
    self._client = tp_client(url,client.HTTPRequestDispatcher())
    self._client.authenticate(auth)
    self.default_params = kwargs

  def get(self,entity_type,Id='',limit=25,**kwargs):
    "Extension to replace project entities with ProjectProxy"
    d = super(TP,self).get(entity_type,Id,limit,**kwargs)
    # Intercept projects and return Project proxy
    if entity_type == "Projects":
      if isinstance(d,collections.Iterator):
        d = itertools.imap(
          lambda entity: ProjectProxy(self._client,entity),d
        )
      else:
        d = ProjectProxy(self._client,d)
    return d
      


# OLD API 
def get_project(project_id, tp_url, auth=None):
  """The main entry point into api, returns a Project object
  which user can query,edit and create entities within a TargetProcess project

  :param project_id: the enitity ID of the target process project
  :param tp_url: url of target process api endpoint e.g targetprocess/api/v1
  :param auth: (Optional) Authentication object for service if require
  :return: :class: tp.Project 
  """
  # Create TPClient and Query interface
  tp_client = client.ObjectMappingClient(tp_url,client.HTTPRequestDispatcher())
  tp_client.authenticate(auth)
  project_entity = Query(tp_client).get('Projects',Id=project_id)
  return ProjectProxy(tp_client, project_entity)


