#!/usr/bin/env python
# encoding: utf-8
"""
NMLTopology.py

Created by Jeroen on 2006-08-10.
Copyright (c) 2006 __MyCompanyName__. All rights reserved.
"""

import sys
import os
import unittest

import rdflib
import urllib2
import xml.sax._exceptions

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
NML = rdflib.Namespace("http://schemas.ogf.org/nml/2012/10/base#")
NSI = rdflib.Namespace("http://schemas.ogf.org/nsi/2012/10/topology#")

DEBUG = False

class NMLTopology:
    
    def __init__(self, url):
        self.url = url
        self.graph = rdflib.Graph()
        try:
            self.graph.parse(url,format="application/rdf+xml")
        except urllib2.URLError:
            print "\nThe URL %s does not exists" % url
        except xml.sax._exceptions.SAXParseException:
            print "\nThe URL %s  is not in a valid format. It cannot be parsed" % url
            print "Please validate against a syntax validator"
        # print "Fetching new topology from %s" % url
        
    
    def getURL(self): return self.url
    
    def __cmp__(self,other):
        if self.getURL() == other.getURL():
            return True
        else:
            return False
    
    def getNonCapacityInterfaces(self):
        nonCap = []
        for interface in self.graph.subjects(predicate=RDF["type"], object=NML["Interface"]):
            if not self.graph.value(subject=interface, predicate=NML["capacity"]):
                nonCap.append(interface)
        return interface
        
    def getSeeAlsoLinks(self):
        "Return all URIs that are the target of seeAlso links in this Topology."
        links = []
        for s,o in self.graph.subject_objects(predicate=NSI["isReference"]):
            links.append(o)
        return links
    
    def getLocations(self):
        "Return all Location objects, together with relevant information."
        locations = []
        for loc in self.graph.subjects(predicate=RDF["type"], object=NML["Location"]):
            locations.append(self.createLocationObject(loc, self))
        return locations
    
    def createLocationObject(self, locURI, topology):
        locName = str(self.graph.value(subject=locURI, predicate=NML["name"]))
        locLat = float(self.graph.value(subject=locURI, predicate=NML["lat"]))
        locLong = float(self.graph.value(subject=locURI, predicate=NML["long"]))
        return NMLLocation(locName,locURI,locLat,locLong, topology)

    def getLocationForInterface(self, interface):
        "Return the relevant Location object, given an interface ID"
        if not interface:
            print "No Interface: %s met URL: %s" %(interface, self.url)
        dev = self.graph.value(predicate=NML["hasOutboundPort"], object=interface)
        if not dev:
            dev = self.graph.value(predicate=NML["hasInboundPort"], object=interface)
        if not dev:
            raise Exception(interface + "does not have accompanying device?")
        loc = self.graph.value(subject=dev, predicate=NML["locatedAt"])
        if loc:
            return self.createLocationObject(loc,self)
        else:
            print "Interface: %s met URL: %s" %(interface, self.url)
            raise Exception, "No Location found"
    

    def getExternalConnections(self,loc):
        externalConnections = []
        q = '''
        SELECT ?extPg ?extURL
        WHERE { 
            ?dev nml:locatedAt <%s> .
            ?dev nml:hasInboundPort ?pgA .
            ?pgA nml:isAlias ?extPg .
            ?extTopo nml:hasOutboundPort ?extPg .
            ?extTopo nsi:isReference ?extURL .
        }'''  % loc.getURI()
        results = self.graph.query(q)
        for result in results:
            extIf = result[0]
            extUrl = result[1]
            try:
                externalGraph = NMLTopology(extUrl)
            except urllib2.URLError:
                print "The external URL '%s' does not exist." % url
            except xml.sax._exceptions.SAXParseException:
                print "The external URL '%s' is not in a valid format." % url
            else:
                externalLoc = externalGraph.getLocationForInterface(extIf)
                externalConnections.append((loc, externalLoc))
        return externalConnections
    
    def getInternalConnections(self, locs):
        internalConnections = []
        for a,b in self.xuniqueCombinations(locs, 2):
            select = ("?ifA", "?ifB")
            where = rdflib.sparql.graphPattern.GraphPattern([
                ("?devA", NML["locatedAt"], rdflib.URIRef(a.getURI())),
                ("?devA", NML["hasInterface"], "?ifA"),
                ("?ifA", NML["connectedTo"], "?ifB"),
                ("?devB", NML["hasInterface"], "?ifB"),
                ("?devB", NML["locatedAt"], rdflib.URIRef(b.getURI()))
                ])
            results = rdflib.sparql.Query.query(self.store, select,where)
            for result in results:
                # We really only want to know whether there is a connection
                # and the number of them.
                internalConnections.append((a,b))
                if DEBUG:
                    print "Adding internal connection: %s to %s" % (a.getName(),b.getName())
        return internalConnections
        
    def getConnections(self):
        """Get connections that involve a seeAlso and two Locations.
        Returns: [(Location, Location)]"""
        connections = []
        locs = self.getLocations()
        if len(locs) > 1:
            connections += self.getInternalConnections(locs)
        for loc in locs:
            connections += self.getExternalConnections(loc)
        return connections
    
    def getConnectionsForLocation(self,loc):
        connections = []
        locs = self.getLocations()
        if len(locs) > 1:
            internalConnections = self.getInternalConnections(locs)
            for a,b in internalConnections:
                if a == loc:
                    connections.append((loc,b))
                elif b == loc:
                    connections.append((loc,a))
        connections += self.getExternalConnections(loc)
        return connections
        
    def xuniqueCombinations(self, items, n):
        if n==0: yield []
        else:
            for i in xrange(len(items)):
                for cc in self.xuniqueCombinations(items[i+1:],n-1):
                    yield [items[i]]+cc

    def getAllTopologies(self):
        "Crawl through topologies following seeAlso links and return a list of all Topologies."
        alltops = []
        allUrls = []
        alltops.append(self)
        allUrls.append(self.url)
        links = self.getSeeAlsoLinks()
        while links:
            l = links.pop()
            if l not in allUrls:
                newTop = NMLTopology(l)
                alltops.append(newTop)
                allUrls.append(l)
                links += newTop.getSeeAlsoLinks()
        return alltops
        
        
    def crawlTopology(self):
        """
        Crawl all topologies and return the list of all locations and all connections between them.
        
        First we crawl through all rdfs:seeAlso links, gathering all the topologies.
        Then for each topology, we gather all Locations.
        For each Location, we get all the external connections, these are given as (Loc, Loc)
        
        Returns: (List of all Locations, List of all connections)"""
        alltops = self.getAllTopologies()
        allLocs = []
        conList = []
        for top in alltops:
            for loc in top.getLocations():
                if loc not in allLocs:
                    allLocs.append(loc)
                cons = top.getConnections()
                for con in cons:
                    # Check if (a,b) or (b,a) is already in the list
                    # Might be better to use a special object, but this works too
                    if not conInConnectionList(con, conList):
                        conList.append(con)
        return allLocs, conList
        
    def writeGoogleMapInfo(self,filename):
        "Convert the CrawlTopology output to a format that can be used by a Google Maps script."
        points, cons = self.crawlTopology()
        f = open(filename,'w')
        f.write("<markers>\n")
        for con in cons:
            f.write("  <connection lat1='%f' lng1='%f' lat2='%f' lng2='%f' />\n" % (con[0].getLattitude(),con[0].getLongitude(),con[1].getLattitude(),con[1].getLongitude()))
        for p in points:
            f.write("  <marker lat='%f' lng='%f' />\n" % (p.getLattitude(), p.getLongitude())) 
        f.write("</markers>")
        f.close()

