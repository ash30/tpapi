import json
import urllib
import requests
from collections import namedtuple

class JsonResponse(object):
  """Simple wrapper to encapsulate reponse format"""
  def __call__(self,response):
    """Parse Response to return iterator of items and optional next url"""
    d = response.json()
    # Return tuple of items + url for next request
    return (d.get('Items',(d,)),d.get('Next'))
  def __str__(self):
    """String to supply to request format arg"""
    return 'json'

class BinaryResponse(object):
  pass # For times when downloading images etc

# HTTP Work
class HTTPRequester(object):
  def __init__(self,response_format,auth=None):
    self.auth = auth
    self.default_response_format = response_format

  def __call__(self,method,url,params=None,data=None,response_format=None):
    if not response_format:
      response_format = self.default_response_format
    if not params:
      params = dict()
    if "format=" not in url:
      params['format'] = str(response_format)

    params_str = self._encode_params(params) 
    final_url = url + ('?' if '?' not in url else '&') + params_str

    #Dispatch to correct request
    assert method == 'get' or 'post'
    response = self.__getattribute__(method)(final_url,self._payload(data))
    try:
      response.raise_for_status()
    except:
      print final_url
      raise

    return response_format(response)
  
  def get(self,url,data):
    return requests.request('get',url,auth=self.auth)

  def post(self,url,data):
    return requests.request('post',url,auth=self.auth,**data)

  def _payload(self,data):
    if not data: return {}
    dump = json.dumps(data,default=lambda o:o.toDict())
    return {
      'data':dump,
      'headers': {"content-type":"application/json",
                 "content-length":len(dump)}}

  def _encode_params(self,params):
    # Transfer param data into query string as requests.py
    # implementation isn't quite the right fit.

    # Filter Current
    result = {}
    for k,v in params.iteritems():
      if not v: 
        continue    
      if hasattr(v,'__iter__'):
        result[k] = "[%s]"%",".join([str(x) for x in v])
      else:
        result[k]=v

    # Return quoted/escaped query string
    param_string ="&".join(["%s=%s"%(k,v) for k,v in result.iteritems()])
    return urllib.quote(param_string,safe='=&')
