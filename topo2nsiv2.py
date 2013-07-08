#!/usr/bin/env python
import rdflib
import collections
import xml.etree.ElementTree as ET
from time import strftime
import sys

# This file implements an extremely limited converter for DTOX to NSI topology files
# It expects a certain format, and only converts those parts it knows about.

RDF = rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = rdflib.Namespace("http://www.w3.org/2000/01/rdf-schema#")
NML = rdflib.Namespace("http://schemas.ogf.org/nml/2013/05/base#")
NMLETH = rdflib.Namespace("http://schemas.ogf.org/nml/2012/10/ethernet#")
NSI = rdflib.Namespace("http://schemas.ogf.org/nsi/2013/09/topology#")
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
    "jgnx": "jgn-x.jp",
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
        return rdflib.term.URIRef("urn:ogf:network:%s:2013:topology" % target)
    else:
        return rdflib.term.URIRef("urn:ogf:network:%s:2013:ets" % target)

class AGXMLTopology:
    def __init__(self, url):
        """docstring for __init__"""
        self.url = url
        self.storev1 = rdflib.Graph()
        print "Parsing %s" % url
        self.storev1.parse(url)
        self.topo = self.storev1.value(predicate=RDF.type, object=DTOX.NSNetwork)
        self.urlname = getUrlName(self.topo.split(":")[-1][:-4])
        self.netname = getNetName(self.topo.split(":")[-1][:-4])
        self.prefix = "urn:ogf:network:%s:2013:" % self.urlname
        ET.register_namespace("nml",NML)
        ET.register_namespace("nsi",NSI)
        ET.register_namespace("nmleth",NMLETH)
    
    def make_xml():
         node = Element('foo')
         node.text = 'bar'

    def addPorts(self,stp,topo,targetUrl=None, targetNet=None):
        if targetUrl and targetNet:
            outPortRel = ET.SubElement(topo,"{%s}%s"%(NML,"Relation"), {"type":NML+"hasOutboundPort"})
            outPortGrp = ET.SubElement(outPortRel,"{%s}%s"%(NML,"PortGroup"), {"id":self.prefix+self.netname+"-"+targetNet})
            outLabel = ET.SubElement(outPortGrp,"{%s}%s"%(NML,"LabelGroup"), {"labeltype":NMLETH+"vlan"})
            outLabel.text = "1780-1783"
            outTargetRel = ET.SubElement(outPortGrp,"{%s}%s"%(NML,"Relation"), {"type":NML+"isAlias"})
            outTargetGrp = ET.SubElement(outTargetRel, "{%s}%s"%(NML,"PortGroup"), 
                    {"id":"urn:ogf:network:%s:2013:%s-%s" % (targetUrl,targetNet,self.netname)})

            inPortRel = ET.SubElement(topo,"{%s}%s"%(NML,"Relation"), {"type":NML+"hasInboundPort"})
            inPortGrp = ET.SubElement(inPortRel,"{%s}%s"%(NML,"PortGroup"), {"id":self.prefix+self.netname+"-"+targetNet})
            inLabel = ET.SubElement(inPortGrp,"{%s}%s"%(NML,"LabelGroup"), {"labeltype":NMLETH+"vlan"})
            inLabel.text = "1780-1783"
            inTargetRel = ET.SubElement(inPortGrp,"{%s}%s"%(NML,"Relation"), {"type":NML+"isAlias"})
            inTargetGrp = ET.SubElement(inTargetRel, "{%s}%s"%(NML,"PortGroup"), 
                    {"id":"urn:ogf:network:%s:2013:%s-%s" % (targetUrl,targetNet,self.netname)})
        else:
            outPortRel = ET.SubElement(topo,"{%s}%s"%(NML,"Relation"), {"type":NML+"hasOutboundPort"})
            outPortGrp = ET.SubElement(outPortRel,"{%s}%s"%(NML,"PortGroup"), {"id":self.prefix+stp+"-out"})
            outLabel = ET.SubElement(outPortGrp,"{%s}%s"%(NML,"LabelGroup"), {"labeltype":NMLETH+"vlan"})
            outLabel.text = "1780-1783"
            inPortRel = ET.SubElement(topo,"{%s}%s"%(NML,"Relation"), {"type":NML+"hasInboundPort"})
            inPortGrp = ET.SubElement(inPortRel,"{%s}%s"%(NML,"PortGroup"), {"id":self.prefix+stp+"-in"})
            inLabel = ET.SubElement(inPortGrp,"{%s}%s"%(NML,"LabelGroup"), {"labeltype":NMLETH+"vlan"})
            inLabel.text = "1780-1783"

    def convert(self):
        oldnsa = self.storev1.value(subject=self.topo,predicate=DTOX.managedBy)
        version = strftime("%Y%m%dT%H%M%SZ")
        nsa = ET.Element("{%s}%s" % (NSI,"NSA"),{"id": self.prefix+"nsa", "version": version })
        # Location
        oldloc = self.storev1.value(subject=self.topo,predicate=DTOX.locatedAt)
        location = ET.SubElement(nsa, "{%s}%s"%(NML,"Topology"), {"id":self.prefix+"location"})
        lat = ET.SubElement(location, "{%s}%s"%(NML, "lat"))
        lat.text = self.storev1.value(subject=oldloc,predicate=DTOX.lat)
        lng = ET.SubElement(location, "{%s}%s"%(NML, "long"))
        lng.text = self.storev1.value(subject=oldloc,predicate=DTOX.long)
        # Service
        
        # Relation: AdminContact
        admin = ET.SubElement(nsa, "{%s}%s"%(NML,"Relation"), {"type":NSI+"adminContact"})
        admin.text = "TODO: Convert this to vCard notation\n"+ self.storev1.value(subject=oldnsa,predicate=DTOX.adminContact)
        # Relation: peersWith
        peeringNets = []
        for stp in self.storev1.objects(self.topo,DTOX.hasSTP):
            target = self.storev1.value(subject=stp,predicate=DTOX.connectedTo)
            if target:
                targetUrl = getUrlName(target.split(":")[4][:-4])
                if targetUrl not in peeringNets:
                    pwrel = ET.SubElement(nsa, "{%s}%s"%(NML,"Relation"), {"type":NSI+"peersWith"})
                    peeringNSA = ET.SubElement(pwrel, "{%s}%s"%(NSI,"NSA"),{"id":"urn:ogf:network:%s:2013:nsa" % (targetUrl)})
                    peeringNets.append(targetUrl)   
        # Topology
        topo = ET.SubElement(nsa,"{%s}%s"%(NML,"Topology"), {"id":NSI+self.urlname})
        tname = ET.SubElement(topo,"{%s}%s"%(NML,"name"))
        tname.text = self.urlname
        # Ports
        localstps = []
        for stp in self.storev1.objects(self.topo,DTOX.hasSTP):
            target = self.storev1.value(subject=stp,predicate=DTOX.connectedTo)
            # We take off the invalid network urn prefix
            localstp = stp.split(":")[-1]
            # and then we take off the label suffix
            localstp = localstp.split("-")[0]
            if localstp not in localstps:
                if target:
                    # We take out the network name of the other end to pass as target
                    # We need both the URL name for the right prefix, and the netname for nicer postfixes
                    targetUrl = getUrlName(target.split(":")[4][:-4])
                    targetNet = getNetName(target.split(":")[4][:-4])
                    self.addPorts(localstp,topo,targetUrl,targetNet)
                else:
                    self.addPorts(localstp,topo)
                localstps.append(localstp)
        
        
        doc = ET.ElementTree(nsa)
        return doc
        
     
            
