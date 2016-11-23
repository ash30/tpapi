import os 
import json
import itertools
import urllib
import requests
import entities
import collections 

"""
Future Todo:
  - Pass entity objects into edits
  - TP client caching
"""
# Utils # 
def is_sequence(elem):
  "Returns true for iterables other than strings"
  if isinstance(
    elem,collections.Sequence
  ) and not isinstance(elem,basestring):
      return True
  else: return False

def encode_sequence(seq):
  return ','.join([str(x) for x in seq])

# Response formats # 
class TPJsonResponseFormat(object):
  def parse(self,response_object):
    return response_object.json()
  def __str__(self):
    return "json"

class TPEntityResponseFormat(TPJsonResponseFormat):
  def parse(self,response_object):
    d = super(TPEntityResponseFormat,self).parse(
      response_object
    )
    return (d.get('Items',(d,)),d.get('Next'))

# HTTP layer # 
class HTTPRequestDispatcher():
  """
  A simple component wrapper over request.py functionality
  takes care of sending the http requests and can be easily
  mocked out for overall testing of the library
  """
  def __init__(self,response_format=TPEntityResponseFormat):
    self.auth = None
    self._default_response_format = response_format()
    self._requests = requests # for mocking

  def encode_params(self,params):
    """ Override default requests.py param data 
    serialisation to suit TP 
    """
    final_params = { 
      k:encode_sequence(v) if is_sequence(v) else str(v)
      for k,v in params.iteritems() if v
    }
    param_string = "&".join(
      ["{}={}".format(k,v) for k,v in final_params.iteritems()]
    )
    return urllib.quote(param_string,safe='=&,')

  def append_params(self,url,params):
    "Combine params and url into single string"
    final_url = "{}{}{}".format(
      url,
      "?" if "?" not in url else "&",
      self.encode_params(params),
    )
    return final_url
  
  def make_request(self,method,url,params,response_format,**kwargs):
    params['format'] = response_format
    final_url = self.append_params(url,params)
    print final_url
    r = self._requests.request(method,final_url,auth=self.auth,**kwargs)
    try:
      r.raise_for_status()
    except:
      print "ERROR",final_url
      print r.content
      raise
    return response_format.parse(r)

  def single_get_request(self,url,params,response_format=None):
    if not response_format: 
      response_format = self._default_response_format
    "Submit a get request to tp api endpoint"
    return self.make_request('get',url,params,response_format)

  def paginated_get_request(self,url,params):
    """ Generator over a series of requests inorder 
    to capture paginated resources
    """
    response,next_url = self.single_get_request(url,params)

    assert isinstance(
      response, collections.Sequence
    ), "Error: Paginated Requests assume iterable response"

    yield response
    while next_url:
      response,next_url = self.single_get_request(next_url,params={})
      yield response
    
  def post_request(self,url,params,message_body,response_format=None):
    if not response_format: 
      response_format = self._default_response_format
    encoded_message = json.dumps(message_body)
    headers = {
      "content-type":"application/"+str(response_format),
      "content-length":len(encoded_message)
    }
    return self.make_request(
      'post',url,params,response_format=response_format,
      headers=headers,data=encoded_message
    )
     

# Clients # 
class BasicClient(object): 
  """
  Submits reqests to TP and returns data

  The two main use cases for this class:
  api endpoints created from user queries
  api endpoints required for entity data and construction

  a deprecated third case used to be absolute url 
  endpoints for pagination but this functionality 
  has been moved to the requester level
  """
  def __init__(self,url,requester):
    self.requester = requester
    self.tp_api_url = url

  def authenticate(self,auth):
    "Replace requester delegate with authenicated one"
    self.requester.auth = auth 

  def raw_request(self,url,params={},response_format=TPJsonResponseFormat):
    "Mainly used to return raw response"
    final_url = '/'.join([self.tp_api_url,url])
    return self.requester.single_get_request(
      final_url,params,response_format())

  # SHOULD WE LEAVE PARAMS AS {}?
  def get_entities(self,entity_endpoint,params={},return_limit=50):
    """
    @params entity_endpoint: 
      can any of the following <entity type> ,
      <entity type>/<id>, <entity type>/<id>/<collection>
    """
    
    assert isinstance(return_limit,int) and return_limit > 0,\
      "return limit should be non negative integer"

    final_url = '/'.join([self.tp_api_url,entity_endpoint])
    return itertools.islice(
      itertools.chain.from_iterable(
        self.requester.paginated_get_request(final_url,params)
      ),
      0, return_limit
    )

  def create_entity(self,entity_endpoint,data,params={}):
    "Create Entity given a dict of attributes"
    # The base client creation does no error checking on uploaded data
    final_url = '/'.join([self.tp_api_url,entity_endpoint])
    new_entity= self.requester.post_request(
      final_url,params,data,
      response_format = TPJsonResponseFormat(),
    )
    return new_entity


class ObjectMappingClient(BasicClient):
  """ Extends the basic client to auto instanciate 
  entitiy classes from data
  """
  def __init__(
    self,url,requester,
    entity_class_factory=entities.EntityClassFactory
  ):
    super(ObjectMappingClient,self).__init__(url,requester)
    self.entity_class_factory = entity_class_factory(self)

  def get_entities(self,entity_endpoint,params={},return_limit=50):
    "Extend method to return list of entity instances"
    entity_data = super(TPEntityClient,self).get_entities(
      entity_endpoint,params,return_limit
    )
    if not entity_data: return [] # guard
    # THIS DOESN'T WORK AS I SLICE WILL BE TRUE

    resource_type_hint = entity_endpoint.split('/')[0]
    entity_class = self.entity_class_factory.get(resource_type_hint,immutable=True)

    return itertools.imap(
      lambda n:entity_class(n), entity_data
    )

  def create_entity(self,entity_endpoint,data,params={}):
    "Create Entity given a dict of attributes"
    # Create a local mutable entity to check data 
    entity_class =  self.entity_class_factory.get(
      entity_endpoint,
      immutable = True,
    )
    mutable_entity_class =self.entity_class_factory.get(
      entity_endpoint,
      immutable = False,
    )
    proposed_entity = mutable_entity_class.create_from_data(data)
    msg_content = proposed_entity.toDict()
    msg_content.pop('Id',None) # No ID for creation!

    # Send request and return resultant entity
    dct = super(ObjectMappingClient,self).create_entity(
      entity_endpoint,msg_content,params
    )
    return entity_class(dct)


# Aliases for backwards compatability
TPEntityClient = ObjectMappingClient
