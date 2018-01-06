#         Python Strem Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# pip3 install hidapi (https://pypi.python.org/pypi/hidapi/0.7.99.post8)

import hid

class HIDAPI(object):
    class Device(object):
        def __init__(self, device_info):
            self.hid_info = device_info
            self.hid = hid.device()

        def open(self):
            self.hid.open_path(self.hid_info['path'])

        def close(self):
            self.hid.close()

        def connected(self):
            devices = hid.enumerate()
            return any([d['path'] == self.hid_info['path'] for d in devices])

        def write_feature(self, payload):
            return self.hid.send_feature_report(payload)

        def write(self, payload):
            return self.hid.write(payload)


    def enumerate(self, vid, pid):
        devices = hid.enumerate()

        if vid is not None:
            devices = [d for d in devices if d['vendor_id'] == vid]

        if pid is not None:
            devices = [d for d in devices if d['product_id'] == pid]

        return [HIDAPI.Device(d) for d in devices]
