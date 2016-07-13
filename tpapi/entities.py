import itertools

# Json keys for meta response # 
PROPERTIES_DEF_KEY = 'ResourceMetadataPropertiesDescription'
VALUE_DEF_KEY = 'ResourceMetadataPropertiesResourceValuesDescription'
RESOURCE_DEF_KEY = "ResourceMetadataPropertiesResourceReferencesDescription"
COLLECTION_DEF_KEY = "ResourceMetadataPropertiesResourceCollectionsDescription"

ALL = [
"Assignables",
"AssignedEfforts",
"Assignments",
"Attachments",
"Bugs",
"Builds",
"Comments",
"Companies",
"Context",
"CustomActivities",
"CustomRules",
"EntityStates",
"EntityTypes",
"Epics",
"Features",
"Generals",
"GeneralFollowers",
"GeneralUsers",
"GlobalSettings",
"Impediments",
"InboundAssignables",
"Iterations",
"Messages",
"MessageUids",
"Milestones",
"OutboundAssignables",
"Priorities",
"Processs",
"Programs",
"Projects",
"ProjectAllocations",
"ProjectMembers",
"Relations",
"RelationTypes",
"Releases",
"Requests",
"Requesters",
"RequestTypes",
"Revisions",
"RevisionFiles",
"Roles",
"RoleEfforts",
"Severities",
"Tags",
"Tasks",
"Teams",
"TeamAssignments",
"TeamIterations",
"TeamMembers",
"TeamProjects",
"TeamProjectAllocations",
"Terms",
"TestCases",
"TestCaseRuns",
"TestPlans",
"TestPlanRuns",
"TestRunItemHierarchyLinks",
"TestSteps",
"TestStepRuns",
"Times",
"Users",
"UserProjectAllocations",
"UserStories",
"Workflows",
] 

def propertyRESTEndpoint(name):
  # HACK: Get REST API end point from entity
  # End point names will be different due to pluralisation...
  # match all but last char of name
  matches = [endpoint for endpoint in ALL if name[:-1] in endpoint]
  if matches:
    return matches[0]
  else:
    # Bail,
    return name 

class ResourceAttribute(object):
  def __init__(self,name):
    self.name = name 
  def __get__(self,inst,cls):
    initial_response_val = inst._tpdata.get(self.name)
    if not initial_response_val: 
      return None
    elif "ResourceType" in initial_response_val:
      # Any substancial resource will be missing most of its data
      # We send another request to return full data for nested entity
      end_point = propertyRESTEndpoint(initial_response_val['ResourceType'])
      url = '/'.join([end_point,str(initial_response_val['Id'])])
      return next(cls.TP.request('get',url))
    else:
      # Trivial Entity
      # Return data as it *probably* includes all data already
      trivial_entity_class = EntityClassFactory(initial_response_val, cls.TP)
      return trivial_entity_class(data=initial_response_val)

class CollectionAttribute(object):
  def __init__(self,name):
    self.name = name
  def __get__(self,inst,cls):
    data = inst._tpdata.get(self.name)
    if data:
      # Must be trivial collection if data is already included
      return itertools.imap(lambda resource:EntityClassFactory(resource,cls.TP),data)
    else:
      # Is a collection, need to send a proper request
      end_point = propertyRESTEndpoint(inst.ResourceType)
      url = '/'.join([end_point,str(inst.Id),self.name])
      return cls.TP.request('get',url,limit=200)

class ValueAttribute(object):
  def __init__(self,name):
    self.name = name
  def __get__(self,inst,cls):
    return inst._tpdata.get(self.name)

class ClassCache(object):
  # We want one class per resource type, memorise class creation
  def __init__(self,function):
    self.function = function
    self.class_cache = {}

  def __call__(self,response,tpclient):
    resource_type = response.get('ResourceType')
    entity_class = self.class_cache.get(resource_type)

    if entity_class:
      return entity_class
    else:
      entity_class = self.function(response,tpclient)
      self.class_cache[resource_type] = entity_class
      return entity_class 
  

@ClassCache
def EntityClassFactory(response,tpclient):
  "Generate Class from entity Meta data endpoint"
  try:
    # HACK: Use internal method of client to retrieve data sans entity wrapping
    # Response = (list of items,next url) hence [0][0]
    entity_meta = tpclient._get_data(
      method='get',
      url="/".join([propertyRESTEndpoint(response['ResourceType']),'meta']),
      data=None,
    )[0][0]

    entity_name = meta['Name']
    entity_property_definitions = meta[PROPERTIES_DEF_KEY]
  except IndexError,KeyError: # Could not get valid meta description
    return GenericEntity

  # Every class has a reference to client... But why not EntityBase??
  class_properties = {'TP':tpclient}

  for descriptor_class,property_def_key in zip(
    [ValueAttribute,ResourceAttribute,CollectionAttribute],
    [VALUE_DEF_KEY,RESOURCE_DEF_KEY,COLLECTION_DEF_KEY]
  ):
    class_properties.update({
      definition['Name']: descriptor_class(definition['Name']) 
        for definition in entity_property_definitions.get(property_def_key,[])
    })

  return type(str(entity_name),(EntityBase,),class_properties) 


class EntityBase(object):
  """Base class for TP Entities, provides simple object interface for the entity data"""

  def __init__(self,data):
    # NOTE: Actually NOT all entities have an ID, just most of them...
    # Commenting this requirement out for now, but we should inforce Id
    # in assignables, probably need to instanciate separate class
    # self.Id = Id
    self._tpdata = data

  # Most entity classes will have properties objects for attributes access
  # We define generic accessors for fallback base class GenericEntity
  def __getattr__(self,name):
    try:
      return self._tpdata[name]
    except KeyError:
      raise AttributeError()

  def __setattr__(self,name,value):
    "All entity classes attributes should be immutable"
    assert name is '_tpdata', "Cannot mutate Entity instance"
    super(EntityBase,self).__setattr__(name,value)

  def __eq__(self,other):
    # For simplicity we only really compare entities with Ids, to my 
    # knowledge the only entites without Ids are contexts
    if hasattr(other,"Id") and hasattr(self,"Id"):
      return self.Id == other.Id
    else:
      return False

  def __ne__(self,other):
    return not (self == other)

  def __hash__(self):
    assert 'Id' in self._tpdata, "Can't hash an item without Id" 
    return self.Id

class GenericEntity(EntityBase):
  pass
