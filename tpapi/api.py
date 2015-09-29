import tp
import entities

"""
  TODO:
  - Entry point needs to take class factory

"""

def get_project(project_acid, tp_url, auth=None, 
                entity_factory=DefaultEntityClassFactory):
  """Entry point into API, returned Project object
     user can query for entities
  """
  client = tp.TPClient(tp_url,auth)
  return tp.Project(project_acid,client,entity_factory)

class DefaultEntityClassFactory(object):
  def __init__(self,extension_module=None):
    self.extension_module = extension_module

  def __call__(self,name):
    if name not in entities.ALL:
      raise Exception() # Not a TP entity

    # Search for user defined class first
    # else return GenericEntity
    user_class = getattr(self.extension_module,name,None)
    if user_class:
      return user_class
    else:
      return tp.GenericEntity
     
    
