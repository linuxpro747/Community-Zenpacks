#!/usr/bin/python -E
# have to unset PYTHONHOME and PYTHONPATH to avoid getting the zenoss python tree....

"""libvirt based statistics fetcher

This script is used for obtaining information from libvirt based virtualization
servers and exporting them in a NAGIOS/Zenoss compatible style format.

"""

__version__ = "0.2"


import libvirt
import getopt
import sys
import pickle
# --TODO-- work around for cross python version differences in elementtree
try:
    from xml.etree import ElementTree
    mypythonversion = '2.6'
except ImportError:
    from elementtree.ElementTree import ElementTree
    from elementtree.ElementTree import fromstring
    mypythonversion = '2.4'


args = sys.argv[1:]
shortopt='c:l:u:H:d:i:n:g:s:hvr'
longopts=['help']
connecttype = 'qemu+ssh://'
socket = '/var/run/libvirt/libvirt-sock-ro'
username = 'zenoss'
hostname = 'localhost'
datatype = 'list'
domain = -1
domainname = ''
disk = ''
interface = ''
verbose = 0
humanreadable = 0


def help(status=0):
    print "check_libvirt.py [-u username] [-c connecttype] [-H hostname] [-l datatype] [-h] [-v]"
    print "-c connecttype   (see the libvirt docs for more info about connecturi format)"
    print "-r		    print in human readable format instead of default NAGIOS format"
    print "-l datatype	    type of data to lookup"
    print "			(list, domain, interface, interfacelist, disk, disklist, memory, cpu, all, modeler)"
    print "-s socket        path to the readonly libvirt socket on the remote host"
    print "-g domain ID#    the ID number of the domain to query"
    print "-n domain name   the name of the domain to query - can be used instead of -g" 
    print "-d disk-device   the device name of the disk to gets stats for (e.g. vda, hda, .etc.)"
    print "-i net-interface the interface name to get stats for (e.g. vnet1, vnet2, etc.)"
    print "-u username	    username to connect as to the remote libvirt host"
    print "-H hostname	    hostname of the remote libvirt host"
    print "-v		    enable verbose mode"
    sys.exit(status)

"""
Print data in either humanly readable or NAGIOS format (the default)
"""
def print_data(data):
    if humanreadable:
	print "\n".join([str(x)+'='+str(data[x]) for x in data.keys()])
    else:
	print '|'+' '.join([str(x)+'='+str(data[x]) for x in data.keys()])

def get_disk_devices(dom):
    if mypythonversion == '2.6':
        etree=ElementTree.fromstring(dom.XMLDesc(0))
    else:
        etree=fromstring(dom.XMLDesc(0))
    devs=[]
    for target in etree.findall("devices/disk/target"):
	dev=target.get("dev")
	if not dev in devs:
	    devs.append(dev)
    return devs

def get_interface_devices(dom):
    if mypythonversion == '2.6':
        etree=ElementTree.fromstring(dom.XMLDesc(0))
    else:
        etree=fromstring(dom.XMLDesc(0))
    devs=[]
    for target in etree.findall("devices/interface/target"):
	dev=target.get("dev")
	if not dev in devs:
	    devs.append(dev)
    return devs

def get_data_domain(conn,domain,domainname):
    """Get data specific to this domain
       --TODO-- I am totaling up the interface and disk totals since I don't have dynamic datapoint support in the zenoss modeler plugin yet....
    """
    try:
	if domain > 0:
	    dom=conn.lookupByID(domain)
	else:
	    dom=conn.lookupByName(domainname)
    except :
	print '|'
	return
    info = dom.info()
    data = dict()
    data['ostype']=dom.OSType()
    data['uuidstring']=dom.UUIDString()
    data['state']=info[0]
    data['maxmemory']=info[1]
    data['memory']=info[2]
    data['nrvirtcpu']=info[3]
    data['cputime']=info[4]
    ifdevs = get_interface_devices(dom)
    dps = ('rxbytes','rxpackets','rxerrs','rxdrops','txbytes','txpackets','txerrs','txdrops')
    for dp in dps:
	data['if_total_' + dp] = 0
    for ifdev in ifdevs:
	if data['state'] == 1:
	    if_stats=dom.interfaceStats(ifdev)
	i = 0
        for dp in dps:
	    if data['state'] == 1:
		data['if_' + ifdev + '_' + dp] = if_stats[i]
		data['if_total_' + dp] += if_stats[i]
	    else:
		data['if_' + ifdev + '_' + dp] = 0
	    i += 1
    diskdevs = get_disk_devices(dom)
    dps = ('readrequests','readbytes','writerequests','writebytes')
    for dp in dps:
	data['disk_total_' + dp]=0
    for disk in diskdevs:
	if data['state'] == 1:
	    disk_stats=dom.blockStats(disk)
	i = 0
	for dp in dps:
	    if data['state'] == 1:
		data['disk_' + disk + '_' + dp]=disk_stats[i]
		data['disk_total_' + dp]+=disk_stats[i]
	    else:
		data['disk_' + disk + '_' + dp]=0
	    i += 1
    print_data(data)

