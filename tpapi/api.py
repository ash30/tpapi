import tp, utils, entities
import functools, itertools 

# Helper classes
class DefaultEntityClassFactory(object):
  def __init__(self,extension_module=None,default_class=tp.GenericEntity):
    self.extension_module = extension_module
    self.default_class = default_class

  def __call__(self,name):
    if name not in entities.ALL:
      raise Exception() # Not a TP entity

    # Search for user defined class first
    # else return GenericEntity
    user_class = getattr(self.extension_module,name,None)
    if user_class:
      return user_class
    else:
      return self.default_class
     
class QueryEntityWrapper(object):
  @classmethod
  def construct(cls,entity_factory,*args,**kwargs):
    'Convenience methods for partialing init'
    return cls(entity_factory = entity_factory,*args,**kwargs)

  def __init__(self,client,project,entity_type,
               entity_factory=DefaultEntityClassFactory,
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
    query = getattr(self._query,method)
    query_response = query(*args,**kwargs)
    if query_response:
      return itertools.imap(self.wrap, query_response)

# API BEGINS 
def get_project(project_acid, tp_url, auth=None, 
                entity_factory=DefaultEntityClassFactory):
  """Entry point into API, returned Project object
     user can query for entities
  """
  client = tp.TPClient(tp_url,utils.HTTPRequester(auth))
  query = functools.partial(QueryEntityWrapper.create,
    entity_factory=entity_factory)

  return tp.Project(project_acid,client,query)
