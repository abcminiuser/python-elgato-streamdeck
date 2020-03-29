#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

from .Transport import Transport, TransportError

import ctypes


class LibUSBHIDAPI(Transport):
    """
    USB HID transport layer, using the `hid` Python wrapper. This transport can
    be used to enumerate and communicate with HID devices.
    """

    class Library():
        HIDAPI_LIBRARY_NAMES = [
            # Windows:
            'hidapi.dll',
            'libhidapi-0.dll'

            # Linux:
            'libhidapi-libusb.so',
            'libhidapi-libusb.so.0',

            # MacOS:
            'libhidapi.dylib',
        ]

        @staticmethod
        def _setup_hidapi_api_types(hidapi):
            class hid_device_info(ctypes.Structure):
                pass

            hid_device_info._fields_ = [
                ("path", ctypes.c_char_p),
                ("vendor_id", ctypes.c_ushort),
                ("product_id", ctypes.c_ushort),
                ("serial_number", ctypes.c_wchar_p),
                ("release_number", ctypes.c_ushort),
                ("manufacturer_string", ctypes.c_wchar_p),
                ("product_string", ctypes.c_wchar_p),
                ("usage_page", ctypes.c_ushort),
                ("usage", ctypes.c_ushort),
                ("interface_number", ctypes.c_int),
                ("next", ctypes.POINTER(hid_device_info))
            ]

            hidapi.hid_init.argtypes = []
            hidapi.hid_init.restype = ctypes.c_int

            hidapi.hid_exit.argtypes = []
            hidapi.hid_exit.restype = ctypes.c_int

            hidapi.hid_enumerate.argtypes = [ctypes.c_short, ctypes.c_short]
            hidapi.hid_enumerate.restype = ctypes.POINTER(hid_device_info)

            hidapi.hid_free_enumeration.argtypes = [ctypes.POINTER(hid_device_info)]
            hidapi.hid_free_enumeration.restype = None

            hidapi.hid_open_path.argtypes = [ctypes.c_char_p]
            hidapi.hid_open_path.restype = ctypes.c_void_p

            hidapi.hid_close.argtypes = [ctypes.c_void_p]
            hidapi.hid_close.restype = None

            hidapi.hid_send_feature_report.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
            hidapi.hid_send_feature_report.restype = ctypes.c_int

            hidapi.hid_get_feature_report.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
            hidapi.hid_get_feature_report.restype = ctypes.c_int

            hidapi.hid_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
            hidapi.hid_write.restype = ctypes.c_int

            hidapi.hid_read.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
            hidapi.hid_read.restype = ctypes.c_int

        def _load_hidapi_library(self):
            for lib_name in self.HIDAPI_LIBRARY_NAMES:
                try:
                    return ctypes.cdll.LoadLibrary(lib_name)
                except OSError:
                    pass

            return None

        def __init__(self):
            self.hidapi = self._load_hidapi_library()
            if not self.hidapi:
                raise TransportError("No suitable HIDAPI library found on this system.")

            self._setup_hidapi_api_types(self.hidapi)

            self.hidapi.hid_init()

        def __del__(self):
            """
            Deletion handler for the StreamDeck, automatically closing the transport
            if it is currently open and terminating the transport reader thread.
            """
            try:
                self.hidapi.hid_exit()
            except (OSError, AttributeError):
                pass

        def enumerate(self, vendor_id=0, product_id=0):
            device_enumeration = self.hidapi.hid_enumerate(vendor_id, product_id)

            device_list = []

            if device_enumeration:
                current_device = device_enumeration.contents
                while current_device:
                    device_list.append({
                        "path": current_device.path,
                        "vendor_id": current_device.vendor_id,
                        "product_id": current_device.vendor_id,
                    })

                    current_device = current_device.next

            self.hidapi.hid_free_enumeration(device_enumeration)

            return device_list

        def open_device(self, path):
            return self.hidapi.hid_open_path(path)

        def close_device(self, handle):
            if not handle:
                return TransportError("No HID device.")

            return self.hidapi.hid_close(handle)

        def send_feature_report(self, handle, data):
            if not handle:
                return TransportError("No HID device.")

            result = self.hidapi.hid_send_feature_report(handle, data, len(data))
            if result < 0:
                raise TransportError("Failed to write feature report (%d)" % result)

        def get_feature_report(self, handle, report_id, size):
            if not handle:
                return TransportError("No HID device.")

            data = ctypes.create_string_buffer(size)
            data[0] = report_id

            self.hidapi.hid_get_feature_report(handle, data, len(data))
            return data.raw[:size]

        def write(self, handle, data):
            if not handle:
                return TransportError("No HID device.")

            return self.hidapi.hid_write(handle, data, len(data))

        def read(self, handle, size):
            if not handle:
                return TransportError("No HID device.")

            data = ctypes.create_string_buffer(size)

            self.hidapi.hid_read(handle, data, len(data))
            return data.raw[:size]

    class Device(Transport.Device):
        def __init__(self, hidapi, device_info):
            """
            Creates a new HID device instance, used to send and receive HID
            reports from/to an attached USB HID device.

            :param dict() device_info: Device information dictionary describing
                                       a single unique attached USB HID device.
            """
            self.hidapi = hidapi
            self.device_info = device_info
            self.device_handle = None

        def __del__(self):
            """
            Deletion handler for the HID transport, automatically closing the
            device if it is currently open.
            """
            self.close()

        def open(self):
            """
            Opens the HID device for input/output. This must be called prior to
            sending or receiving any HID reports.

            .. seealso:: See :func:`~HID.Device.close` for the corresponding
                         close method.
            """
            if self.device_handle:
                self.close()

            self.device_handle = self.hidapi.open_device(self.device_info["path"])

        def close(self):
            """
            Closes the HID device for input/output.

            .. seealso:: See :func:`~~HID.Device.open` for the corresponding
                         open method.
            """
            if self.device_handle:
                try:
                    self.hidapi.close_device(self.device_handle)
                    self.device_handle = None
                except Exception:  # nosec
                    pass

        def connected(self):
            """
            Indicates if the physical HID device this instance is attached to
            is still connected to the host.

            :rtype: bool
            :return: `True` if the device is still connected, `False` otherwise.
            """
            return any([d['path'] == self.hid_info['path'] for d in self.hidapi.enumerate()])

        def path(self):
            """
            Retrieves the logical path of the attached HID device within the
            current system. This can be used to differentiate one HID device
            from another.

            :rtype: str
            :return: Logical device path for the attached device.
            """
            return self.device_info['path']

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

            return self.hidapi.send_feature_report(self.device_handle, payload)

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
            return self.hidapi.get_feature_report(self.device_handle, report_id, length)

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

            return self.hidapi.write(self.device_handle, payload)

        def read(self, length):
            """
            Performs a blocking read of a HID In report from the open HID device.

            :param int length: Maximum length of the In report to read.

            :rtype: list(byte)
            :return: List of bytes containing the read In report. The first byte
                     of the report will be the Report ID of the report that was
                     read.
            """

            return self.hidapi.read(self.device_handle, length)

    @staticmethod
    def probe():
        """
        Attempts to determine if the back-end is installed and usable. It is
        expected that probe failures throw exceptions detailing their exact
        cause of failure.
        """

        LibUSBHIDAPI.Library()

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

        hidapi = LibUSBHIDAPI.Library()

        return [LibUSBHIDAPI.Device(hidapi, d) for d in hidapi.enumerate(vendor_id=vid, product_id=pid)]
