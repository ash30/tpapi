import unittest
import tp

class ClientTests(unittest.TestCase):
  
  def setUp(self):
    pass

class ProjectTests(unittest.TestCase):

  class MockClient(tp.TPClient):
    def _request(self,url,verb='get',*args,**kwargs):
      return url

  def setUp(self):
    self.mock_client =  self.MockClient('BASEURL',None)

  def test(self):
    class_under_test = tp.Project('ACIDVAL',self.mock_client)
    print class_under_test.bugs(12345)
    

if __name__ == "__main__":
  # Import it! 
  unittest.main();