def conInConnectionList(con, connlist):
    if con in connlist:
        return True
    if (con[1],con[0]) in connlist:
        return True
        
class NMLLocation:
    def __init__(self, name, uri, lat=None, lon=None, topology=None):
        self.name = name
        self.uri = str(uri)
        self.lat = lat
        self.lon= lon
        self.topology = topology
    
    def __cmp__(self, other):
        if self.uri == other.uri:
            return False
        else:
            return True
           
    def __str__(self):
        return self.uri
    
    def getConnections(self):
        x = self.topology.getConnectionsForLocation(self)
        return x

    def getConnectionsStr(self):
        cons = self.getConnections()
        result = []
        for (a,b) in cons:
            if a == self:
                result.append(b.getName())
            if b == self:
                result.append(a.getName())
        result.sort()
        resultStr = ""
        for x in result:
            resultStr += "%s, " % x
        return resultStr[:-2]
        
    def getName(self): return self.name
    def getURI(self): return self.uri
    def getLongitude(self): return self.lon
    def getLattitude(self): return self.lat
    def getTopology(self): return self.topology
    
    def setName(self, newValue): self.name = newValue
    def setURI(self, newValue): self.uri = newValue
    def setLongitude(self, newValue): self.lon= newValue
    def setLattitude(self, newValue): self.lat = newValue