import os 
import functools 
import utils

# Respons Formats
JSON = utils.JsonResponse()

"""
Todo:
  - Docs 
  - Tests Tests Tests 

  0.2
  - TP client caching
"""

class TPClient(object):
  'Takes questions and puts them to TP'
  def __init__(self, url, requester):
    self.BASEURL = url
    self.requester = requester 

  def _request(self, method, url, data=None,
              base=True, response_format=JSON, **params):
    """ Make single request """
    return self.requester(
      url = os.path.join((self.BASEURL*base),url) ,
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
    item,url = self.init_response()
    limit = self.limit
    for x in range((self.limit/25)+1):
      for x in range(min(len(item),self.limit)):
        yield item[x]
      if len(item) < self.limit and url:
        limit = limit - len(item)
        item,url = self.next(url)
      else: break


class Project(object):
  """ Projects are Query Factories, setup acid and client
  """
  def __init__(self,acid,tp_client,query_class):
    self.tp_client = tp_client
    self.project_acid = acid
    self._query = query_class

  def __getattr__(self,name):
    return self._query( self.tp_client,
                  self.project_acid,
                  entity_type=name)


class Query(object):
  "Interface class for client interaction"
  def __init__(self, client, project_acid, entity_type):
    self.entity_type = entity_type
    self._project_acid = project_acid
    self._client = client
  
  def _IDUrl(self,Id):
    return '/'.join([self.entity_type,str(Id)])

  def create(self,**data):
    resp = self._client.request(
      method = 'post',
      url = self.entity_type,
      data = data,
      acid = self._project_acid)
    return resp

  def edit(self,Id,**data):
    resp = self._client.request(
      method = 'post',
      url = self._IDUrl(Id),
      acid = self._project_acid,
      data = data)

  def query(self,Id='',entity_max=25,**kwargs):
    r = self._client.request(
      method = 'get',
      url = self._IDUrl(Id),
      acid = self._project_acid,
      limit=entity_max,
      **kwargs)
    return r


class EntityBase(object):
  def __new__(cls,*args,**kwargs):
    "Setup _tpdata before instance access controls"
    instance = super(EntityBase, cls).__new__(cls)
    super(EntityBase,instance).__setattr__('_tpdata',{})
    return instance 

  def __init__(self,project,**kwargs):
    if 'Id' not in kwargs:
      raise Exception() #TODO: Better exception
    self._project = project
    self._tpdata.update(kwargs)

  def __setattr__(self,name,val):
    if name in self._tpdata:
      self._tpdata[name] = val
    else:
      object.__setattr__(self,name,val)

  def __getattr__(self,name):
    if name in self._tpdata:
      return self._tpdata[name]
    else: 
      return AttributeError()

  def sync(self):
    """ post changes made entity to server """
    entitiy_id = self.Id
    data = self._tpdata.copy()
    data.pop('Id')
    getattr(self._project,'Assignables').edit(Id = entitiy_id,data=str(data))

  def __repr__(self):
    name = self.__class__.__name__
    return "{}({})".format(name,
    ",".join("{}={}".format(k,repr(v)) for k,v in self._tpdata.iteritems()))


class GenericEntity(EntityBase):
  pass

if __name__ == "__main__":
  pass
