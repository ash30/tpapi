# tpapi
A Python client library for the Target Process Rest API. Mostly a simple object mapper for entity data
and takes care of the http requests for you. Entities are returned as Python Objects, dynamic classes based on the meta data returned by the tp rest api.

As of 0.3 tpapi supports reading most of the data in a project.
Creating and editing entity still WIP.

## Quickstart
	import tpapi
	from requests.auth import HTTPBasicAuth
	
	uname = 'USER'
	pword = 'PASS'
	url = "https://yourCompany.tpondemand.com/api/v1/"
	project_id = 1001
	project = tpapi.get_project(project_id,url,auth=HTTPBasicAuth(uname,pword))

	# Get the release
	release = next(project.Releases(where="Name eq 'Version1'"))
	
	# Get all assigned bugs
	current_bugs = list(release.Bugs)

	# Remaining Bug effort for release
	print sum(map(lambda b:b.TimeRemain,current_bugs))

	# Panic ? 
