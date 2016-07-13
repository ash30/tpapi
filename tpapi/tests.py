import unittest
import re
import json
import collections
from collections import namedtuple

import client,api,entities

# TODO:
# Test multiple get_entities calls
# so that the second one uses the cached value
# Really - the class factory needs a delegate to call inorder to get 
# the meta data. THE CLIENT SHOULDN"T NEED TO TEST FOR CLASS EXISTANCE

# MOCKS
class MockCallable(object):
  fcall = namedtuple('fcall',['args','kwargs'])
  def __init__(self,response=None):
    self.last_call = None
    self.response = response
  def __call__(self,*args,**kwargs):
    self.last_call = self.fcall(args,kwargs)
    return self.response(*args,**kwargs) if callable(self.response) else self.response

class MockObject(object):
  def __init__(self,**kwargs):
    self.__dict__.update(kwargs)

# UNIT TESTS
# == client.py Tests == #
class HTTPRequestDispatcherTests(unittest.TestCase):
  def setUp(self):
    self.test_instance = client.HTTPRequestDispatcher()

  def test_encode_params_list(self):
    # The only time I can thing this is called
    # is when using ids=123,1234 for context
    "I think this only called when using 'ids' *maybe?"
    n = self.test_instance.encode_params({'test':[1,2,3]})
    self.assertEqual(n,"test=1,2,3")
  
  def test_encode_params_str(self):
    n = self.test_instance.encode_params({'test':"foobar"})
    self.assertEqual(n,"test=foobar")

  def test_encode_params_unicode(self):
    n = self.test_instance.encode_params({u'test':u"foobar"})
    self.assertEqual(n,"test=foobar")

  def test_encode_params_int(self):
    n = self.test_instance.encode_params({'test':123})
    self.assertEqual(n,"test=123")


class TPBasicClientTests(unittest.TestCase):
  """ The client is an adapter of the more basic functionality of the 
  HTTPRequestDispatcher hence to test the base client, we need to prove
  proper delegation for each action method.
  """
  TEST_BASE_URL  = 'testurl'
  def setUp(self):
    "Setup client with mock requester so we can feed in request reponses"
    self.request_response = [[1,2,3]]

    self.mock_dispatcher = MockObject(
      paginated_get_request = MockCallable(
        response = lambda url,params:self.request_response
      ),
      post_request = MockCallable(
        response = lambda url,params,msg,response_format:self.request_response
      ),
    )
    self.test_client = client.BasicClient(
      self.TEST_BASE_URL,self.mock_dispatcher
    )

  # Method call tests
  def test_get_entities_http_request(self):
    "Get entities should send a paginated get request"
    test_inst = [i for i in self.test_client.get_entities('test_entity')]
    self.assertEqual(test_inst,[1,2,3])

  def test_create_entity_http_request(self):
    "create entity should send post request and return response"
    self.request_response = "client just returns response"
    test_inst = self.test_client.create_entity('test_entity',{})
    self.assertEqual(test_inst,self.request_response)

  # Client functionality
  def test_get_entities_chains_multi_iterable(self):
    """ Get entities should present a list of lists as a single iterable,
    This way we simplify paginated request for caller
    """
    self.request_response = [[0,1,2,3],[4,5,6],[7,8,9]]
    test_inst = [i for i in self.test_client.get_entities('test_entity')]
    self.assertEqual(test_inst,range(10))

  def test_request_call_includes_baseurl(self):
    """General condition for interaction with client and requester
    The client will always make sure to pass full urls to the requester
    """
    test_inst = [i for i in self.test_client.get_entities('test_entity')]
    self.assertEqual(
      self.mock_dispatcher.paginated_get_request.last_call.args[0],
      "/".join([self.TEST_BASE_URL,"test_entity"])
    )

