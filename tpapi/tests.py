import unittest, functools
from collections import namedtuple
import tp,api

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
    mock_requestor = MockCallable()
    base_url       = 'www.baseurl.com'
    client         = tp.TPClient(base_url,mock_requestor)
  
    # has base class by default
    client._request('get',url='bugs',params={})
    self.assertEqual( 
      mock_requestor.last_call.kwargs.get('url'),base_url+'/bugs')

    client._request('get',url='bugs',base=False,params={})
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
  "Query Tests only have to validate correct use of client"  

  def setUp(self):
    self.mock_client = MockObject(request=MockCallable(response=[]))

  def test_queryEntity(self):
    "Query submits entity to client call"
    query = tp.Query(self.mock_client,'acid','entity')
    # query
    call = query.query()
    self.assertTrue(
      self.mock_client.request.last_call.kwargs['url'].startswith('entity'))
    # edit
    call = query.edit(entity_id=123)
    self.assertTrue(
      self.mock_client.request.last_call.kwargs['url'].startswith('entity'))
    # create
    call = query.create()
    self.assertTrue(
      self.mock_client.request.last_call.kwargs['url'].startswith('entity'))

  def test_queryID(self):
    "Query submits entity+id to client call"
    query = tp.Query(self.mock_client,'acid','entity')
    self.assertEqual(query._IDUrl(123),'entity/123')


class EntityBaseTests(unittest.TestCase):
  class mock_object(object):
    def __init__(self,**kwargs):
      self.__dict__.update(kwargs)
  
  def test_getattr_Tpdata(self):
    'I can retrieve value from TP data cache'
    i = tp.EntityBase('project_mock',Id=123,data1='a',data2=1,data3=[1,2])
    self.assertEqual(i.data1,'a')
    self.assertEqual(i.data2,1)
    self.assertEqual(i.data3,[1,2])
  
  def test_getattr_InstanceVar(self):
    'I can retrieve standard variable from instance'
    i = tp.EntityBase('project_mock',Id=123, data1='a',data2=1,data3=[1,2]) 
    self.assertEqual(i._project, 'project_mock')

  def test_getattr_shadowing(self):
    'If name exists in tpdata and instance, get instance'
    i = tp.EntityBase('project_mock',_project='not_project',Id=123)
    self.assertEqual(i._project,'project_mock')
    self.assertTrue('_project' in i._tpdata)
    
  def test_setattr_Tpdata(self):
    'I can edit tpdata cache ref'
    i = tp.EntityBase('project_mock',Id=123,data1='a')
    i.data1 = 'b'
    self.assertEqual(i.data1,'b')
    self.assertEqual(i._tpdata['data1'],'b')

  def test_setattr_InstanceVar(self):
    'I can modify normally instance ref'
    i = tp.EntityBase('project_mock',Id=123,data1='a')
    i._project = 'new_project'
    self.assertEqual(i._project, 'new_project')
    self.assertEqual(i.__dict__['_project'],'new_project')

  def test_sync(self):
    'I can send copy of tp data to update client'
    # To be sucessful, cls needs to call _project for query
    # then call  with id and copy of cls _tpdata

    mock_project = self.mock_object(
      Assignables = self.mock_object(edit=MockCallable()))

    i = tp.EntityBase(mock_project,Id=123,data2='a',data3=[1,2])
    i.sync()
    spy = mock_project.Assignables.edit
    call = spy.last_call[1] # kwargs that were called
    self.assertEqual(call['Id'],123)
    self.assertEqual(call['data'],"{'data3': [1, 2], 'data2': 'a'}")

# Utils Tests
class JsonResponseTests(unittest.TestCase):
  "Make sure it parse json correctly into TP response"

class RequesterTests(unittest.TestCase):
  "Error handling on bad dumps + general call"

# API Tests
class EntityFactoryTests(unittest.TestCase):
  'make sure it finds right class + custom module + illegal class name'

  def test_wrongEntity(self):
    'factory Errors on wrong entity'
    factory = api.EntityFactory('dummyClass')
    self.assertRaises(Exception,factory,'test')

  def test_defaultClass(self):
    'Default class, factory should return given default callable'
    factory = api.EntityFactory(
      default_class = MockCallable(response='class'))
    self.assertEqual(factory('Bugs')(),'class')

  def test_CustomLookup(self):
    'factory looks up class name in custom module'
    factory = api.EntityFactory(
      default_class = MockCallable(response='generic'),
      extension_module = MockObject(Bugs = MockCallable(response='Bug')))
    self.assertEqual(factory('Bugs')(),'Bug')


if __name__ == "__main__":
  # Import it! 
  unittest.main();
