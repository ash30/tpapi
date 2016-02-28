from api import *

def quickstart():
  """
  Setup a project
	>>> from requests.auth import HTTPBasicAuth
	>>> project = tpapi.Project(
	>>>   project_id=1234,
	>>>   tp_url='yourCompany.Targetproces/api/v1/',
	>>>   auth=HTTPBasicAuth('uname','pword'),
	>>> )  

  Most of the times you will be instanciating a project object to get started 
  as its a convenient way to make requests within the context of a single TP project.
  If Authentication is required you can use the BasicAuth from requests

  Creating 
      >>> new_bug = project.Bugs.create(
      >>>   Name="bug title",
      >>>   Description="This is how to reproduce the bug" 
      >>> )
	  tp.QueryIter

  You can create a query for any TP entity type using the project obect and dot notation.
  Beware of the capitalisation, this was decision taken to mirror the original rest api we are wrapping.
  The return for any request is an iterator for any matching entity within TP project. For creation
  this is obviously an iterator over 1 element.

  Querying 
      >>> bugs = Project.Bugs.query() # All bugs upto limit
      >>> bugs = Project.Bugs.query(Id=2345)
      >>> bugs = Project.Bugs.query(
      >>>   where="EntityState.Name eq 'In Progress'",
      >>>   orderByDesc='CreateDate'
      >>> )

  To get information from the project use the query method. Supplying no parameters does a basic query over any entity matching the same type.
  The paramters for the method are identical to parameters you would normally pass as url query parameters. 

  Tpapi provides an additional parameter in the form of 'limit' and this is just a safe guard to ensure you don't kill your network.

  Editing
	  >>> new_bug.Name = "New Name" # editing
	  >>> new_bug..Description = "New Description"
	  >>> bug2.sync()

  There is a rough api in place to edit entites but its mostly unused/untest at this point...
  """


   
