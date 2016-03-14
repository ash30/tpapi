ALL = [
"Assignables",
"AssignedEfforts",
"Assignments",
"Attachments",
"Bugs",
"Builds",
"Comments",
"Companies",
"Contexts",
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

# Exception
class EntityNameError(Exception): pass 

class EntityFactory(object):
  """Default implementation of Entity Class Factory,
    When called, will instanciate tp.GenericEntity sub class based on entity string"""

  def __init__(self,default_class, extension_module=None):
    """
    :param default_class: Default class to return if 
      name doesn't exist in extension_module
    :param extension_module: (Optional) 
      getattr(extension_module,type) should return desired sub class
    """
    self.extension_module = extension_module
    self.default_class = default_class

  def __call__(self,name):
    """Looks up class name in extension module and returns class, else 
    returns default class 

    :param name: name of Target Process Entity
    :return: tp.GenericEntity sub class
    :raise: EntityNameError if name doesn't match valid TargetProcess Entity
    """

    # Search for user defined class first
    # else return GenericEntity
    user_class = getattr(self.extension_module,name,None)
    if user_class:
      return user_class
    else:
      return self.default_class


class EntityBase(object):
  def __new__(cls,*args,**kwargs):
    "Setup _tpdata before instance access controls"
    instance = object.__new__(cls)
    super(EntityBase,instance).__setattr__('_tpdata',{})
    return instance 

  def __init__(self,Id,**kwargs):
    # Every Entity requires ID
    self.Id = Id
    self._tpdata.update(kwargs)

  def __setattr__(self,name,val):
    if name in self._tpdata:
      self._tpdata[name] = val
    else:
      object.__setattr__(self,name,val)

  def __getattr__(self,name):
    if name in self._tpdata:
      return self._tpdata[name]
    else: 
      return AttributeError()

  def sync(self):
    """ post changes made entity to server """
    #TODO: We've got rid of project, need to fix sync method
    # DO we add acid value to entity object?
    entitiy_id = self.Id
    data = self._tpdata.copy()
    getattr(self._project,'Assignables').edit(Id = entitiy_id,data=str(data))

  def toDcit(self):
    return self._tpdata

  def __repr__(self):
    name = self.__class__.__name__
    return "{}({})".format(name,
    ",".join("{}={}".format(k,repr(v)) for k,v in self._tpdata.iteritems()))


class GenericEntity(EntityBase):
  pass

