import client as tp
import utils
import entities
import functools, itertools, urllib

# API BEGINS 
class Query(object):
  """Adapter class for putting requests to TPClients
  """
  def __init__(self, tp_client):
    """
    :param tp.TPClient tp_client: TPclient object
    :param str project_acid: acid string of TargetProcess project:
    :param str entity_type: Name of desired TargetProcess Entity
    """
    self._client = tp_client
  
  def __call__(self,entity_type,method='get',*args,**kwargs):
    """ Main interface to query which will dispatch to correct method
    query('bugs',acid="")
    query('bugs',acid="",where="")
    query('bugs',10001',acid="")
    query('bugs',method="create",acid="",Name="",Description="")
    """
    return getattr(self,method)(entity_type,*args,**kwargs)

  def create(self,entity_type,**data):
    """Create a new entity within TargetProcess Project

    :param data: extra keyword argurments that are used to set entity properties 
    :return: tp.Response
    """
    resp = self._client.request(
      method = 'post',
      url = entity_type,
      data = data)
    return resp

  def get(self,entity_type,entity_id='',limit=25,**kwargs):
    """ Returns an iterator over any matching entities to query within TargetProcess Project

    :param int entity_id: (Optional) If provided, return specific TargetProcess Entity
    :param int entity_max: (Optional) Max number of entities to return
    :param kwargs: extra keyword arguments to be passed as query args
    :return: tp.Response
    """
    r = self._client.request(
      method = 'get',
      url = '/'.join([entity_type,str(entity_id)]),
      limit = limit,
      **kwargs)
    return r


class Project(object):
  """ Projects are Query Factories, setting up query instances 
  with desired client,acid_str and entity type via an attribute lookup interface
  """
  def __init__(self,project_acid,query_delegate):
    """
    :param tp.TPclient tp_client: TPclient object
    :param str project_acid: acid string of TargetProcess project:
    """
    self.project_acid = project_acid
    self.query_delegate = query_delegate

  def __getattr__(self,name):
    """ Provide a query interface within the context of a project and attribute look
        project.Bugs() => query(entity_type="Bugs",acid=self.project_acid ...
 
    """
    assert name in entities.ALL
    return functools.partial(self.query_delegate,entity_type=name,acid=self.project_acid)

def get_project(project_id, tp_url, auth=None):
  """The main entry point into api, returns a Project object
  which user can query,edit and create entities within a TargetProcess project

  :param project_id: the enitity ID of the target process project
  :param tp_url: url of target process api endpoint e.g targetprocess/api/v1
  :param auth: (Optional) Authentication object for service if require
  :return: :class: tp.Project 
  """
  # Create TPClient and Query interface
  tp_client = tp.TPEntityClient(tp_url)
  tp_client.authenticate(auth)
  query_delegate = Query(tp_client)
  
  # Create request to find out 'acid' value for given project
  context = query_delegate(ids=project_id,entity_type='Context')
  # NEED to implement better ux for single entity queries
  project_acid = next(context.__iter__()).Acid

  return Project(project_acid,query_delegate)