class TPClientEntityLimitTests(unittest.TestCase):
  """The client is also able to limit number of entities it returns
  This is really a safety check to make sure we don't inadvertantly
  send too many requests (each request = 25 items)
  """
  def setUp(self):
    "Setup client with mock requester so we can feed in request reponses"
    self.request_response = [[1,2,3,4,5]]
    self.mock_dispatcher = MockObject(
      paginated_get_request = MockCallable(
        response = lambda url,params:self.request_response
      ),
    )
    self.test_client = client.BasicClient(
      "test",self.mock_dispatcher
    )
  def test_limit_more_than_response_length(self):
    # default limit = 50
    test_collection = [i for i in self.test_client.get_entities('test_entity')]
    self.assertTrue(len(test_collection)==5)

  def test_limit_less_than_response_length(self):
    test_collection = [i for i in self.test_client.get_entities('test_entity',return_limit=3)]
    self.assertTrue(len(test_collection)==3)

  def test_limit_spans_multiple_requests(self):
    self.request_response = [range(10),range(10,20)]
    test_collection = [i for i in self.test_client.get_entities('test_entity',return_limit=15)]
    self.assertEqual(test_collection,range(15))

  def test_limit_is_unsupported(self):
    "We don't support floats or non numbers or negative ints, should raise error"
    "Also it seems 0 returns nothing, so we also guard against that"
    # all error cases raise Assertino errors 
    with self.assertRaises(AssertionError):
      test_collection = [
        i for i in self.test_client.get_entities('test_entity',return_limit=-1)
      ]
    with self.assertRaises(AssertionError):
      test_collection = [
        i for i in self.test_client.get_entities('test_entity',return_limit=0.1)
      ]
    with self.assertRaises(AssertionError):
      test_collection = [
        i for i in self.test_client.get_entities('test_entity',return_limit="s")
      ]
    with self.assertRaises(AssertionError):
      test_collection = [
        i for i in self.test_client.get_entities('test_entity',return_limit=0)
      ]
class ObjectMappingClientTests(unittest.TestCase):
  """ The conversion of entity data to entity instances is done in
  a specific subclass. These tests confirm the right instance
  is created for a given entity endpoint as data retrieval is already covered.
  """
  def setUp(self):
    "Setup client with mock requester so we can feed in request reponses"
    # Setup mock client
    self.request_response = [[1,2,3,4,5]]
    self.mock_dispatcher = MockObject(
      paginated_get_request = MockCallable(
        response = lambda url,params:self.request_response
      ),
      post_request = MockCallable(
        response = lambda url,params,data,response_format:self.request_response
      )
    )
    # setup mock class factory
    class MockEntity(object):
      def __init__(self,data):
        self.d = data
      @classmethod
      def create_from_data(cls,d):
        return cls(d)
      def toDict(self):
        return self.d
    # Mock factory will return new subclass of mock 
    self.mock_factory = MockObject(
      get = MockCallable(
        response = lambda entity,immutable: type('MockEntitySubclass',(MockEntity,),{
          'name':entity,'immutable':immutable
        })
      )
    )
    self.test_client = client.ObjectMappingClient(
      "test",self.mock_dispatcher,MockCallable(response=self.mock_factory)
    )
  def test_get_entities_return_class(self):
    "Entity data is instanciated by entity classes based on entity_endpoint"
    test_inst = [i for i in self.test_client.get_entities('test_entity')]
    # Test mock 'get' method of factory was passed entity endpoint
    # also test reponse data was passed to init
    for i in test_inst:
      self.assertEqual(i.name,'test_entity')
      self.assertIn(i.d,range(1,6))

  def test_create_entity_return_class(self):
    "Test we return an immutable entity and passed the post data to init"
    self.request_response = {'foo':'bar'}
    test_inst = self.test_client.create_entity('test_entity',{'foo':'bar'})
    self.assertTrue(test_inst.immutable)
    self.assertEqual(test_inst.d['foo'],'bar')
    self.assertEqual(test_inst.name,'test_entity')

  def test_get_entities_empty_response(self):
    """ If the query result has no items, get entities shouldn't fail 
    aka instanciate stuff without data
    """
    self.request_response = [[]]
    test_inst = [i for i in self.test_client.get_entities('test_entity')]
    self.assertEqual(test_inst,[])
    

