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
     
class QueryEntityWrapper(object):
  "Query Class Wrapper to transparently instanciate entitiy subclass"
  @classmethod
  def construct(cls,client,project,entity_type,entity_factory):
    'Convenience methods for partialing init'
    return cls(client,project,entity_type,entity_factory = entity_factory)

  def __init__(self,client,project,entity_type,
               entity_factory=EntityFactory,
               query_class=tp.Query):
    self._query = query_class(client,project,entity_type)
    self._client = client
    self._entity_class = entity_factory(entity_type)

  def __getattr__(self,name):
    'delegate to query methods else raise'
    if name in ['create','edit','query']:
      return functools.partial(self.__call__,method=name)
    else:
      raise AttributeError()

  def wrap(self,data):
    return self._entity_class(self._client,**data)

  def __call__(self,method,*args,**kwargs):
    """ call delegate method and wrap return """
    query = getattr(self._query,method)
    query_response = query(*args,**kwargs)
    if query_response:
      return itertools.imap(self.wrap, query_response)

class EntityQuery(tp.Query):
    def __init__(self,client,project,entity_type,
               entity_factory=EntityFactory):
      super(EntityQuery,self).__init__(self,client,project,entity_type)
      self._entity_class = entity_factory(entity_type)


# API BEGINS 
DEFAULT_ENTITY_FACTORY = EntityFactory(tp.GenericEntity)

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

  wrapped_query_class  = functools.partial(QueryEntityWrapper.construct,
    entity_factory=entity_factory)

  return tp.Project(client,project_acid,wrapped_query_class)


