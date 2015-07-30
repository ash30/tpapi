import functools
import requests

class TPClient(object):
  def __init__(self,url,auth,requester=requests.request):
    self.BASEURL = url
    self.requester = requester
    self.auth = auth

  def query(self,entity_id,entity_type,mode='query',**kwargs):
    'convert args to TP URL'
    url_args = ",".join(
      ["{}={}".format(k,v) for k,v in kwargs.iteritems()] )
    final_url = self.BASEURL + "{}/{}/?{}".format(
          entity_type,entity_id,url_args)

    return self._request(final_url,auth=self.auth)

  def _request(self,url,verb='get',*args,**kwargs):
    'make request to TP server'
    self.requester(verb,BASEURL+url,auth=self.auth,*args,**kwargs)


class Project(object):
  ENTITIES = [
    'bugs',
    'comments',
    'userstories',
  ]  

  def __init__(self,acid,tp_client):
    self.tp_client = tp_client
    self.project_acid = acid
    self.element_factory = Element

  def __getattr__(self,name):
    'We delegate most of our work to tp_client'
    if name not in self.ENTITIES: raise AttributeError()

    return functools.partial(
            self.tp_client.query,
            entity_type = name, acid= self.project_acid) 


class Entity(object):
  'Factory class for dynamic Entity Instanciation'

  ENTITY_CLASS_REGISTER={
    'bug':Bug
  }

  def __new__(cls,entity,response):
    'Here we switch based on entity type if known,'
    'Otherwise just return Generic Element'
    klass = cls.ENTITY_CLASS_REGISTER.get(entity,Generic)
    return klass.from_json(response)


class EntityBase(object):
  @classmethod 
  def from_json(cls,entity,json):
    'Its the Entities responsiblity to decode response'
    return cls(entity,**parse_json(json))

  def __init__(self,client,**kwargs):
    self._client = Client
    self._cache = kwargs

  def __getattr__(self,name):
    return self._cache.get('name',None)

class Generic(EntityBase):
  pass

class Bug(EntityBase):
  'Here is where we add entity specific methods'
  def Priority(self):
    pass # SHOULD BE PROPERTY

  def 

if __name__ == "__main__":
  """
  Bug.create(client,12312)
  Bug(tp,1234).

  # TP client is where we get the project item?
  tp = Client()  
  # Or we can create one by passing in project
  Project(tp,acid)
  
  # Preferred API, everything is based on projects,
  # So we query them in that context

  # bugs is a method
  # it assumes id exists and fetches data
  Project.bugs('123123')
  Project.releases('1232')
  Project.userstories('44234')

  # its possible to create as well as query. In this case,
  # pass create flag
  Project.bugs('12323',mode='create')
  Project.bugs(id=12312)
    return element instance()
    element is id + initial state() + methods to query/set

  Project.bugs(mode='create')
  Project.bugs(mode='query',id=)

  # its possible to query items
  Projects.query('bug',filter=ads,order)

  """ 
