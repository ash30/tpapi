# tpapi
A Python client library for the Target Process Rest API.
Mostly a simple object mapper for entity data and takes care
of the http requests for you. Entities are returned as Python Objects,
dynamic classes based on the meta data returned by the api.

## Changes
### v0.4 
Support for reading and creating entity data.
Editing data and nice access to custom attributes is next.

### v0.3
Support reading most of the data in a project.
Creating and editing entity still WIP.

## Quickstart
	import tpapi
	from requests.auth import HTTPBasicAuth
	
	uname = 'USER'
	pword = 'PASS'
	url = "https://yourCompany.tpondemand.com/api/v1/"
	project_id = 1001

	tpapi.TP(url,auth=HTTPBasicAuth(uname,pword))
	project = TP.get('Projects',Id=project_id)

	# Get the release
	release = project.get('Releases',where="Name eq 'Version1'")
	
	# Get all assigned bugs
	current_bugs = list(release.Bugs)

	# Remaining Bug effort for release
	print sum(map(lambda b:b.TimeRemain,current_bugs))

	# Panic ? 
	# Starting planning hotfix Release
	new_release = project.create('Release',Name="Version1-Hotfix",Project=project)
