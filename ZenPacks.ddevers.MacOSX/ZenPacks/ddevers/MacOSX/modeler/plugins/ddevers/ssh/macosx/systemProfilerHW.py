#-------------------------------------------------------->
#	Copyright 2011 - David Devers, Getty Images
#
#	Mac OS X System Profiler Script
#-------------------------------------------------------->

_doc__ = """system_profiler
Determine hardware info using the Mac OS X system_profiler
"""

from Products.DataCollector.plugins.CollectorPlugin import CommandPlugin
from Products.DataCollector.plugins.DataMaps import MultiArgs


def normalize_space(s):
    """Return s stripped of leading/trailing whitespace
    and with internal runs of whitespace replaced by a single SPACE"""
    # This should be a str method :-(
    return ' '.join(s.split())


class systemProfilerHW(CommandPlugin):
	"""
Sample Output:

seadccopmac01:~ root# system_profiler SPHardwareDataType
Hardware:

    Hardware Overview:

      Model Name: Xserve
      Model Identifier: Xserve1,1
      Processor Name: Dual-Core Intel Xeon
      Processor Speed: 2 GHz
      Number Of Processors: 2
      Total Number Of Cores: 4
      L2 Cache (per processor): 4 MB
      Memory: 8 GB
      Bus Speed: 1.33 GHz
      Boot ROM Version: XS11.0080.B00
      SMC Version: 1.11f5
      LOM Revision: 1.2.1
      Serial Number: G871419MV2Q
	"""

	maptype = "DeviceMap"
	compname = ""
	command = "/usr/sbin/system_profiler SPHardwareDataType"

	def process(self, device, results, log):
		"""Collect hardware info for this device"""
		log.info("Processing hardware info for device %s",
			device.id)
		if not results:
			log.warn("%s returned no results!", self.command)
			return
		resultList = [normalize_space(i) for i in filter(None, results.split('\n'))]
		hwDict = dict([i.split(':') for i in resultList])
		for key, val in hwDict.items():
			hwDict[key] = val.strip()
		log.debug("Results = %s", str(hwDict))
		om = self.objectMap()
		om.setHWSerialNumber = hwDict["Serial Number"]
		om.setHWProductKey = MultiArgs(hwDict["Model Name"], "Apple")
		return om
