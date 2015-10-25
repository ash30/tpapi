import json, urllib
import requests
from collections import namedtuple

# RESPONSE FORMATS
TP_RESPONSE = namedtuple('TPResponse',['Items','NextUrl'])

class JsonResponse(object):
  """Simple wrapper to encapsulate reponse format"""
  def __call__(self,response):
    """Parse Response to return iterator of items and optional next url"""
    d = response.json()
    return TP_RESPONSE(d.get('Items',(d,)),d.get('Next'))
  def __str__(self):
    """String to supply to request format arg"""
    return 'json'

class BinaryResponse(object):
  pass # For times when downloading images etc

# HTTP Work
class HTTPRequester(object):
  def __init__(self,auth=None):
    self.auth = auth

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
    return "?" + urllib.quote(param_string,safe='=&')

  def __call__(self, url, response_format, method='get', params='', data=None ):
    # TODO: Remove param default, its provided up stream
    if params:
      # if params aren't specified and included in url
      # we assume format is already included and do not add 
      # Only TP generated urls will have no params as any basic request
      # will need to specify an acid value 
      params = self._encode_params(params) + "&" + "format=%s" % str(response_format) # Add Format class to http args
    else:
      params = ''

    print url+params

    if method == 'get':
      response = requests.request(method,url+params,auth=self.auth)
    if method == 'post':
      response = requests.request(method,url+params,auth=self.auth,
                   **self._payload(data))

    response.raise_for_status()
    return response_format(response)

  def _payload(self,data):
    dump = json.dumps(data,default=lambda o:o.toDict())
    return {
      'data':dump,
      'header': {"content-type":"application/json",
                 "content-length":len(dump)}}
