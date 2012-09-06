#!/usr/bin/env python
import rdflib

# This file implements an extremely limited converter for DTOX to NSI topology files
# It expects a certain format, and only converts those parts it knows about.

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
NML = rdflib.Namespace("http://schemas.ogf.org/nml/2012/10/base#")
NMLETH = rdflib.Namespace("http://schemas.ogf.org/nml/2012/10/ethernet#")
NSI = rdflib.Namespace("http://schemas.ogf.org/nsi/2012/10/topology#")
DTOX = rdflib.Namespace("http://www.glif.is/working-groups/tech/dtox#")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")

class AGTopology:
    def __init__(self, url):
        self.url = url
        self.storev1 = rdflib.Graph()
        self.storev2 = rdflib.Graph()
        try:
            self.storev1.parse(url)
        except Exception as e:
            print e
        self.init_v2()
    
    def init_v2(self):
        self.storev2.bind("nml",NML)
        self.storev2.bind("nsi",NSI)
        self.storev2.bind("nmleth",NMLETH)
        
    def addTopo(self,oldtopo):
        topo = self.prefix+"topology"
        self.storev2.add((topo,OWL.NamedIndividual,NML.Topology))
        # NSA
        nsa = self.prefix+"nsa"
        self.storev2.add((nsa,OWL.NamedIndividual,NSI.NSA))
        self.storev2.add((topo,NSI.managedBy,nsa))
        self.storev2.add((nsa,NSI.managing,topo))
        oldnsa = self.storev1.value(subject=oldtopo,predicate=DTOX.managedBy)
        adminContact = self.storev1.value(subject=oldnsa,predicate=DTOX.adminContact)
        self.storev2.add((nsa,NSI.adminContact,adminContact))
        csProviderEndpoint = self.storev1.value(subject=oldnsa,predicate=DTOX.csProviderEndpoint)
        self.storev2.add((nsa,NSI.csProviderEndpoint,csProviderEndpoint))
        # Location
        location = self.prefix+"location"
        self.storev2.add((location,OWL.NamedIndividual,NML.Location))
        self.storev2.add((topo,NML.locatedAt,location))
        oldloc = self.storev1.value(subject=oldtopo,predicate=DTOX.locatedAt)
        lat = self.storev1.value(subject=oldnsa,predicate=DTOX.lat)
        self.storev2.add((nsa,NML.lat,lat))
        long = self.storev1.value(subject=oldnsa,predicate=DTOX.long)
        self.storev2.add((nsa,NML.long,long))
        return topo
    
    def addUniPorts(self,stp,topo,target=None):
        outPort = self.prefix+stp+"-out"
        inPort = self.prefix+stp+"-in"
        for p in (outPort,inPort):
            self.storev2.add((p,OWL.NamedIndividual,NML.Port))
            self.storev2.add((p,NMLETH.vlans,"1780-1783"))
        self.storev2.add((topo,NML.hasOutboundPort,outPort))
        self.storev2.add((topo,NML.hasInboundPort,inPort))
        
    def convert(self):
        topo = self.storev1.value(predicate=RDF.type, object=DTOX.NSNetwork)
        toponame = topo.split(":")[-1]
        self.prefix = "urn:ogf:network:%s.net:2012:" % toponame[:-4]
        print "using prefix: %s" % self.prefix
        self.storev2.bind("owl",OWL)
        self.storev2.bind(toponame,self.prefix)
        # Convert the Topology and its basic attributes
        topov2 = self.addTopo(topo)
        # Convert the STPs
        for stp in self.storev1.objects(topo,DTOX.hasSTP):
            # We take off the invalid network urn prefix
            stp = stp.split(":")[-1]
            # and then we take off the label suffix
            stp = stp.split("-")[0]
            # This means we'll add each port 4 times. Fortunately rdflib is robust to that.
            self.addUniPorts(stp,topov2)
        self.storev2.commit()
        return self.storev2

def main():
    topo = AGTopology("golesv1/aist.owl")
    graph = topo.convert()
    graph.commit()
    print graph.serialize()
if __name__ == '__main__':
    main()
