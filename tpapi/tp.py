import itertools
import functools 
import entities 
import utils

# Respons Formats
JSON = utils.JsonResponse()

"""
Todo:
  - Project has to take Entity Factory Callback
  - Default class factory
  - Move entities list to class factory, move dependancy to api module

  - Docs 
  - Tests Tests Tests 

  0.2
  - entity editing
  - TP client caching
"""

class TPClient(object):
  'Takes questions and puts them to TP'
  ENTITIES = entities.ALL

  def __init__(self, url, auth=None, requester=HTTPRequester):
    self.BASEURL = url
    self.requester = functools.partial(requester(),auth=auth)

  def _request(self, method, url, data=None,
              base=True, response_format=JSON, **params):
    """ Make single request """
    return self.requester(
      url = (self.BASEURL*base) + url ,
      method = method,
      format = response_format,
      params = params, 
      data = data)

  def request(self,method,url,data=None,limit=50,**params):
    """ Return iterator over mutli request response """
    init = functools.partial(
                self.__request,
                method = method,
                url = url,
                params = params,
                data = data)
    next_f  = functools.partial(self.request,method='get',base=False)
    return Response(init,next_f,limit)


class Response(object):
  """ Seamless Iter over Response to a query """
  def __init__(self,init_f,next_f,limit):
    self.init_response = init_f
    self.limit = limit
    self.next = next_f

  def __iter__(self):
    """Merge result of all rquests as one iterator"""
    items,url = self.init_response()
    for i in range(max(self.limit/len(items),1)):
      if i==0: # Special case start 
        pass # already assigned 
      else:
        items,url = self.next(url)
      for x in items:yield x 

class Project(object):
  """ Projects are Query Factories, setup acid and client
  """
  def __init__(self,acid,tp_client):
    self.tp_client = tp_client
    self.project_acid = acid

  def __getattr__(self,name):
    if name not in self.tp_client.ENTITIES:
       raise AttributeError()
    return Query(self.tp_client,self.project_acid,entity_type=name)


class Query(object):
  def __init__(self, client, project_acid, entity_type):
    self.entity_type = entity_type
    self.entity_class = Entity(self.entity_type)
    self._project_acid = project_acid
    self._client = client

  def create(self,**data):
    resp = self._client.request(
      method = 'post',
      url = self.entity_type,
      data = data,
      acid = self._project_acid)
    r = itertools.imap(lambda x :self.entity_class(self._client,**x),r)
    return self.entity_class(self._client,**(next(r)))

  def query(self,Id='',entity_max=25,**kwargs):
    r = self._client.request(
      method = 'get',
      url = '/'.join([self.entity_type,str(Id)]),
      acid = self._project_acid,
      limit=entity_max,
      **kwargs)
    r = itertools.imap(lambda x :self.entity_class(self._client,**x),r)

    # If id just return the 1 and only instance, else return iter 
    if id: return next(r)
    else: return r 

def Entity(name):
  return  globals().get(name,GenericEntity) 

class EntityBase(object):
  def __init__(self,project,**kwargs):
    if 'Id' not in kwargs:
      raise Exception() #TODO: Better exception

    self._project = project
    self._cache = kwargs

  def __getattr__(self,name):
    return self._cache.get(name,None)

  def __repr__(self):
    name = self.__class__.__name__
    return "{}({})".format(name,
    ",".join("{}={}".format(k,repr(v)) for k,v in self._cache.iteritems()))

  def getComments(self):
    pass     

class GenericEntity(EntityBase):
  pass

class Bugs(EntityBase):
  'Here is where we add entity specific methods'
  def Priority(self):
    pass # SHOULD BE PROPERTY


if __name__ == "__main__":
  """
  client = TPClient(url,auth)
  Project = (tp,acid)

  Project.bugs.create(Name,Description)
  bug = Project.bugs.query(id=12311)
  bug.Name = "New Name" # editing

  Project.tags.query()
  Project.tags.create(Name=Name)
  """ 
