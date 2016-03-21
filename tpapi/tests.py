import unittest, functools
from collections import namedtuple
import tp,api,entities,utils

# MOCKS
class MockCallable(object):
  fcall = namedtuple('fcall',['args','kwargs'])
  def __init__(self,response=None):
    self.last_call = None
    self.response = response
  def __call__(self,*args,**kwargs):
    self.last_call = self.fcall(args,kwargs)
    return self.response

class MockObject(object):
  def __init__(self,**kwargs):
    self.__dict__.update(kwargs)

# TP TESTS
class TPClientTests(unittest.TestCase):
  "Test baseurl behaviour + it creates correct Response instances"
  def test_url_has_base(self):
    mock_requestor = MockCallable(response=[[{'Id':1},{'Id':2},{'Id':3}],None])
    base_url       = 'www.baseurl.com'
    client         = tp.TPClient(base_url,mock_requestor,)
  
    # has base class by default
    client._simple_request('get',url='bugs',params={},data=None)
    self.assertEqual( 
      mock_requestor.last_call.kwargs.get('url'),base_url+'/bugs')

    client._simple_request('get',url='bugs',base=False,params={},data=None)
    self.assertEqual(
      mock_requestor.last_call.kwargs.get('url'),'bugs')

  def test_correctReponse(self):
    pass


class ResponseTests(unittest.TestCase):
  "Response class have to validate continual iter over + limits"

  def create_iter(self,init,limit):
    response = tp.Response(init,lambda url:url,limit)
    return [ x for x in response]

  def test_simpleIter(self):
    'Given response of list of items, no url, just iter items'
    r = lambda: (range(10),None)
    result = self.create_iter(r,limit=100)
    self.assertEqual(len(result),len(range(10)))

  def test_simpleIterLong(self):
    'Given long list of items, no url, just iter items'
    r = lambda: (range(99),None)
    result = self.create_iter(r,limit=100)
    self.assertEqual(len(result),len(range(99)))

  def test_simpleIterLimit(self):
    'Given long list of items, no url, just iter items until limit'
    r = lambda: (range(99),None)
    result = self.create_iter(r,limit=50)
    self.assertEqual(len(result),50)

  def test_urlIter(self):
    'Given url,iter will continue over next list of items'
    r =  lambda: (range(10),(range(10),None))
    result = self.create_iter(r,limit=100)
    self.assertEqual(len(result),20)

  def test_urlIterTwice(self):
    'Given 2 urls, iter will continue'
    r =  lambda: (range(10),(range(10),(range(10),None)))
    result = self.create_iter(r,limit=100)
    self.assertEqual(len(result),30)

  def test_urlIterLimit(self):
    'Regardless of urls, iter will stop at limi'
    r =  lambda: (range(10),(range(10),(range(10),None)))
    result = self.create_iter(r,limit=5)
    self.assertEqual(len(result),5)


class QueryTests(unittest.TestCase):
  """Query Tests only have to validate correct use of client as
  Query class is really just an adapter over client
  """  
  def setUp(self):
    "create a mock client"
    self.mock_client = MockObject(
      request=MockCallable(response=[]),
      _simple_request=MockCallable(response=[]),
    )

  def test_queryQueryMethod(self):
    query = tp.Query(self.mock_client,'acid','entity')
    call = query.query()
    self.assertTrue(
      self.mock_client.request.last_call.kwargs['url'].startswith('entity'))

  @unittest.skip('Feature needs reworking, not latest version')
  def test_queryEditMethod(self):
    query = tp.Query(self.mock_client,'acid','entity')
    call = query.edit(entity_id=123)
    self.assertTrue(
      self.mock_client.request.last_call.kwargs['url'].startswith('entity'))

  def test_queryCreateMethod(self):
    query = tp.Query(self.mock_client,'acid','entity')
    call = query.create()
    self.assertTrue(
      self.mock_client._simple_request.last_call.kwargs['url'].startswith('entity'))

  def test_queryID(self):
    "Query submits entity+id to client call"
    query = tp.Query(self.mock_client,'acid','entity')
    self.assertEqual(query._IDUrl(123),'entity/123')

# ENTITIES TESTS
class EntityBaseTests(unittest.TestCase):
  class mock_object(object):
    def __init__(self,**kwargs):
      self.__dict__.update(kwargs)
  
  def test_getattr_Tpdata(self):
    'I can retrieve value from TP data cache'
    i = entities.EntityBase(Id=123,data1='a',data2=1,data3=[1,2])
    self.assertEqual(i.data1,'a')
    self.assertEqual(i.data2,1)
    self.assertEqual(i.data3,[1,2])
  
  def test_getattr_InstanceVar(self):
    'I can retrieve standard variable from instance'
    i = entities.EntityBase(Id=123, data1='a',data2=1,data3=[1,2]) 
    self.assertEqual(i.Id,123 )

  """ Currently not needed
  def test_getattr_shadowing(self):
    'If name exists in tpdata and instance, get instance'
    i = entities.EntityBase(Id=123)
    self.assertTrue('_project' in i._tpdata)
  """

  def test_setattr_Tpdata(self):
    'I can edit tpdata cache ref'
    i = entities.EntityBase(Id=123,data1='a')
    i.data1 = 'b'
    self.assertEqual(i.data1,'b')
    self.assertEqual(i._tpdata['data1'],'b')

  def test_setattr_InstanceVar(self):
    'I can modify normally instance ref'
    i = entities.EntityBase(Id=123,data1='a')
    i._project = 'new_project'
    self.assertEqual(i._project, 'new_project')
    self.assertEqual(i.__dict__['_project'],'new_project')

  @unittest.skip('Feature needs reworking, not latest version')
  def test_sync(self):
    'I can send copy of tp data to update client'
    # To be sucessful, cls needs to call _project for query
    # then call  with id and copy of cls _tpdata

    mock_project = self.mock_object(
      Assignables = self.mock_object(edit=MockCallable()))

    i = entities.EntityBase(Id=123,data2='a',data3=[1,2])

    call = spy.last_call[1] # kwargs that were called
    self.assertEqual(call['Id'],123)
    self.assertEqual(call['data'],"{'data3': [1, 2], 'data2': 'a'}")