class AGTopology:
    def __init__(self, url):
        print "WARNING! This is not NML NSI syntax yet."
        self.url = url
        self.storev1 = rdflib.Graph()
        self.storev2 = rdflib.Graph()
        # try:
        print "Parsing %s" % url
        self.storev1.parse(url)
        # except Exception as e:
        #     print e
        self.topo = self.storev1.value(predicate=RDF.type, object=DTOX.NSNetwork)
        self.urlname = getUrlName(self.topo.split(":")[-1][:-4])
        self.netname = getNetName(self.topo.split(":")[-1][:-4])
        self.prefix = rdflib.Namespace("urn:ogf:network:%s:2013:" % self.urlname)
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
        self.storev2.add((nsa,NSI.manages,topo))
        oldnsa = self.storev1.value(subject=oldtopo,predicate=DTOX.managedBy)
        MAPPING[nsa] = oldnsa
        adminContact = self.storev1.value(subject=oldnsa,predicate=DTOX.adminContact)
        self.storev2.add((nsa,NSI.adminContact,adminContact))
        csProviderEndpoint = self.storev1.value(subject=oldnsa,predicate=DTOX.csProviderEndpoint)
        self.storev2.add((nsa,NSI.csProviderEndpoint,csProviderEndpoint))
        # Location
        location = rdflib.term.URIRef(self.prefix+"location")
        self.storev2.add((location,NML.name,rdflib.Literal(self.netname)))
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
            outTarget = rdflib.term.URIRef("urn:ogf:network:%s:2013:%s-%s" %
                                                 (targetUrl,targetNet,self.netname))
            inTarget = rdflib.term.URIRef("urn:ogf:network:%s:2013:%s-%s" %
                                                 (targetUrl,self.netname,targetNet))
            self.storev2.add((outPort,NML.isAlias,inTarget))
            self.storev2.add((inPort,NML.isAlias,outTarget))
            targettopo = getTargetTopo(targetUrl)
            self.storev2.add((targettopo,NML.hasInboundPort,inTarget))
            self.storev2.add((targettopo,NML.hasOutboundPort,outTarget))
            self.storev2.add((targettopo,RDF.type,NML.Topology))
            self.storev2.add((targettopo,RDF.type,OWL.NamedIndividual))
            self.storev2.add((targettopo,NSI.isReference,
                rdflib.Literal("https://raw.github.com/jeroenh/AutoGOLE-Topologies/nsiv2/goles/%s.owl" % targetUrl)))
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
        # self.storev2.add((topo,NML.hasBidirectionalPort,biport))
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

def OWLConversion():
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
    master1.bind("dtox",DTOX)
    
    # OWL
    for name in ["aist","czechlight","esnet","geant","gloriad","jgnx","kddi-labs","krlight","netherlight","northernlight","pionier","starlight","uvalight","psnc"]:
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

def XMLConversion():
    # XML
    for name in ["aist","czechlight","esnet","geant","gloriad","jgnx","kddi-labs","krlight","netherlight","northernlight","pionier","starlight","uvalight","psnc"]:
        newname = getUrlName(name)
        topo = AGXMLTopology("golesv1/%s.owl" % name)
        doc = topo.convert()
        doc.write("goles/%s.xml"%newname,encoding="UTF-8",xml_declaration=True)

def createMapping():
    # Write the mapping file. Remember to undo the jerrification:
    f = open("mapping.txt",'w')
    jerrify(MAPPING)
    for x in MAPPING:
        if type(MAPPING[x]) is list:
            MAPPING[x].sort()
        f.write("%s: %s\n" % (x,MAPPING[x]))
    f.close()
            
def main():
    # OWLConversion()
    XMLConversion()
    # createMapping()
if __name__ == '__main__':
    main()
