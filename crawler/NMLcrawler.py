#!/usr/bin/env python
# encoding: utf-8
"""
ndl-crawler.py

Created by Jeroen on 2006-09-05.
Copyright (c) 2006 Universiteit van Amsterdam. All rights reserved.
"""

import sys
import os
import unittest
import NMLTopology

DEBUG = True

class NDLcrawler:
    def __init__(self):
        self._topologies = {}
        self._locations = []
        self._connections = []
        self._verifiedConnections = []
        self._unverifiedConnections = []
    
    def crawl(self, startingpoint,resultfile):
        startTopology = NMLTopology.NMLTopology(startingpoint)
        self.findTopologies(startTopology)
        self.findLocations()
        self.findConnections()
        self.writeGoogleMapInfo(resultfile)
    
    def getLocationForURI(self, uri):
        for loc in self._locations:
            if uri == loc.getURI():
                return loc
    
    def addLocations(self, locations):
        for loc in locations:
            if loc not in self._locations:
                if DEBUG:
                    print "Found Location: %s (%s)" % (loc.getName(), loc.getURI())
                self._locations.append(loc)
    
    def findTopologies(self, startingpoint):
        "Crawl through topologies following seeAlso links and return a list of all Topologies."
        self._topologies[startingpoint.url] = startingpoint
        links = startingpoint.getSeeAlsoLinks()
        while links:
            l = links.pop()
            if l not in self._topologies:
                newTop = NMLTopology.NMLTopology(l)
                self._topologies[l] = newTop
                links += newTop.getSeeAlsoLinks()

    def findLocations(self):
        for top in self._topologies.values():
            self.addLocations(top.getLocations())
    
    def findConnections(self):
        allConnections = []
        for loc in self._locations:
            allConnections += loc.getConnections()
        while allConnections:
            (locA,locB) = allConnections.pop()
            if (locB,locA) in allConnections:
                allConnections.remove((locB,locA))
                self._verifiedConnections.append((locA,locB))
                if DEBUG:
                    print "Found connection: %s to %s" % (locA.getName(),locB.getName())
            else:
                self._unverifiedConnections.append((locA,locB))
        
    def writeGoogleMapInfo(self,filename):
        "Convert the CrawlTopology output to a format that can be used by a Google Maps script."
        f = open(filename,'w')
        f.write("<markers>\n")
        for con in self._verifiedConnections:
            f.write("  <connection lat1='%f' lng1='%f' lat2='%f' lng2='%f' />\n" % (con[0].getLattitude(),con[0].getLongitude(),con[1].getLattitude(),con[1].getLongitude()))
        for p in self._locations:
            f.write("  <marker lat='%f' lng='%f' name='%s' url='%s' links='%s'/>\n" % (p.getLattitude(), p.getLongitude(), p.getName(), p.getTopology().getURL(), p.getConnectionsStr())) 
        f.write("</markers>")
        f.close()
    
    


class NDLcrawlerTests(unittest.TestCase):
    def setUp(self):
        pass



        
        
if __name__ == '__main__':
    n = NDLcrawler()
    # n.crawl("http://trafficlight.uva.netherlight.nl/~jeroen/netherlight.rdf", "data.xml")
    n.crawl("https://raw.github.com/jeroenh/AutoGOLE-Topologies/nsiv2/goles/netherlight.net.owl","data.xml")