def get_data_disklist(conn,domain,domainname):
    """Get a list of disks for this domain"""
    if domain > 0:
	dom=conn.lookupByID(domain)
    else:
	dom=conn.lookupByName(domainname)
    data = dict()
    for dev in get_disk_devices(dom):
	data[dev] = dev
    print_data(data)
	

def get_data_disk(conn,domain,domainname,disk):
    """
     Get disk stats about an individual disk
      domain will be a number returned by get_data_list
      disk will be something like vda, hda, etc...
    """
    if domain > 0:
	dom=conn.lookupByID(domain)
    else:
	dom=conn.lookupByName(domainname)
    disk_stats=dom.blockStats(disk)
    data = dict()
    data['readrequests']=disk_stats[0]
    data['readbytes']=disk_stats[1]
    data['writerequests']=disk_stats[2]
    data['writebytes']=disk_stats[3]
    print_data(data)

def get_data_memory(conn,domain,domainname):
    """Get memory stats on this domain"""
    print "Not implemented yet - not available until at least libvirt 0.7.5"
    if domain > 0:
	dom=conn.lookupByID(domain)
    else:
	dom=conn.lookupByName(domainname)
    #mem_stats=dom.memoryStats()
    exit(1)

def get_data_cpu(conn,domain,domainname):
    """Get data on CPU"""
    if domain > 0:
	dom=conn.lookupByID(domain)
    else:
	dom=conn.lookupByName(domainname)
    data = dict()
    data['vcpus']=dom.vcpus()
    print_data(data)

def get_data_interface(conn,domain,domainname,interface):
    """Get stats on this interface for this domain"""
    if domain > 0:
	dom=conn.lookupByID(domain)
    else:
	dom=conn.lookupByName(domainname)
    if_stats=dom.interfaceStats(interface)
    data = dict()
    data['rxbytes'] = if_stats[0]
    data['rxpackets'] = if_stats[1]
    data['rxerrs'] = if_stats[2]
    data['rxdrops'] = if_stats[3]
    data['txbytes'] = if_stats[4]
    data['txpackets'] = if_stats[5]
    data['txerrs'] = if_stats[6]
    data['txdrops'] = if_stats[7]
    print_data(data)

def get_data_interfacelist(conn,domain,domainname):
    """List all interfaces on this domain"""
    if domain > 0:
	dom=conn.lookupByID(domain)
    else:
	dom=conn.lookupByName(domainname)
    data = dict()
    for dev in get_interface_devices(dom):
	data[dev] = dev
    print_data(data)

def get_data_list(conn):
    """List all domains on this host"""
    data = dict()
    for id in conn.listDomainsID():
	dom=conn.lookupByID(id)
	data[id]=dom.name()
    print_data(data)

def get_data_modeler(conn):
    """List all domains on this host"""
    data = dict()
    for name in conn.listDefinedDomains():
	dom=conn.lookupByName(name)
	data[name]=dict()
	data[name]['name'] = dom.name()
	data[name]['ostype'] = dom.OSType()
	data[name]['uuidstring'] = dom.UUIDString()
	data[name]['maxmemory'] = dom.maxMemory()
	#data[name]['vcpus'] = dom.vcpus()
	info = dom.info()
	data[name]['state'] = info[0]
	data[name]['nrvirtcpus'] = info[3]
	data[name]['disks'] = get_disk_devices(dom)
	data[name]['interfaces'] = get_interface_devices(dom)
    for id in conn.listDomainsID():
	dom=conn.lookupByID(id)
	data[id]=dict()
	data[id]['name'] = dom.name()
	data[id]['ostype'] = dom.OSType()
	data[id]['uuidstring'] = dom.UUIDString()
	data[id]['maxmemory'] = dom.maxMemory()
	#data[id]['vcpus'] = dom.vcpus()
	info = dom.info()
	data[id]['state'] = info[0]
	data[id]['nrvirtcpus'] = info[3]
	data[id]['disks'] = get_disk_devices(dom)
	data[id]['interfaces'] = get_interface_devices(dom)
    print pickle.dumps(data)
    #print pickle.loads(pickle.dumps(data))

