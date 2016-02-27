.. tpapi documentation master file, created by
   sphinx-quickstart on Wed Oct  7 19:39:46 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to TPapi's documentation!
=================================
A Python wrapper library over the TargetProcess REST API - create, query and edit 
entities within a TargetProcess Project. 

Entities are returned as Python Objects with properties cached in memory. Initial implementation 
doesn't include cache validation so best not hold onto entity references for too long. 

A mechanism for extending returned entity classes is included, hopefully allowing you to implement
additional helper methods as needed, see user guide for examples.

User Guide
----------
.. toctree::
   :maxdepth: 4
  
   user 


API Documentation
------------------
.. toctree::
   :maxdepth: 4

   tpapi



