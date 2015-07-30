import functools
import requests

class TPClient(object):
  def __init__(self,url,auth,requester=requests.request):
    self.BASEURL = url
    self.requester = requester
    self.auth = auth

  def request(self,url,verb='get',*args,**kwargs):
    self.requester(verb,BASEURL+url,auth=self.auth,*args,**kwargs)


class Project(object):
  def __init__(self,acid,tp_client):
    self.tp_client = tp_client
    self.project_acid = acid
    self.element_factory = Element

  def __query(self,entity,entity_id,mode='query',**kwargs):
    # Takes args and creates query object which in turn is fed to tpClient
    query = Query(entity,entity_id,mode,**kwargs)
    response = self.tp_client.request(str(query))
    return self.element_factory.from_json(entity,response)

  def __getattr__(self,name):
    'We delegate most of our work to tp_client'
    return functools.partial(self.__query, entity = name) 

class Query():
  # Here is where we model query rules 
  # e.g if No ID, must be in 'create' mode
  def __new__(cls,*args,**kwargs):
    if cls.validate(*args,**kwargs):
      return cls(*args,**kwargs)
    else:
      raise Exception()

  def __init__(self,entity,verb

  def __str__(self):
    return "query as tpurl string"  

  @class_method
  def validate(self,*args,**kwargs):
    pass


class Element(object):
  @staticmethod 
  def from_json(cls,json):
    return cls(**parse_json(json))

  def __new__(cls,element,**kwargs):
    return new element!!!


class ElementBase(object):
  def __init__(self,client,**kwargs):
    self._client = Client
    self._cache = kwargs

  def __getattr__(self,name):
    return self._cache.get('name',None)





if __name__ == "__main__":
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

   