def get_data_all(conn):
    """Print all data for all domains"""
    print 'Listing running domains'
    for id in conn.listDomainsID():
	dom=conn.lookupByID(id)
	print dom.name()# ,dom.blockStats()
	print "\tid:", id
	print "\tostype:", dom.OSType()
	print "\tuuidstring:", dom.UUIDString()
	print "\tmaxmemory:", dom.maxMemory()
	print "\tvcpus:", dom.vcpus()
	info = dom.info()
	state = info[0]
	maxMem = info[1]
	memory = info[2]
	nrVirtCpu = info[3]
	cpuTime = info[4]
	print "\tinfo:", "state:",state,"maxMem:", maxMem,"memory:", memory,"nrVirtCpu:", nrVirtCpu,"cpuTime:", cpuTime
	#print "\tschedulerParameters:", dom.schedulerParameters()
	#print "\tschedulerType:", dom.schedulerType() # ?
	# print dom.XMLDesc, # details of domain config in XML format
	for dev in get_disk_devices(dom):
	    print "\tdiskdev: ",dev
	    disk_stats=dom.blockStats(dev)
	    print "\tdiskstats:","rr:",disk_stats[0],"rB:",disk_stats[1],"wr:",disk_stats[2],"wB:",disk_stats[3]
	    # disk_stats[0] = Read Requests
	    # disk_stats[1] = Read Bytes
	    # disk_stats[2] = Write Requests
	    # disk_stats[3] = Written Bytes
	for dev in get_interface_devices(dom):
	    interface_stats=dom.interfaceStats(dev)
	    rx_bytes = interface_stats[0]
	    rx_packets = interface_stats[1]
	    rx_errs = interface_stats[2]
	    rx_drop = interface_stats[3]
	    tx_bytes = interface_stats[4]
	    tx_packets = interface_stats[5]
	    tx_errs = interface_stats[6]
	    tx_drop = interface_stats[7]
	    print "\trx_ifstats:","rx_bytes: ",rx_bytes,"rx_packets:", rx_packets,"rx_errs:", rx_errs,"rx_drop:", rx_drop
	    print "\ttx_ifstats:","tx_bytes: ",tx_bytes,"tx_packets:", tx_packets,"tx_errs:", tx_errs,"tx_drop:", tx_drop
	# dom.memoryStats only exists in libvirt as of version 0.7.5 ....

    print 'Listing defined domains'
    for id in conn.listDefinedDomains():
	dom=conn.lookupByName(id)
	print dir(dom)

if __name__=='__main__':
    opts, args = getopt.getopt(args,shortopt,longopts)
    for opt in opts:
	if opt[0] == "-h":
	    help()
	elif opt[0] == "-H":
	    hostname = opt[1]
	elif opt[0] == "-u":
	    username = opt[1]
	elif opt[0] == "-c":
	    connecttype = opt[1]
	elif opt[0] == "-l":
	    datatype = opt[1]
	elif opt[0] == "-g":
	    domain = int(opt[1])
	elif opt[0] == "-n":
	    domainname = opt[1]
        elif opt[0] == "-2":
            socket = opt[1]
	elif opt[0] == "-i":
	    interface = opt[1]
	elif opt[0] == "-d":
	    disk = opt[1]
	elif opt[0] == "-v":
	    verbose = 1
	elif opt[0] == "-r":
	    humanreadable = 1

    #conn=libvirt.openReadOnly('qemu+ssh://test8virt3/')
    #conn=libvirt.openReadOnly('remote://test8virt3/')
    #conn=libvirt.openReadOnly('qemu://test8virt3/system')
    conn=libvirt.openReadOnly(connecttype+username+'@'+hostname+'/system'+'?socket='+socket)


    if datatype == 'list':
	get_data_list(conn)
    elif datatype == 'modeler': # used for passing information to the zenoss modeler plugin.....
	get_data_modeler(conn)
    elif datatype == 'all':
	get_data_all(conn)
    elif datatype == 'disk':
	get_data_disk(conn,domain,domainname,disk)
    elif datatype == 'disklist':
	get_data_disklist(conn,domain,domainname)
    elif datatype == 'memory':
	get_data_memory(conn,domain,domainname)
    elif datatype == 'cpu':
	get_data_cpu(conn,domain,domainname)
    elif datatype == 'domain':
	get_data_domain(conn,domain,domainname)
    elif datatype == 'interface':
	get_data_interface(conn,domain,domainname,interface)
    elif datatype == 'interfacelist':
	get_data_interfacelist(conn,domain,domainname)
    else:
	print "Unrecognized datatype:",datatype
	help(1)

