import os 
import functools 
import utils

"""
Future Todo:
  - Pass entity objects into edits
  - TP client caching
"""

class EntityResponse(utils.JsonResponse):
  def __init__(self,entity_factory):
      self.entity_factory = entity_factory

  def __call__(self,response):
    items,url = super(EntityResponse,self).__call__(response)
    new_items = [self.entity_factory(i.get('ResourceType','NOENTITYTYPE'))(**i) for i in items]
    return (new_items,url)


class TPClient(object):
  'Takes questions and puts them to TP'
  def __init__(self, url, requester):
    self.BASEURL = url
    self.requester = requester

  def _simple_request(self, method, url, data, params,
                           base=True):
    "Construct request and delegate to requester"
    final_url = os.path.join((self.BASEURL*base),url)

    return self.requester(
      method = method,
      url = final_url ,
      params = params,
      data = data,)

  def request(self, method, url, data=None, limit=50,**params):
    """
    Returns iterator over paginated response
    :return :class: tp.Response 
    """
    init = functools.partial(
                self._simple_request,
                method = method,
                url = url,
                params = params,
                data = data)
    next_f  = functools.partial(self._simple_request,method='get',params={},base=False)
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

