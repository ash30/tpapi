import os 
import functools 
import utils

# Respons Formats
JSON = utils.JsonResponse()

"""
Future Todo:
  - Pass entity objects into edits
  - TP client caching
"""

class TPClient(object):
  'Takes questions and puts them to TP'
  def __init__(self, url, requester):
    self.BASEURL = url
    self.requester = requester 

  def _request(self, method, url, params,  data=None,
              base=True, response_format=JSON):
    """ Make single request """
    return self.requester(
      url = os.path.join((self.BASEURL*base),url) ,
      method = method,
      response_format = response_format,
      params = params, 
      data = data)

  def request(self,method,url,data=None,limit=50,**params):
    """ Return iterator over multi request response """
    init = functools.partial(
                self._request,
                method = method,
                url = url,
                params = params,
                data = data)
    next_f  = functools.partial(self._request,method='get',params={},base=False)
    return Response(init,next_f,limit)


class Response(object):
  """Iterator over an Entity list.
  ransparently handles pagination of resources and 
  keeps enitity data up todate by resending http request on iter
  """
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
        item,url = self.next(url=url)
      else: break


class Query(object):
  """Adapter class for putting requests to TPClients

  """
  def __init__(self, tp_client, project_acid, entity_type):
    """
    :param tp.TPClient tp_client: TPclient object
    :param str project_acid: acid string of TargetProcess project:
    :param str entity_type: Name of desired TargetProcess Entity
    """
    self.entity_type = entity_type
    self._project_acid = project_acid
    self._client = tp_client
  
  def _IDUrl(self,entity_id):
    'return entity specific url'
    return '/'.join([self.entity_type,str(entity_id)])

  def create(self,**data):
    """Create a new entity within TargetProcess Project

    :param data: extra keyword argurments that are used to set entity properties 
    :return: tp.Response
    """
    resp = self._client.request(
      method = 'post',
      url = self.entity_type,
      data = data,
      acid = self._project_acid)
    return resp

  def edit(self,entity_id,**data):
    """Edits the properties of an exisitng entity within TargetProcess Project

    :param int entity_id: The id of entity
    :param data: extra keyword argurments that are used to set entity properties 
    :return: tp.Response
    """
    resp = self._client.request(
      method = 'post',
      url = self._IDUrl(entity_id),
      acid = self._project_acid,
      data = data)

  def query(self,entity_id='',entity_max=25,**kwargs):
    """ Returns an iterator over any matching entities to query within TargetProcess Project

    :param int entity_id: (Optional) If provided, return specific TargetProcess Entity
    :param int entity_max: (Optional) Max number of entities to return
    :param kwargs: extra keyword arguments to be passed as query args
    :return: tp.Response
    """
    r = self._client.request(
      method = 'get',
      url = self._IDUrl(entity_id),
      acid = self._project_acid,
      limit=entity_max,
      **kwargs)
    return r


class EntityBase(object):
  def __new__(cls,*args,**kwargs):
    "Setup _tpdata before instance access controls"
    instance = object.__new__(cls)
    super(EntityBase,instance).__setattr__('_tpdata',{})
    return instance 

  def __init__(self,project,Id,**kwargs):
    # Every Entity requires a project and ID
    self._project = project
    self._tpdata['Id'] = Id
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

  def toDcit(self):
    return self._tpdata

  def __repr__(self):
    name = self.__class__.__name__
    return "{}({})".format(name,
    ",".join("{}={}".format(k,repr(v)) for k,v in self._tpdata.iteritems()))


class GenericEntity(EntityBase):
  pass

if __name__ == "__main__":
  pass
