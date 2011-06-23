#-------------------------------------------------------->
#	Copyright 2011 - David Devers, Getty Images
#
#	Mac OS X System Profiler Script
#-------------------------------------------------------->

_doc__ = """systemProfilerSW
Determine software info using the Mac OS X sw_vers command
"""

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin
from Products.DataCollector.plugins.DataMaps import MultiArgs

def normalize_space(s):
    return ' '.join(s.split())

class systemProfilerSW(CommandPlugin):
	"""
Sample Output:
ProductName:    Mac OS X Server
ProductVersion: 10.4.11
BuildVersion:   8S2169
	"""

	maptype = "DeviceMap"
	compname = ""
	command = "/usr/bin/sw_vers"

	def process(self, device, results, log):
		"""Collect OS info for this device"""
		log.info("Processing OS info for device %s",
			device.id)
		if not results:
			log.warn("%s returned no results!", self.command)
			return
		resultList = [normalize_space(i) for i in filter(None, results.split('\n'))]
		swDict = dict([i.split(':') for i in resultList])
		for key, val in swDict.items():
			swDict[key] = val.strip()
		osName = swDict['ProductName'] + " " + swDict['ProductVersion']
		log.debug("Results = %s", osName)
		om = self.objectMap()
		om.setOSProductKey = MultiArgs(osName, "Apple")
		return om