# == Api.py Tests == #
class QueryTests(unittest.TestCase):
  """ Querys form the basis of the public api. They mainly wrap the client
  But have some new functionality in how they accept and transform input
  and output args.
  """
  def setUp(self):
    self.mock_client = MockObject(
      get_entities=MockCallable(
        response=lambda entity_endpoint,params,return_limit:(entity_endpoint,params)
      )
    )

  # Default args
  def test_default_args(self):
    "We can pass key val pairs at init time that will always be apart of params"
    test_query = api.Query(self.mock_client,acid='helloWorld')
    test_inst = test_query.get('Bugs')
    self.assertEqual(test_inst[1].get('acid'),'helloWorld')

  def test_default_args(self):
    "We can pass multi default kwargs for incusion into params"
    test_query = api.Query(self.mock_client,acid='helloWorld',foo="bar")
    test_inst = test_query.get('Bugs')
    self.assertEqual(test_inst[1].get('acid'),'helloWorld')
    self.assertEqual(test_inst[1].get('foo'),'bar')

  def test_get_id_return(self):
    "When specifying an Entity Id, we expect a single entity to be returned"
    # redefine mock client to return iter
    self.mock_client = MockObject(
      get_entities=MockCallable(
        response=lambda entity_endpoint,params,return_limit:iter([entity_endpoint,1])
      )
    )
    test_query = api.Query(self.mock_client,acid='helloWorld',foo="bar")
    test_inst = test_query.get('Bugs',Id=1)
    # Test that we didn't get back a list, instead 1st elem
    self.assertTrue(isinstance(test_inst,str))
    self.assertEqual(test_inst,'Bugs/1')
    
  def test_check_endpoint_exists(self):
    "We guard against non existant endpoints to save on the network request"
    with self.assertRaises(AssertionError):
      test_query = api.Query(self.mock_client,acid='helloWorld',foo="bar")
      test_inst = test_query.get('foobar')


# == entities.py Tests == #
class EntityBaseTests(unittest.TestCase):
  class mock_object(object):
    def __init__(self,**kwargs):
      self.__dict__.update(kwargs)
  
  # Data Access Tests
  def test_getattr_Tpdata(self):
    'I can retrieve value from TP data cache via attribute lookup'
    i = entities.EntityBase(data={
      'data1':'a',
      'data2':1,
      'data3':[1,2]
    })

    self.assertEqual(i.data1,'a')
    self.assertEqual(i.data2,1)
    self.assertEqual(i.data3,[1,2])
  
  def test_setattr_Tpdata(self):
    "I cannot edit tpdata cache ref aka entity instance is immutable"
    i = entities.EntityBase(data={'data1':'a'})
    with self.assertRaises(AssertionError):
      i.data1 = 'b'

  def testEntitySubclass_setattr(self):
    "Entity subclasses are still immutable"
    class test(entities.EntityBase):
      pass

    i = test(data={})
    with self.assertRaises(AssertionError):
      i.data1 = 'arbitrary string'

  # Comparison Tests
  def test_entityComparisonTrue(self):
    "Entities with same id should be equal"
    i = entities.EntityBase(data={'Id':1})
    j = entities.EntityBase(data={'Id':1,'onlyIdsMatter':2})
    self.assertEqual(i,j)

  def test_entityComparisonFalse(self):
    "Entites with different Ids should not be equal"
    i = entities.EntityBase(data={'Id':100})
    j = entities.EntityBase(data={'Id':1,'onlyIdsMatter':100})
    self.assertNotEqual(i,j)

  def test_entityComparisonNoId(self):
    "An entity without id can never be equal"
    i = entities.EntityBase(data={'noId':1})
    self.assertNotEqual(i,i)

  # Hashable Tests
  def test_entityHashingTrue(self):
    i = entities.EntityBase(data={'Id':100})
    try:
      d = {i:"isHashable"}
    except:
      raise Exception("Entity isn't hashable")

  def test_entityHashingNoId(self):
    i = entities.EntityBase(data={'Id':100})
    self.assertRaises({i:"isn't Hashable"})

class MutableEntityTests(unittest.TestCase):
  def test_setProperty(self):
    "on a mutable entity, setattr will forward to property objects setter"
    pass


