from api import *

def QuickStart(self):
  # Setup client
  client = TPClient(url,auth)
  Project = (tp,acid)

  # Creating 
  bug1 = Project.bugs.create(Name,Description)

  # Querying 
  bug2 = Project.bugs.query(id=12311)

  # Editing
  bug2.Name = "New Name" # editing
  bug2.Description = "New Description"

  # Sync save
  bug1.sync()


   
