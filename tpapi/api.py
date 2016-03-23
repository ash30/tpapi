import client, utils, entities
import functools, itertools, urllib

# API BEGINS 
DEFAULT_ENTITY_FACTORY = entities.EntityFactory(entities.GenericEntity)

class Project(object):
  """ Projects are Query Factories, setting up query instances 
  with desired client,acid_str and entity type via an attribute lookup interface
  """

  def __init__(self,tp_client,project_acid):
    """
    :param tp.TPclient tp_client: TPclient object
    :param str project_acid: acid string of TargetProcess project:
    """
    self.tp_client = tp_client
    self.project_acid = project_acid

  def __getattr__(self,name):
    """
    :raise: EntityNameError if name doesn't match valid TargetProcess Entity
    """
    # I wish there was a more efficent way to do this...
    # Keep dot notation for entity type but not create Query per method call
    if name not in entities.ALL:
      raise EntityNameError() 

    return client.Query(self.tp_client,
                    self.project_acid,
                    entity_type = name)

def get_project(project_id, tp_url, auth=None, 
                entity_factory=DEFAULT_ENTITY_FACTORY):
  """The main entry point into api, returns a Project object
  which user can query,edit and create entities within a TargetProcess project

  :param project_id: the enitity ID of the target process project
  :param tp_url: url of target process api endpoint e.g targetprocess/api/v1
  :param auth: (Optional) Authentication object for service if require
  :param entity_factory: (Optional) Callable that will be passed 
    the entity type and expected to return sub class of tp.EntityBase.
    User can overide this in order to customise instanciation of TP Entity,
    By default we return tp.GenericEntity instances 
  :return: :class: tp.Project 
  """
  requester = utils.HTTPRequester(
    tp.EntityResponse(entity_factory),auth,
  )
  client = tp.TPClient(tp_url,requester)
  context = tp.Query(client,project_acid=None,entity_type='Context').query(ids=project_id)
  # NEED to implement better ux for single entity queries
  project_acid = next(context.__iter__()).Acid

  return Project(client,project_acid)


