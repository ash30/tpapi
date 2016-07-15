import weakref

# Utils #
def extract_resourceType_from_uri(uri):
  assert uri.endswith('meta')
  return uri.split('/')[-2]

# Computed properties classes #
class EntityProperty(object):
  def __init__(self,name,uri=None,metadata=None):
    self.name = name 
    self.resourceType_endpoint = extract_resourceType_from_uri(uri) if uri else None
    self._metadata = metadata
    if self._metadata: self._metadata['RelUri'] = self.resourceType_endpoint

  def get_meta(self):
    # return a copy as dict is mutable
    return self._metadata.copy() if self._metadata else None

class ValueAttribute(EntityProperty):
  def __get__(self,inst,cls):
    return inst._tpdata.get(self.name)

  def __set__(self,inst,value):
    assert isinstance(
      value,(basestring,int,float)
    ), "WIP: Value Attributes only supports str,int,float currently"
    inst._tpdata[self.name] = value

class ResourceAttribute(EntityProperty):
  def __get__(self,inst,cls):
    initial_response_val = inst._tpdata.get(self.name)
    if not initial_response_val: 
      return None
    else:
      # We send another request to return full data for nested entity
      assert 'Id' in initial_response_val, "Cannot find resource without Id"
      url = '/'.join([
        self.resourceType_endpoint,
        str(initial_response_val['Id'])
      ])
      return next(cls.TP.get_entities(url))

  def __set__(self,inst,value):
    if not value:
      inst._tpdata[self.name] = None
      return
    # Currently we don't support setting resources to locally made
    # entities. You must first create the leaf entity and then reference it.
    try:
      inst._tpdata[self.name] = {'Id':value.Id}
    except AttributeError:
      raise TypeError("Cannot Set Resource Attribute to non Entity")

class CollectionAttribute(EntityProperty):
  def __get__(self,inst,cls):
    data = inst._tpdata.get(self.name)
    if data:
      # Must be trivial collection if data is already included
      return [GenericEntity(entity_data) for entity_data in data]
    else:
      # Is a collection, need to send a proper request
      url = '/'.join([
        inst._api_endpoint,
        str(inst.Id),
        self.resourceType_endpoint
      ])
      return cls.TP.get_entities(url,return_limit=500)
  # CANNOT SET COLLECTIONS!

class EntityClassFactory(object):
  PROPERTIES_DEF_KEY = 'ResourceMetadataPropertiesDescription'
  PROPERTIES_TYPES = {
    # VALUE
      "ResourceMetadataProperties"\
      "ResourceValuesDescription":ValueAttribute,
    # RESOURCES
      "ResourceMetadataProperties"\
      "ResourceReferencesDescription":ResourceAttribute,
    # COLLECTIONS
      "ResourceMetadataProperties"\
      "ResourceCollectionsDescription":CollectionAttribute,
  }

  def __init__(self,client_delegate):
    self._generated_classes = {}
    # Client already holds reference to factory
    self.client_delegate = weakref.ref(client_delegate)

  def get(self,entity_endpoint,immutable=True):
    "get entitiy class for api end point, if not available, create it"
    entity_class = self._generated_classes.get(entity_endpoint,None)
    if not entity_class:
      try:
        client = self.client_delegate();assert client
        entity_metadata = client.raw_request(
          url="/".join([entity_endpoint,'meta']),
        )
        self._register(
          entity_endpoint, entity_metadata, client
        )
      except ValueError:
        # Parsing meta data went wrong...
        self._generated_classes[entity_endpoint] = GenericEntity
      # Try again now that we've registered something 
      entity_class = self._generated_classes.get(entity_endpoint,None)

    if immutable: return entity_class[0]
    else: return entity_class[1]

  def _register(self,entity_name,metadata,tp_client_reference):
    class_properties = {
      "TP":tp_client_reference,
      "_api_endpoint":entity_name
    }
    # Setup Metadata Properties
    generated_property_objects = {}
    try:
      class_name = metadata['Name']
      property_defintions = metadata[self.PROPERTIES_DEF_KEY]     

      for prop_type,matching_descriptor in self.PROPERTIES_TYPES.iteritems(): 
        for definition in property_defintions.get(prop_type,{}).get('Items',[]):
          name = str(definition['Name'])
          generated_property_objects[name] = matching_descriptor(
            name,uri=definition.get('Uri'),metadata=definition
          )
      # Record list of all properties so classes can reflect over
      class_properties['entity_properties'] = property(
        lambda self :generated_property_objects.copy()
      )
      class_properties.update(generated_property_objects) 
      
      # Now create Mutable and Immutable version of entity class
      mutable_new_class = type(
        "Mutable" + str(class_name),(MutableEntity,),class_properties
      )
      # Immutable class has reference to mutable
      new_class = type(
        str(class_name),(EntityBase,),class_properties
      ) 
    except KeyError:
      # ERROR Badly formed meta data, falling back to generic entity
      new_class = GenericEntity
      mutable_new_class = None

    self._generated_classes[entity_name] = (new_class,mutable_new_class)
    

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

  def toDict(self):
    "Convert Entity to dictionary structure for later serialisation"
    return self._tpdata

class GenericEntity(EntityBase):
  pass

class MutableEntity(EntityBase):
  @classmethod
  def create_from_data(cls,data):
    inst = cls({})
    # We set initial data via property interfaces to 
    # error check content
    for attr,value in data.iteritems():
      setattr(inst,attr,value)
    return inst

  def __init__(self,data):
    # Special case: if Id == 0, then its local entity
    data['Id'] = 0
    super(MutableEntity,self).__init__(data)

  def __setattr__(self,name,value):
    # Allow setting of class properties as well
    if name in vars(self.__class__):
      object.__setattr__(self,name,value)
    elif name == "_tpdata":
      super(MutableEntity,self).__setattr__(name,value)
    else:
      raise AttributeError("Cannot set non existant entity property '{}'".format(name))
