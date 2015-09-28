import json
import requests
from collections import namedtuple

# RESPONSE FORMATS
TP_RESPONSE = namedtuple('TPResponse',['Items','NextUrl'])

class JsonResponse(object):
  """Simple wrapper to encapsulate reponse format"""
  def __call__(self,response):
    """Parse Response to return iterator of items and optional next url"""
    d = response.json
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

  def __call__(self, url, response_format, method='get', params=None, data=None, auth=None ):
    params['format'] = str(response_parser) # Add Format class to http args

    if method == 'get':
      response = requests.request(method,url,params=params,auth=auth)
    if method == 'post':
      response = requests.request(method,url,params=params,auth=auth,
                   **self._payload(data))

    response.raise_for_status()
    return response_format(response)

  def _payload(self,data):
    dump = json.dumps(data)
    return {
      'data':dump,
      'header': {"content-type":"application/json",
                 "content-length":len(dump)}}
