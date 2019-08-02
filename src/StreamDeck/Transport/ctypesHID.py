from .Transport import Transport

import hid

class ctypesHID(Transport):
	"""
	pyhidapi ctypes based wrapper because hidapi has severe stack corruption on Windows and appears unmaintained
	"""

	class Device(Transport.Device):
		def __init__(self, device_info):

			self.hid_info = device_info
			self.hid = hid.Device(vid=device_info['vendor_id'], pid=device_info['product_id'])

		def __del__(self):

			try:
				self.hid.hid_close()
			except:
				pass

		def open(self):

			self.hid = hid.Device(path=self.hid_info['path'])

		def close(self):

			self.hid.close()

		def connected(self):

			import hid

			devices = hid.enumerate()
			return any([d['path'] == self.hid_info['path'] for d in devices])

		def path(self):

			return self.hid_info['path']

		def write_feature(self, payload):

			if type(payload) is bytearray:
				payload = bytes(payload)

			return self.hid.send_feature_report(payload)

		def read_feature(self, report_id, length):

			return self.hid.get_feature_report(report_id, length)

		def write(self, payload):

			if type(payload) is bytearray:
				payload = bytes(payload)
			return self.hid.write(payload)

		def read(self, length):

			return self.hid.read(length)

	def enumerate(self, vid, pid):
		devices = hid.enumerate(vid=(vid if vid else 0), pid=(pid if pid else 0))

		return [ctypesHID.Device(d) for d in devices]
