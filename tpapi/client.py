import entities
import os 
import functools 
import itertools
import utils

"""
Future Todo:
  - Pass entity objects into edits
  - TP client caching
"""
DEFAULT_REQUESTER = utils.HTTPRequester(response_format = utils.JsonResponse())

class TPClient(object):
  """
  Interface to Target Process Rest API.
  Aims to returns a nicely parsed objects.
  """
  def __init__(self, url, requester=DEFAULT_REQUESTER):
    """
    :param url: url for tp api service
    :param requester: callable to delegate http request to
    """
    self.BASEURL = url
    self.requester = requester

  def authenticate(self,auth):
    "Replace requester delegate with authenicated one"
    self.requester = utils.HTTPRequester(
      response_format = utils.JsonResponse(), auth=auth)

  def _get_data(self, method, url, data, base=True, **params):
    "Deletegate response and return list of enitity dicts"
    final_url = os.path.join((self.BASEURL*base),url)
    return self.requester(method,final_url,params, data)

  def request(self, method, url, data=None, limit=50, **params):
    """
    Returns iterator over paginated response
    :return :class: tp.Response 
    """
    init = functools.partial(
      self._get_data,
      method = method,
      url = url,
      data = data,
      **params)
    next_f  = functools.partial(self._get_data,method='get',base=False,data=data)
    return EntityIter(init,next_f,limit)


class TPEntityClient(TPClient):
  def request(self,method,url,data=None,limit=50,**params):
    "Extend method to return list of entity instances"
    data = super(TPEntityClient,self).request(method,url,data,limit,**params)
    return itertools.imap(lambda dct: entities.EntityClassFactory(dct,self)(dct),data)


class EntityIter(object):
  """Iterator over an Entity list, transparently handles pagination of resources and 
  keeps entity data updated by resending http request per __iter__ call.

  You shouldn't need to directly instanciate, these are created and returned by the TPClient
  """
  def __init__(self,init_f,next_f,limit):
    """
    :param init_f: callback for initial url query
    :param next_f: callback for additional pagination urls
    :param limit: Max number of objects of entities to returned via iteration

    """
    self.init_response = init_f
    self.limit = limit
    self.next = next_f

  def __iter__(self):
    "TODO: improve limit implementation"
    item,url = self.init_response()
    limit = self.limit
    for x in range((self.limit/25)+1):
      for x in range(min(len(item),self.limit)):
        yield item[x]
      if len(item) < self.limit and url:
        limit = limit - len(item)
        item,url = self.next(url=url)
      else: break


