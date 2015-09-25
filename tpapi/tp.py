import json
import itertools
import functools 
import requests
import entities 
from collections import namedtuple, OrderedDict

"""
Todo:
  - Commit Entity cacher, branch it off at this point
  - Tidy up this branch/ remove it 
  - Project has to take Entity Factory Callback
  - Default class factory
  - Make api to return a PROJECT with CLIENT setup
  - Make inital package setup, import api into package
  - Move entities list to class factory, move dependancy to api module

  - Tidy up Respnse parser
  - Docs 
  - Tests Tests Tests 

  0.2
  - entity editing
  - TP client caching
"""

class JsonResponse(object):
  """Simple wrapper to encapsulate reponse format"""
  def __call__(self,string):
    """Parse Response to return iterator of items and optional next url"""
    d = json.loads(string)
    return (d.get('Items',(d,)),d.get('Next'))
  def __str__(self):
    """String to supply to request format arg"""
    return 'json'

# Default Response Parser
JSON = JsonResponse()

class HTTPRequester(object):
  """simple wrapper around http request"""
  def __init__(self,auth=None):
    self.auth = auth

  def __call__(self, url, method='get', params=None, data=None, auth=None ):
    import pdb;pdb.set_trace()
    if method == 'get':
      response = requests.request(method,url,params=params,auth=auth)
    if method == 'post':
      response = requests.request(method,url,params=params,auth=auth,
                   **self._payload(data))

    response.raise_for_status()
    return response.content # TODO: What about binary content???

  def _payload(self,data):
    dump = json.dumps(data)
    return {
      'data':dump,
      'header': {"content-type":"application/json",
                 "content-length":len(dump)}}

class TPClient(object):
  'Takes questions and puts them to TP'
  ENTITIES = entities.ALL

  def __init__(self, url, auth=None, requester=HTTPRequester):
    self.BASEURL = url
    self.requester = functools.partial(requester(),auth=auth)

  def __request(self, method, url, data=None,
              base=True, response_parser=JSON, **params):

    params['format'] = str(response_parser)
    resp = self.requester(
      url = (self.BASEURL*base) + url ,
      method = method,
      params = params, 
      data = data)
    return resp

  def request(self,method,url,data=None,limit=50,**params):
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
  def __init__(self,init_f,next_f,limit,parser=JSON):
    self.parser = parser
    self.init_response = init_f
    self.limit = limit
    self.next = next_f

  def __iter__(self):
    """Merge result of all rquests as one iterator"""
    items,url = self.parser(self.init_response())
    for i in range(max(self.limit/len(items),1)):
      if i==0: # Special case start 
        pass # already assigned 
      else:
        items,url = self.parser(self.next(url))
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
