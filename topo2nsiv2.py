#!/usr/bin/env python
import rdflib
import collections

# This file implements an extremely limited converter for DTOX to NSI topology files
# It expects a certain format, and only converts those parts it knows about.

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
NML = rdflib.Namespace("http://schemas.ogf.org/nml/2012/10/base#")
NMLETH = rdflib.Namespace("http://schemas.ogf.org/nml/2012/10/ethernet#")
NSI = rdflib.Namespace("http://schemas.ogf.org/nsi/2012/10/topology#")
DTOX = rdflib.Namespace("http://www.glif.is/working-groups/tech/dtox#")
OWL = rdflib.Namespace("http://www.w3.org/2002/07/owl#")

golenames = {
    "netherlight": "netherlight.net",
    "czechlight": "czechlight.cesnet.cz",
    "starlight": "startap.net",
    "northernlight": "nordu.net",
    "uvalight": "uvalight.net",
    "pionier": "pionier.net.pl",
    "aist": "aist.go.jp",
    "kddi": "kddilabs.jp",
    "kddi-labs": "kddilabs.jp",
    "geant": "geant.net",
    "krlight": "krlight.net",
    "max": "maxgigapop.net",
    "jgnx": "jgn.nict.go.jp",
    "gloriad": "gloriad.org",
    "esnet": "es.net",
    "psnc": "exp.pionier.net.pl",

}
MAPPING = collections.defaultdict(list)
def getUrlName(name):
    if name in golenames.keys():
        return golenames[name]
    else:
        return name
def getNetName(name):
    if "pionier.junos.exp.net" in name:
        return "pionier-exp"
    return getUrlName(name).split(".")[0]
def getTargetTopo(target):
    # UvA believes there is more to GOLEs than just Ethernet.
    if "uva" in target:
        return rdflib.term.URIRef("urn:ogf:network:%s:2012:topology" % target)
    else:
        return rdflib.term.URIRef("urn:ogf:network:%s:2012:ets" % target)

