import unittest
import tp

'''
TODO:
Test toArgString
'''

# Todo: Test baseurl is respected
# Todo: Client method tests
# Todo: Test Different Limit numbers -> Higher than response len, lower
# Todo: Test getitem

class ClientTests(unittest.TestCase):
  # MOCK
  class mock_requester(object):
    def __init__(self,response_callback): 
      self.response = response_callback
    def __call__(self,url,params,*args,**kwargs):
      return self.response()

  def setUp(self):
    self.BASEURL = 'test'

  def testSimpleResponse(self):
    'I can Iterate over given response'
    response = lambda: """{"Items":[1,2]}"""
    self.aut = tp.TPClient( self.BASEURL,
                            requester=self.mock_requester(response))
    assert 1 in self.aut.query('Bugs',)      

  def testMultiResponse(self):
    'I can Iterate over a multi query response'
    
    def create_mock():
      r = [""" {"Items":[3,4]} """,
           """ {"Items":[1,2], "Next":"url2"} """]
                   
      callback =  lambda: r.pop() if len(r) > 1  else r[0]
      return tp.TPClient( self.BASEURL,
                            requester=self.mock_requester(callback))

    aut = create_mock()
    assert 4 in aut.query('Arbitrary') 

  def testMaxMultiResponse(self):
    'I can only iterate equal to length of ENTITY_MAX'
    response = lambda: """ {"Items":[1,2],"Next":"url"} """
    aut = tp.TPClient( self.BASEURL,
                       requester=self.mock_requester(response))
    assert len([x for x in aut.query('Arb',entity_max=10)]) == 10 

  def testSingleResponse(self):
    'I can request single entity info'
    response = lambda: """ {"Id":123} """
    aut = tp.TPClient( self.BASEURL,
                        requester=self.mock_requester(response))  
    assert aut.query('Arb')[0]


class ProjectTests(unittest.TestCase):

  class MockClient(tp.TPClient):
    def _request(self,url,verb='get',*args,**kwargs):
      return {}

  class MockEntity(object):
    @classmethod
    def from_json(cls,raw):
      return raw

  def setUp(self):
  
    self.mock_client =  self.MockClient('BASEURL',None)

  def test(self):
    class_under_test = tp.Project('ACIDVAL',self.mock_client,self.MockEntity)
    #assert class_under_test.Bugs(ids=12345) == []
    

if __name__ == "__main__":
  # Import it! 
  unittest.main();
