import requests
import functools

class TPClient(object):
  def __init__(self,url):
    self.URL = url

  def _request(self):
    pass

  def get(self):
    pass

  def post(self):
    pass

class Project(object):
  def __init__(self,acid,tp_client,element_factory):
    self.tp_client = tp_client
    self.project_acid = acid
    self.element_factory = element_factory

  def __query(self,element_name,mode='query',**kwargs):
    self.tp_client._request(element_name,
                                   project=self._acid, 
                                   verb='get', **kwargs)  

  def __getattr__(self,element_name):
    'We delegate most of our work to tp_client'
    return functools.partial(self.__query, element_name = element_name) 


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

  tp = Client()  
  Project(tp,acid)

  Project.bugs('123123')
  Project.releases('1232')
  Project.userstories('44234')

  Project.bugs('12323',mode='create')
  Project.bugs(id=12312)
    return element instance()
    element is id + initial state() + methods to query/set

  Project.bugs(mode='create')
  Project.bugs(mode='query',id=)
  Projects.query('bug',filter=ads,order)

   