class AGTopology:
    def __init__(self, url):
        self.url = url
        self.storev1 = rdflib.Graph()
        self.storev2 = rdflib.Graph()
        try:
            self.storev1.parse(url)
        except Exception as e:
            print e
        self.topo = self.storev1.value(predicate=RDF.type, object=DTOX.NSNetwork)
        self.urlname = getUrlName(self.topo.split(":")[-1][:-4])
        self.netname = getNetName(self.topo.split(":")[-1][:-4])
        self.prefix = rdflib.Namespace("urn:ogf:network:%s:2012:" % self.urlname)
        self.storev2.bind(self.netname.replace(".","-"),self.prefix)
        self.init_v2()
    
    def init_v2(self):
        self.storev2.bind("nml",NML)
        self.storev2.bind("nsi",NSI)
        self.storev2.bind("nmleth",NMLETH)
        self.storev2.bind("owl",OWL)
        
        
        
    def addTopo(self,oldtopo):
        topo = getTargetTopo(self.urlname)
        self.storev2.add((topo,RDF.type,OWL.NamedIndividual))
        self.storev2.add((topo,RDF.type,NML.Topology))
        # NSA
        nsa = rdflib.term.URIRef(self.prefix+"nsa")
        self.storev2.add((nsa,RDF.type,OWL.NamedIndividual))
        self.storev2.add((nsa,RDF.type,NSI.NSA))
        self.storev2.add((topo,NSI.managedBy,nsa))
        self.storev2.add((nsa,NSI.managing,topo))
        oldnsa = self.storev1.value(subject=oldtopo,predicate=DTOX.managedBy)
        MAPPING[nsa] = oldnsa
        adminContact = self.storev1.value(subject=oldnsa,predicate=DTOX.adminContact)
        self.storev2.add((nsa,NSI.adminContact,adminContact))
        csProviderEndpoint = self.storev1.value(subject=oldnsa,predicate=DTOX.csProviderEndpoint)
        self.storev2.add((nsa,NSI.csProviderEndpoint,csProviderEndpoint))
        # Location
        location = rdflib.term.URIRef(self.prefix+"location")
        self.storev2.add((location,RDF.type,OWL.NamedIndividual))
        self.storev2.add((location,RDF.type,NML.Location))
        self.storev2.add((topo,NML.locatedAt,location))
        oldloc = self.storev1.value(subject=oldtopo,predicate=DTOX.locatedAt)
        lat = self.storev1.value(subject=oldloc,predicate=DTOX.lat)
        self.storev2.add((location,NML.lat,lat))
        long = self.storev1.value(subject=oldloc,predicate=DTOX.long)
        self.storev2.add((location,NML.long,long))
        return topo
    
    def addPorts(self,stp,topo,targetUrl=None,targetNet=None):
        if targetUrl and targetNet:
            outPort = rdflib.term.URIRef(self.prefix+self.netname+"-"+targetNet)
            inPort = rdflib.term.URIRef(self.prefix+targetNet+"-"+self.netname)
            outTarget = rdflib.term.URIRef("urn:ogf:network:%s:2012:%s-%s" %
                                                 (targetUrl,targetNet,self.netname))
            inTarget = rdflib.term.URIRef("urn:ogf:network:%s:2012:%s-%s" %
                                                 (targetUrl,self.netname,targetNet))
            self.storev2.add((outPort,NML.isAlias,inTarget))
            self.storev2.add((inPort,NML.isAlias,outTarget))
            targettopo = getTargetTopo(targetUrl)
            self.storev2.add((targettopo,RDF.type,NML.Topology))
            self.storev2.add((targettopo,RDF.type,OWL.NamedIndividual))
            self.storev2.add((targettopo,NSI.isReference,
                rdflib.Literal("https://github.com/jeroenh/AutoGOLE-Topologies/blob/nsiv2/goles/%s.n3" % targetUrl)))
        else:
            outPort = rdflib.term.URIRef(self.prefix+stp+"-out")
            inPort = rdflib.term.URIRef(self.prefix+stp+"-in")
        for p in (outPort,inPort):
            self.storev2.add((p,RDF.type,OWL.NamedIndividual))
            self.storev2.add((p,RDF.type,NML.PortGroup))
            self.storev2.add((p,NMLETH.vlans,rdflib.term.Literal("1780-1783")))
            self.storev2.add((NMLETH.vlans, OWL.subPropertyOf, NML.hasLabelGroup))
        self.storev2.add((topo,NML.hasOutboundPort,outPort))
        self.storev2.add((topo,NML.hasInboundPort,inPort))
        if targetUrl and targetNet:
            biport = self.prefix["bi-%s-%s" % (self.netname,targetNet)]
        else:
            biport = self.prefix["bi-%s" % (stp)]
        self.storev2.add((biport,RDF.type,OWL.NamedIndividual))
        self.storev2.add((biport,RDF.type,NML.BidirectionalPort))
        self.storev2.add((biport,NML.hasPort,outPort))
        self.storev2.add((biport,NML.hasPort,inPort))
        self.storev2.add((topo,NML.hasBidirectionalPort,biport))
        return biport
        
    def convert(self):
        # Convert the Topology and its basic attributes
        topov2 = self.addTopo(self.topo)
        # Convert the STPs
        for stp in self.storev1.objects(self.topo,DTOX.hasSTP):
            target = self.storev1.value(subject=stp,predicate=DTOX.connectedTo)
            # We take off the invalid network urn prefix
            localstp = stp.split(":")[-1]
            # and then we take off the label suffix
            # This means we'll add each port 4 times. Fortunately rdflib is robust to that.
            localstp = localstp.split("-")[0]
            if target:
                # We take out the network name of the other end to pass as target
                # We need both the URL name for the right prefix, and the netname for nicer postfixes
                targetUrl = getUrlName(target.split(":")[4][:-4])
                targetNet = getNetName(target.split(":")[4][:-4])
                biport = self.addPorts(localstp,topov2,targetUrl,targetNet)
            else:
                biport = self.addPorts(localstp,topov2)
            MAPPING[biport].append(str(stp))
        return self.storev2