class EntityFactoryTests(unittest.TestCase):
  """ Make sure EntityClassFactory can parse a metadata reponse into
  a suitable class.
  """
  _TESTDATA = './testdata.json'

  def setUp(self):
    with open(self._TESTDATA) as f:
      self.test_data = json.load(f)

    self.test_client = MockObject(
      raw_request = MockCallable(
        response = lambda url:self.test_data
      )
    )
    self.test_class_factory = entities.EntityClassFactory(
      self.test_client
    )
  def test_metadataFailsToParse(self):
    "If error occurs reading metadata we should get a Generic Entity"
    self.test_data = {}
    test_instance = self.test_class_factory.get('Bugs')({})
    self.assertIsInstance(test_instance,entities.GenericEntity) 

  def test_classCreation_value_attribute(self):
    "Parse meta data and assign value properties"
    test_instance = self.test_class_factory.get('Bugs')({})

    self.assertIn("Name",test_instance.__class__.__dict__)
    self.assertIsInstance(
      test_instance.__class__.__dict__['Name'],
      entities.ValueAttribute
    )
  def test_classCreation_resource_attribute(self):
    "Parse meta data and assign resource properties"
    test_instance = self.test_class_factory.get('Bugs')({})

    self.assertIn("Release",test_instance.__class__.__dict__)
    self.assertIsInstance(
      test_instance.__class__.__dict__['Release'],
      entities.ResourceAttribute
    )
  def test_classCreation_collection_attribute(self):
    "Parse meta data and assign Collection properties"
    test_instance = self.test_class_factory.get("Bugs")({})

    self.assertIn("Comments",test_instance.__class__.__dict__)
    self.assertIsInstance(
      test_instance.__class__.__dict__["Comments"],
      entities.CollectionAttribute
    )

  def test_get_mutable_entity_class(self):
    "Factory should be able to supply a mutable version of a entity"
    test_cls = self.test_class_factory.get('Bugs',immutable=False)
    self.assertTrue(issubclass(test_cls,entities.MutableEntity))

  def test_get_all_property_info(self):
    "User should be able to reflect over all class properties"
    test_instance = self.test_class_factory.get('Bugs')({})
    # Assert all types of properties are present in dict
    self.assertIn('Comments',test_instance.entity_properties)
    self.assertIn('Release',test_instance.entity_properties)
    self.assertIn('Name',test_instance.entity_properties)
      

# Entity Property Tests #
class BasePropertyTests(unittest.TestCase):
  """ The base property class mainly supports reflection of
  initial metadata used at init time, the rest is left up to subclasses
  """

  def setUp(self):
    self.test_property = entities.EntityProperty('name','uri/meta',{'meta1':'foo'})

  def test_get_meta_return(self):
    "A Property can return a copy of the meta data it was init from"
    self.assertEqual(self.test_property.get_meta()['meta1'],'foo')

  def test_meta_contains_relURI(self):
    "A propery meta data contains an 'entity endppoint' reference for inspection"
    self.assertEqual(self.test_property.get_meta()['RelUri'],'uri')

  def test_meta_data_is_copy(self):
    "User can't change/edit a metadata as you're only returned a copy"
    m = self.test_property.get_meta()
    m['new_attr'] = 1
    self.assertTrue('new_attr' not in self.test_property.get_meta())

class ValuePropertiesTests(unittest.TestCase):
  def setUp(self):
    class test_class(object):
      test_property = entities.ValueAttribute(
        name = 'test_property', uri = ""
      )
      test_error_property = entities.ValueAttribute(
        name = 'not there', uri = ""
      )
      def __init__(self,test_variable):
        self._tpdata = {'test_property':test_variable}
    self.test_class = test_class

  def test_valueDescriptorGet(self):
    "Descriptor should return value in _tpdata field"
    test_instance = self.test_class(99) 
    self.assertEqual(test_instance.test_property,99)

  def test_valueDescriptorSet(self):
    "Setting the property should update the value in _tpdata"
    test_instance = self.test_class(99) 
    test_instance.test_property = 1
    self.assertEqual(test_instance._tpdata['test_property'],1)

  def test_valueDescriptorSet_missing_attr(self):
    "if propert value not found in _tpdata, just set it,don't error"
    test_instance = self.test_class(99) 
    test_instance.test_error_property = 1
    self.assertEqual(test_instance._tpdata['not there'],1)

  def test_valueDescriptorGetNoValue(self):
    "Descriptor should return None if value = None"
    test_instance = self.test_class(None) 
    self.assertEqual(test_instance.test_property,None)

  def test_valueDescriptorGetDataNotPresent(self):
    "Descriptor should return None if value wasn't in initial tp data"
    test_instance = self.test_class(None) 
    self.assertEqual(test_instance.test_error_property,None)


