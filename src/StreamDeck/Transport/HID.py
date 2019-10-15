#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

# pip3 install hid (https://pypi.org/project/hid/)

from .Transport import Transport


class HID(Transport):
    """
    USB HID transport layer, using the `hid` Python wrapper. This transport can
    be used to enumerate and communicate with HID devices.
    """

    class Device(Transport.Device):
        def __init__(self, device_info):
            """
            Creates a new HID device instance, used to send and receive HID
            reports from/to an attached USB HID device.

            :param dict() device_info: Device information dictionary describing
                                       a single unique attached USB HID device.
            """
            import hid

            self.hid_info = device_info
            self.hid = hid.Device(vid=device_info['vendor_id'], pid=device_info['product_id'])

        def __del__(self):
            """
            Deletion handler for the HID transport, automatically closing the
            device if it is currently open.
            """
            try:
                self.hid.close()
            except (IOError, ValueError):
                pass

        def open(self):
            """
            Opens the HID device for input/output. This must be called prior to
            sending or receiving any HID reports.

            .. seealso:: See :func:`~HID.Device.close` for the corresponding
                         close method.
            """
            import hid

            self.hid = hid.Device(path=self.hid_info['path'])

        def close(self):
            """
            Closes theHID  device for input/output.

            .. seealso:: See :func:`~~HID.Device.open` for the corresponding
                         open method.
            """
            self.hid.close()

        def connected(self):
            """
            Indicates if the physical HID device this instance is attached to
            is still connected to the host.

            :rtype: bool
            :return: `True` if the device is still connected, `False` otherwise.
            """
            import hid

            devices = hid.enumerate()
            return any([d['path'] == self.hid_info['path'] for d in devices])

        def path(self):
            """
            Retrieves the logical path of the attached HID device within the
            current system. This can be used to differentiate one HID device
            from another.

            :rtype: str
            :return: Logical device path for the attached device.
            """
            return self.hid_info['path']

        def write_feature(self, payload):
            """
            Sends a HID Feature report to the open HID device.

            :param enumerable() payload: Enumerate list of bytes to send to the
                                         device, as a feature report. The first
                                         byte of the report should be the Report
                                         ID of the report being sent.

            :rtype: int
            :return: Number of bytes successfully sent to the device.
            """
            if type(payload) is bytearray:
                payload = bytes(payload)

            return self.hid.send_feature_report(payload)

        def read_feature(self, report_id, length):
            """
            Reads a HID Feature report from the open HID device.

            :param int report_id: Report ID of the report being read.
            :param int length: Maximum length of the Feature report to read..

            :rtype: list(byte)
            :return: List of bytes containing the read Feature report. The
                     first byte of the report will be the Report ID of the
                     report that was read.
            """
            return self.hid.get_feature_report(report_id, length)

        def write(self, payload):
            """
            Sends a HID Out report to the open HID device.

            :param enumerable() payload: Enumerate list of bytes to send to the
                                         device, as an Out report. The first
                                         byte of the report should be the Report
                                         ID of the report being sent.

            :rtype: int
            :return: Number of bytes successfully sent to the device.
            """
            if type(payload) is bytearray:
                payload = bytes(payload)

            return self.hid.write(payload)

        def read(self, length):
            """
            Performs a blocking read of a HID In report from the open HID device.

            :param int length: Maximum length of the In report to read.

            :rtype: list(byte)
            :return: List of bytes containing the read In report. The first byte
                     of the report will be the Report ID of the report that was
                     read.
            """
            return self.hid.read(length)

    def enumerate(self, vid, pid):
        """
        Enumerates all available USB HID devices on the system.

        :param int vid: USB Vendor ID to filter all devices by, `None` if the
                        device list should not be filtered by vendor.
        :param int pid: USB Product ID to filter all devices by, `None` if the
                        device list should not be filtered by product.

        :rtype: list(HID.Device)
        :return: List of discovered USB HID devices.
        """

        if vid is None:
            vid = 0

        if pid is None:
            pid = 0

        import hid
        devices = hid.enumerate(vid=vid, pid=pid)

        return [HID.Device(d) for d in devices]

    @staticmethod
    def probe():
        """
        Attempts to determine if the backend is installed and usable.

        :rtype: bool
        :return: True if the backend is installed and is likely usable to
                 discover and communicate with attached devices.
        """
        try:
            import hid

            hid.enumerate(vid=0, pid=0)

            return True
        except:  # noqa: E722
            return False
