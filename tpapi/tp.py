import json
import requests
import itertools

"""
Todo:
  - Create a bug usign lib
  - Client caching ??
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
  """simple  wrapper to encapsulate validation and keep client ignorant"""
  def __init__(self,auth=None):
    self.auth = auth

  def __call__(self,url,params,method='get'):
    response = requests.request(method,url,params=params,auth=self.auth)

    if not self.validate(response): raise Exception() # TODO:Better Excep
    return response.content # TODO: What about binary content???

  def validate(self,response):
    return response.status_code == requests.codes.ok    


class TPClient(object):
  'Takes questions and puts them to TP'
  
  ENTITIES = [
    'Bugs',
    'Tags',
    'Comments',
    'Userstories',
  ]  
  def __init__(self, url, auth=None, requester=HTTPRequester):

    self.BASEURL = url
    self.requester = requester(auth)

  def _request(self,method,url,response_parser=JSON,**params):
    """ base method to make request"""
    params['format'] = str(response_parser)
    response = response_parser(self.requester(url,params))
    return response

  def _entityUrl(self,entity_type,eid=''):
    url = '/'.join([self.BASEURL,
                    entity_type,
                    str(eid),])
    return url

  def query(self,entity_type,entity_max=50,
            create=False,edit=False,data=None,**kwargs):
    """ Makes suitable requests to TP Service based on args passed. 
    
    @param entity_type: TP entity to query
    @param id: (Optional) specific TP entity to query
    @param entity_max: (Optional) max number of entities returned, default 100

    Operational modes, defaults to query Mode 
    @param create: (Optional) IF true, create entity
    @param create: (Optional) If True, edit existing entity
    """
    if create and 'Id' in kwargs:
      raise Exception() # cannot create existing ID
    if edit and not 'Id' in kwargs:
      raise Exception() # Must edit existing ID
    if create and edit: 
      raise Exception() # Can't edit and create 

    url = self._entityUrl(entity_type,kwargs.pop('id',''))
    request_method = 'post' if (create or edit) else 'get'
    view = lambda: self._request('get', url, **kwargs)

    
    if request_method is 'post': # make request and return view of new elem
      i = self._request(request_method, url, **kwargs)[0][0]
      view = lambda: self._request(
                      'get', self._entityUrl(entity_type,i['Id']))

    # We return an iterator over requested data
    return ResponseIter(view, lambda url: self._request('get',url),
                        limit=entity_max) 

class ResponseIter(object):
  def __init__(self,init_response,next_f,limit):

    self.init_response = init_response
    self.limit = limit
    self.f_next = next_f

  def __iter__(self):
    """Merge result of all rquests as one iterator"""
    items,url = self.init_response()
    
    for i in range((self.limit/len(items))): #TODO: PROPER LIMIT DIV
      for x in items: yield x
      if url:
        items,url = self.f_next(url) # continue 
      else:
        break

  def __getitem__(self,index):
    if index > self.limit-1: raise Exception
    if index < 0: index = self.limit - index 

    return [x for x in self][index]


class Project(object):

  def __init__(self,acid,tp_client,entity):
    'todo: enity factory default'
    self.tp_client = tp_client
    self.project_acid = acid
    self.entity_factory = entity

  def __getattr__(self,name):
    'We delegate most of our work to tp_client'
    if name not in self.tp_client.ENTITIES:
       raise AttributeError()
    Entity_class = Entity(name)

    def get_wrapped_response(*args,**kwargs):
      'return entity based on query response(name+args)'
      response = self.tp_client.query(
                                entity_type = name, 
                                acid = self.project_acid,
                                *args, **kwargs )

      return (Entity_class(self,**dct) for dct in response)

    return get_wrapped_response


def Entity(name):
  return  globals().get(name,GenericEntity) 


class EntityBase(object):
  def __init__(self,project,**kwargs):
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
  Bug.create(client,12312)
  Bug(tp,1234).

  Project(tp,acid)

  # bugs is a method
  # it assumes id exists and fetches data
  Project.bugs('123123')
  Project.releases('1232')
  Project.userstories('44234')

  # its possible to create and edit as well as query. In this case,
  # pass create flag
  Project.bugs(create=1,Name='New Bug',Description='Blah')
  Project.bugs(edit=1,id=12312,Name='New Name')

  """ 
