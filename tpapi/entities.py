import itertools
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
    data = inst._tpdata.get(self.name)
    if not data: 
      return None
    elif "ResourceType" in data:
      # Any substancial resource will be missing most of its data
      # We send another request to return full data for nested entity
      end_point = propertyRESTEndpoint(data['ResourceType'])
      url = '/'.join([end_point,str(data['Id'])])
      return next(cls.TP.request('get',url))
    else:
      # Trivial Entity, just return data as it *probably* includes all data already
      return EntityClassFactory(data,cls.TP)(data)

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
  # Work around a bug, for some reason context meta doesn't return correctly...
  if response.get('ResourceType') == 'Context':
    return GenericEntity

  # Make sure every class has a reference to client
  properties = {'TP':tpclient}

  # Get Entity Definition
  # Bit of hack, we use internal method in client to retrieve data sans entity wrapping
  # Response = (list of items,url) hence [0][0]
  meta = tpclient._get_data('get',"/".join([propertyRESTEndpoint(response['ResourceType']),'meta']),data=None)[0][0]
  name = meta['Name']
  property_info = meta['ResourceMetadataPropertiesDescription']

  # Values
  for definition in property_info['ResourceMetadataPropertiesResourceValuesDescription']['Items']:
    properties[definition['Name']] = ValueAttribute(definition['Name'])

  # Resources 
  if property_info.get("ResourceMetadataPropertiesResourceReferencesDescription"):
    for definition in property_info['ResourceMetadataPropertiesResourceReferencesDescription']['Items']:
      properties[definition['Name']] = ResourceAttribute(definition['Name'])

  # Collections
  if property_info.get("ResourceMetadataPropertiesResourceCollectionsDescription"):
    for definition in property_info['ResourceMetadataPropertiesResourceCollectionsDescription']['Items']:
      properties[definition['Name']] = CollectionAttribute(definition['Name'])

  return type(str(name),(EntityBase,),properties) 


class EntityBase(object):
  """Base class for TP Entities, provides simple object interface for the entity data"""

  def __init__(self,data):
    # NOTE: Actually NOT all entities have an ID, just most of them...
    # Commenting this requirement out for now, but we should inforce Id
    # in assignables, probably need to instanciate separate class
    ## Every Entity requires ID
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
    if hasattr(other,"Id") and hasattr(self,"Id"):
      return self.Id == other.Id
    else:
      return False

  def __hash__(self):
    return self.Id

class GenericEntity(EntityBase):
  pass
