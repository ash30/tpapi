import tp, utils, entities
import functools, itertools, urllib

# Exception
class EntityNameError(Exception): pass 

# Helper classes
class EntityFactory(object):
  """Default implementation of Entity Class Factory,
    When called, will instanciate tp.GenericEntity sub class based on entity string"""

  def __init__(self,default_class,extension_module=None):
    """
    :param default_class: Default class to return if 
      name doesn't exist in extension_module
    :param extension_module: (Optional) 
      getattr(extension_module,type) should return desired sub class
    """
    self.extension_module = extension_module
    self.default_class = default_class

  def __call__(self,name):
    """Looks up class name in extension module and returns class, else 
    returns default class 

    :param name: name of Target Process Entity
    :return: tp.GenericEntity sub class
    :raise: EntityNameError if name doesn't match valid TargetProcess Entity
    """
    if name not in entities.ALL:
      raise EntityNameError() 

    # Search for user defined class first
    # else return GenericEntity
    user_class = getattr(self.extension_module,name,None)
    if user_class:
      return user_class
    else:
      return self.default_class
     

class EntityQuery(tp.Query):
  "Query subclass that returns response as Entities"
  class QueryIter(object):
    def __init__(self,data,entity_class):
      self.data = data
      self.entity_class = entity_class
    def __iter__(self):
      for x in self.data:
        yield self.entity_class(x)

  def __init__(self,client,project_acid,entity_type,entity_class):
    super(EntityQuery,self).__init__(client,project_acid,entity_type)
    self.entity_class = entity_class

  def query(self,entity_id='',entity_max=25,**kwargs):
    response = super(EntityQuery,self).query(entity_id,entity_max,**kwargs)
    return self.QueryIter(response,self.entity_class)

  def create(self,**data):
    response = super(EntityQuery,self).create(**data)
    return self.entity_class([x for x in response][0])

# API BEGINS 
DEFAULT_ENTITY_FACTORY = EntityFactory(tp.GenericEntity)

class Project(object):
  """ Projects are Query Factories, setting up query instances 
  with desired client,acid_str and entity type via an attribute lookup interface

  The attribute string is identical to the TargetProcess reference documentation
  so be aware of capitalisation.

  Usage::
    >>> proj = Project(acid,client)
    >>> proj.Bugs
    >>> proj.Userstories
  """

  def __init__(self,tp_client,project_acid,entity_factory,query_class=EntityQuery):
    """
    :param tp.TPclient tp_client: TPclient object
    :param str project_acid: acid string of TargetProcess project:
    """
    self.tp_client = tp_client
    self.project_acid = project_acid
    self.entity_factory = entity_factory
    self._query = query_class

  def _create_entity(self,data,entity_type):
    return self.entity_factory(entity_type)(self,**data)

  def __getattr__(self,name):
    return self._query( self.tp_client,
                  self.project_acid,
                  entity_type = name,
                  entity_class = functools.partial(self._create_entity,entity_type=name))


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
  client = tp.TPClient(tp_url,utils.HTTPRequester(auth))
  context = tp.Query(client,project_acid=None,entity_type='Context').query(ids=project_id)
  project_acid = next(context.__iter__())['Acid']

  return Project(client,project_acid,entity_factory)