class ResourcePropertiesTests(unittest.TestCase):
  def setUp(self):
    self.test_client = MockObject(
      get_entities = MockCallable(response = iter([{"Name":"helloWorld"}]))
    )
    test_client = self.test_client
    class test_class(object):
      TP = test_client
      test_property = entities.ResourceAttribute(
        name = 'test_property', uri = 'spam/meta', metadata = {}
      )
      test_error_property = entities.ResourceAttribute(
        name = 'not there', uri = ""
      )
      def __init__(self,test_variable):
        self._tpdata = {
          'test_property':test_variable
        }
    self.test_class = test_class
  
  def test_ResourcePropertyWithoutAnyData(self):
    "if no data is there, return None ie, no resource assigned"
    test_instance = self.test_class(None) 
    self.assertEqual(test_instance.test_property,None)

  def test_ResourcePropertyCallsClientCorrectly(self):
    "Resources are just sparse, only hold Id in _tpdata. Property has to fetch data"
    test_instance = self.test_class({'Name':'foobar',"ResourceType":'chips','Id':1})
    self.assertEqual(test_instance.test_property['Name'],'helloWorld')
    # Make sure url is working
    # Interesting, seems we ignore resource type in initial data
    # and prefer uri ? Good / bad ?
    self.assertEqual(self.test_client.get_entities.last_call.args[0], 'spam/1')

  def test_ResourcePropertyCanSetToOtherEntity(self):
    "When user sets property, update value to dict with id == new entity"
    test_instance = self.test_class(None) 
    test_instance.test_property = MockObject(Id=999)
    self.assertEqual(test_instance._tpdata['test_property'],{'Id':999})


class CollectionPropertiesTests(unittest.TestCase):
  """ Collection properties are some what easier than resources
  Most of the time they will be blank, as so client returns it
  """
  def setUp(self):
    self.test_client = MockObject(
      get_entities = MockCallable(
        response = iter([{"Name":"helloWorld"},{"Name":"Goodbye"}])
      )
    )
    test_client = self.test_client
    class test_class(object):
      TP = test_client
      _api_endpoint = "foo"
      test_property = entities.CollectionAttribute(
        name = 'test_property', uri = 'spam/meta'
      )
      def __init__(self,test_variable):
        self._tpdata = {
          'test_property':test_variable,
          'Id':1,
        }
      def __getattr__(self,name):
      # Mimic GenericEntity lookup
        return self._tpdata[name]

    self.test_class = test_class

  def test_trivialCollectionInData(self):
    """ If the collection attr has any data
    in initial response, just return it
    """
    test_instance = self.test_class([
      {'Name':'foobar'},
      {'Name':'HelloWorld'},
    ])
    self.assertEqual(len(test_instance.test_property),2)
    self.assertEqual(test_instance.test_property[0].Name,'foobar')
    self.assertIsInstance(
      test_instance.test_property[0],entities.GenericEntity
    )
    
  def test_CollectionCallsClientCorrectly(self):
    "if no data is present, property makes call to client"
    test_instance = self.test_class(None) 
    self.assertNotEqual(test_instance.test_property,None)
    # Make sure url is correct ie 
    # <current entitiy endpoint>/<current entity id>/<collection endpoint>
    self.assertEqual(
      self.test_client.get_entities.last_call.args[0], 'foo/1/spam'
    )