def jerrify(mapping):
    mapping['urn:ogf:network:gloriad.org:2012:bi-gloriad-krlight']= ['urn:ogf:network:stp:gloriad.ets:krl.0', 'urn:ogf:network:stp:gloriad.ets:krl.1', 'urn:ogf:network:stp:gloriad.ets:krl.2', 'urn:ogf:network:stp:gloriad.ets:krl.3']
    mapping['urn:ogf:network:gloriad.org:2012:bi-gloriad-startap']= ['urn:ogf:network:stp:gloriad.ets:sl.0', 'urn:ogf:network:stp:gloriad.ets:sl.1', 'urn:ogf:network:stp:gloriad.ets:sl.2', 'urn:ogf:network:stp:gloriad.ets:sl.3']
    mapping['urn:ogf:network:nordu.net:2012:bi-nordu-pionier']= ['urn:ogf:network:stp:northernlight.ets:poz-0', 'urn:ogf:network:stp:northernlight.ets:poz-1', 'urn:ogf:network:stp:northernlight.ets:poz-2', 'urn:ogf:network:stp:northernlight.ets:poz-3']
    mapping['urn:ogf:network:nordu.net:2012:bi-nordu-uvalight']= ['urn:ogf:network:stp:northernlight.ets:uva-1780', 'urn:ogf:network:stp:northernlight.ets:uva-1781', 'urn:ogf:network:stp:northernlight.ets:uva-1782', 'urn:ogf:network:stp:northernlight.ets:uva-1783']
    mapping['urn:ogf:network:pionier.net.pl:2012:bi-pionier-nordu']= ['urn:ogf:network:stp:pionier.ets:cpha','urn:ogf:network:stp:pionier.ets:cphb','urn:ogf:network:stp:pionier.ets:cphc','urn:ogf:network:stp:pionier.ets:cphd']
    mapping['urn:ogf:network:startap.net:2012:bi-startap-gloriad']= ['urn:ogf:network:stp:starlight.ets:glo-06f4', 'urn:ogf:network:stp:starlight.ets:glo-06f5', 'urn:ogf:network:stp:starlight.ets:glo-o6f6', 'urn:ogf:network:stp:starlight.ets:glo-06f7']
    mapping['urn:ogf:network:uvalight.net:2012:bi-uvalight-nordu']= ['urn:ogf:network:stp:uvalight.ets:ndn-0', 'urn:ogf:network:stp:uvalight.ets:ndn-1', 'urn:ogf:network:stp:uvalight.ets:ndn-2', 'urn:ogf:network:stp:uvalight.ets:ndn-3']

def main():
    master = rdflib.Graph()
    master.bind("nml",NML)
    master.bind("nsi",NSI)
    master.bind("nmleth",NMLETH)
    master.bind("owl",OWL)
    master1 = rdflib.Graph()
    master1.bind("nml",NML)
    master1.bind("nsi",NSI)
    master1.bind("nmleth",NMLETH)
    master1.bind("owl",OWL)
    
    for name in ["aist","czechlight","esnet","geant","gloriad","jgnx","kddi-labs","krlight","max","netherlight","northernlight","pionier","starlight","uvalight","psnc"]:
        newname = getUrlName(name)
        topo = AGTopology("golesv1/%s.owl" % name)
        master1 += topo.storev1
        graph = topo.convert()
        graph.serialize("goles/%s.owl"%newname,format="pretty-xml")
        graph.serialize("goles/%s.n3"%newname,format="n3")
        master.bind(newname.replace(".","_"),topo.prefix)
        master += graph
    # Remove the isReference functions from the master topology,
    # since it has resolved all references already.
    for s,o in master.subject_objects(NML.isReference):
        master.remove((s,NML.isReference,o))
    master.serialize("master.owl",format="pretty-xml")
    master.serialize("master.n3",format="n3")
    master1.serialize("AutoGOLE-Topo.owl",format="xml")
    
    # Write the mapping file. Remember to undo the jerrification:
    f = open("mapping.txt",'w')
    jerrify(MAPPING)
    for x in MAPPING:
        if type(MAPPING[x]) is list:
            MAPPING[x].sort()
        f.write("%s: %s\n" % (x,MAPPING[x]))
    f.close()
if __name__ == '__main__':
    main()