class EntityFactoryTests(unittest.TestCase):
  'make sure it finds right class + custom module + illegal class name'


  def test_defaultClass(self):
    'Default class, factory should return given default callable'
    factory = entities.EntityFactory(
      default_class = MockCallable(response='class'))
    self.assertEqual(factory('Bugs')(),'class')

  def test_CustomLookup(self):
    'factory looks up class name in custom module'
    factory = entities.EntityFactory(
      default_class = MockCallable(response='generic'),
      extension_module = MockObject(Bugs = MockCallable(response='Bug')))
    self.assertEqual(factory('Bugs')(),'Bug')


# Utils Tests, TODO...
class JsonResponseTests(unittest.TestCase):
  "Make sure it parse json correctly into TP response"

class RequesterTests(unittest.TestCase):
  "Error handling on bad dumps + general call"

# API Tests
class ProjectTests(unittest.TestCase):
  def test_wrongEntity(self):
    'Project Errors on wrong entity lookup'
    project = api.Project('blah','blah')
    with self.assertRaises(Exception):
      project.NonEntity


# Integration Tests
class IntegrationTests(unittest.TestCase):
  # We mock at request.py and our actual util requester
  # This is so we can still test the entity creating requester subclass
  class MockRequester(utils.HTTPRequester):
    class MockRequest(object):
      "Mock request.py object, provided so response.json in EntityResponse"
      def __init__(self,mock_response):
        self.mock_response = mock_response 
      def json(self):
        return self.mock_response

    def __init__(self,response_format,mock_response):
      super(IntegrationTests.MockRequester,self).__init__(response_format)
      self.mock_response = self.MockRequest(mock_response)
    def __call__(self,*args,**kwargs):
      self.last_call = (args,kwargs) # Record last call for inspection
      return self.default_response_format(self.mock_response)


  TESTACID='TESTACIDSTR'

  def setup_mockProject(self,http_response):
    # setup mocked client
    mock_requester = self.MockRequester(
      tp.EntityResponse(api.DEFAULT_ENTITY_FACTORY),http_response)

    test_client = tp.TPClient(
      url = 'baseurl',
      requester = mock_requester
    )
    return api.Project(test_client,self.TESTACID)

  def test_query_request(self):
    "Make sure query urls are following the basic pattern of GET baseurl+entity_type"
    # Create project and sent request
    project = self.setup_mockProject(
      {'Items':[{"Id":123,"Name":"OnlyBug","ResourceType":"Bug"}]})
    [x for x in project.Bugs.query()]

    # Make sure request was correct
    request_kwargs = project.tp_client.requester.last_call[1]
    self.assertEqual(request_kwargs['params']['acid'],self.TESTACID)
    self.assertEqual(request_kwargs['method'],'get')
    self.assertEqual(request_kwargs['url'],'baseurl/Bugs/')

  def test_querySingleEntity(self):
    "I can create a query for an entity with a Target Process Project"
    # Create project
    project = self.setup_mockProject(
      {'Items':[{"Id":123,"Name":"OnlyBug","ResourceType":"Bug"}]})
    # Get bugs from project
    bugs_test = [x for x in project.Bugs.query()]
    
    # Make sure Returned Entity is Correct
    self.assertEqual(len(bugs_test),1)
    self.assertEqual(bugs_test[0].Id,123)
    self.assertEqual(bugs_test[0].Name,"OnlyBug")

  def test_queryEntityWithoutID(self):
    "I can create a query for entities (like Contexts) that don't have an ID"
    # Create project
    project = self.setup_mockProject(
      {'Items':[{"Name":"OnlyBug","ResourceType":"Context"}]})
    # Get bugs from project
    entities = [x for x in project.Bugs.query()]
    
    # Make sure Returned Entity is Correct and with ID 
    self.assertEqual(len(entities),1)
    self.assertEqual(entities[0].Name,"OnlyBug")
    with self.assertRaises(AttributeError) as e:
      entities[0].Id 

  def test_createEntity(self):
    "I can create a query to create an entity within a TP Project"
    name_test_str = 'test_name'
    description_test_str = 'test_description'

    # Create project
    project = self.setup_mockProject(
      {'Items':[{"Id":123,"Name":"OnlyBug","ResourceType":"Bug"}]})

    # TEST if url query is bas/entity?params AND also request = post
    project.Bugs.create(Name=name_test_str,Description=description_test_str)
    request_kwargs = project.tp_client.requester.last_call[1]
    print request_kwargs
    self.assertEqual(request_kwargs['method'],'post')
    self.assertEqual(request_kwargs['params']['acid'],self.TESTACID)
    self.assertEqual(request_kwargs['data']['Name'],name_test_str)
    self.assertEqual(request_kwargs['data']['Description'],description_test_str)

  def test_createEntityWithEntityReference(self):
    pass

  def test_editQuery(self):
    pass





if __name__ == "__main__":
  # Import it! 
  unittest.main();