# Integration Tests
class IntegrationTests(unittest.TestCase):
  """ Here we setup a full object graph and see if a a request from the
  api layer can make its way all the way through and back again returning
  entity instances. We mock out the very lowest level, the request.py
  module handle in HTTPRequestDispatcher and supply our own data to the requests
  """

  def setUp(self):
    self.TESTACID='TESTACIDSTR'
    
    # Mock response need to be from root to specifc 
    # in order to be matched correctly 
    # e.g { "test":1,"test/123/":2,
    self.mock_responses = {
      r"Test/Context/\?ids=111":{
        'Items':[{'Acid':'foo'}]
      },
      r"Test/Context/meta": {
        'This will error to a generic Entity':1
      },
      r"Test/Bugs/\?acid=foo":{
        'Items':[
          {'Id':1,'Name':'Item1'},{'Id':2,'Name':'Item2'}
        ]
      },
      "Test/Bugs/meta":{
        'Name':"Bug",
        'ResourceMetadataPropertiesDescription':{
          
          "ResourceMetadataProperties"\
          "ResourceValuesDescription":{"Items":[
            {"Name":"Id"},{"Name":"ValueAttrExample"}]},

          "ResourceMetadataProperties"\
          "ResourceReferencesDescription":{"Items":[{"Name":"ResourceAttrExample"}]},
        },
      },
    }

    def mock_request(method,url,auth,**kwargs):
      try:
        return MockObject(
          json = MockCallable(response = [
            v for k,v in self.mock_responses.iteritems()
            if re.match(r"^("+ k +r")/?\??(&?format=json)?(?!.)",url)][0]
          ),
          raise_for_status = MockCallable(response=None)
        )
      except IndexError:
        raise Exception("Mock Request couldn't match {}".format(url or "None"))

    # Mock out requests.py for test client
    self.test_requester = client.HTTPRequestDispatcher()
    self.test_requester._requests = MockObject(
      request = mock_request
    )
    self.test_client = client.TPEntityClient(
      url = 'Test',
      requester = self.test_requester,
    )
    self.test_project = api.ProjectProxy(self.test_client,MockObject(Id=111))

  def test_simple_query_request(self):
    "Project attributes should return iter of Generic Entities"
    # Bad meta should fail and return generic entities
    self.mock_responses.update({
      r"Test/Bugs/meta":{
        'ResourceMetadataPropertiesDescription':{
        },
      },
    })
    items = [x for x in self.test_project.get("Bugs")]

    # We should get back 2 generic entities
    self.assertTrue(len(items) == 2 )
    self.assertTrue(items[0].Name == 'Item1')
    self.assertTrue(items[0].Id == 1)
    self.assertIsInstance(items[0],entities.GenericEntity)

  def test_EntityClass_from_request(self):
    "This tests to make sure the class factory instanciates dynamic classes"
    self.mock_responses.update({
      r"Test/Bugs/\?acid=foo":{
        'Items':[
          {'Id':1,'Name':'Item1','ValueAttrExample':1},
          {'Id':2,'Name':'Item2','ValueAttrExample':2},
        ]
      },
    })
    items = [ x for x in self.test_project.get('Bugs')] 
    self.assertTrue(len(items) == 2 )
    self.assertNotIsInstance(items[0],entities.GenericEntity)
    self.assertEqual(items[0].ValueAttrExample, 1)

  def test_queryEntityWithoutID(self):
    "I can create a query for entities (like Contexts) that don't have an ID"
    self.mock_responses.update({
      r"Test/Context/\?acid=foo":{
        "Items":[{'ItemWithoutId':1,'Name':'Context'}]
      }
    })

    # Get bugs from project
    items = [x for x in self.test_project.get('Context')]
    
    # Make sure Returned Entity is Correct and with ID 
    self.assertEqual(len(items),1)
    self.assertEqual(items[0].Name,'Context')
    self.assertIsInstance(items[0],entities.GenericEntity)
    with self.assertRaises(AttributeError) as e:
      items[0].Id 

  def test_createEntity(self):
    "I can create a query to create an entity within a TP Project"
    # Try creating a test bug with value and resource based attrs
    bug_data = {
      'Id': 0,
      'ValueAttrExample':'NewBug',
      'ResourceAttrExample':MockObject(Id=1)
    }
    returned_bug_data = bug_data.copy()
    returned_bug_data['Id']=123

    self.mock_responses.update({
      r"Test/Bugs":returned_bug_data
    })

    # Assert returned bug has same data as input data
    # plus now has an ID
    new_bug = self.test_project.create('Bugs',bug_data)
    self.assertEqual(new_bug.ValueAttrExample,'NewBug')
    self.assertEqual(new_bug.Id,123)

if __name__ == "__main__":
  unittest.main();
