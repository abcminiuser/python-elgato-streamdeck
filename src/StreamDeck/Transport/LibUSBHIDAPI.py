#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import atexit
import ctypes
import platform
import threading

from .Transport import Transport, TransportError


class LibUSBHIDAPI(Transport):
    """
    USB HID transport layer, using the LibUSB HIDAPI dynamically linked library
    directly via ctypes.
    """

    class Library():
        HIDAPI_INSTANCE = None

        def _load_hidapi_library(self, library_search_list):
            """
            Loads the given LibUSB HIDAPI dynamic library from the host system,
            if available.

            :rtype: ctypes.CDLL
            :return: Loaded HIDAPI library instance, or None if no library was found.
            """

            if self.HIDAPI_INSTANCE:
                return self.HIDAPI_INSTANCE

            for lib_name in library_search_list:
                try:
                    type(self).HIDAPI_INSTANCE = ctypes.cdll.LoadLibrary(lib_name)
                    break
                except OSError:
                    pass
            else:
                return None

            class hid_device_info(ctypes.Structure):
                """
                Structure definition for the hid_device_info structure defined
                in the LibUSB HIDAPI library API.
                """
                pass

            hid_device_info._fields_ = [
                ('path', ctypes.c_char_p),
                ('vendor_id', ctypes.c_ushort),
                ('product_id', ctypes.c_ushort),
                ('serial_number', ctypes.c_wchar_p),
                ('release_number', ctypes.c_ushort),
                ('manufacturer_string', ctypes.c_wchar_p),
                ('product_string', ctypes.c_wchar_p),
                ('usage_page', ctypes.c_ushort),
                ('usage', ctypes.c_ushort),
                ('interface_number', ctypes.c_int),
                ('next', ctypes.POINTER(hid_device_info))
            ]

            self.HIDAPI_INSTANCE.hid_init.argtypes = []
            self.HIDAPI_INSTANCE.hid_init.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_exit.argtypes = []
            self.HIDAPI_INSTANCE.hid_exit.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_enumerate.argtypes = [ctypes.c_ushort, ctypes.c_ushort]
            self.HIDAPI_INSTANCE.hid_enumerate.restype = ctypes.POINTER(hid_device_info)

            self.HIDAPI_INSTANCE.hid_free_enumeration.argtypes = [ctypes.POINTER(hid_device_info)]
            self.HIDAPI_INSTANCE.hid_free_enumeration.restype = None

            self.HIDAPI_INSTANCE.hid_open_path.argtypes = [ctypes.c_char_p]
            self.HIDAPI_INSTANCE.hid_open_path.restype = ctypes.c_void_p

            self.HIDAPI_INSTANCE.hid_close.argtypes = [ctypes.c_void_p]
            self.HIDAPI_INSTANCE.hid_close.restype = None

            self.HIDAPI_INSTANCE.hid_set_nonblocking.argtypes = [ctypes.c_void_p, ctypes.c_int]
            self.HIDAPI_INSTANCE.hid_set_nonblocking.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_send_feature_report.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
            self.HIDAPI_INSTANCE.hid_send_feature_report.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_get_feature_report.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
            self.HIDAPI_INSTANCE.hid_get_feature_report.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_write.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
            self.HIDAPI_INSTANCE.hid_write.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_read.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char), ctypes.c_size_t]
            self.HIDAPI_INSTANCE.hid_read.restype = ctypes.c_int

            self.HIDAPI_INSTANCE.hid_init()
            atexit.register(self.HIDAPI_INSTANCE.hid_exit)

            return self.HIDAPI_INSTANCE

        def __init__(self):
            """
            Creates a new LibUSB HIDAPI library instance, used to interface with
            HID devices attached to the host system.
            """

            search_library_names = {
                "Windows": ["hidapi.dll", "libhidapi-0.dll"],
                "Linux": ["libhidapi-libusb.so", "libhidapi-libusb.so.0"],
                "Darwin": ["libhidapi.dylib"],
            }

            self.platform_name = platform.system()
            platform_search_library_names = search_library_names.get(self.platform_name)

            if not platform_search_library_names:
                raise TransportError("No suitable LibUSB HIDAPI library search names were found for this system.")

            self.hidapi = self._load_hidapi_library(platform_search_library_names)
            if not self.hidapi:
                raise TransportError("No suitable LibUSB HIDAPI library found on this system. Is the '{}' library installed?".format(platform_search_library_names[0]))

            self.mutex = threading.Lock()

        def enumerate(self, vendor_id=None, product_id=None):
            """
            Enumerates all available USB HID devices on the system.

            :param int vid: USB Vendor ID to filter all devices by, `None` if the
                            device list should not be filtered by vendor.
            :param int pid: USB Product ID to filter all devices by, `None` if the
                            device list should not be filtered by product.

            :rtype: list(dict())
            :return: List of discovered USB HID device attributes.
            """

            vendor_id = vendor_id or 0
            product_id = product_id or 0

            device_list = []

            with self.mutex:
                device_enumeration = self.hidapi.hid_enumerate(vendor_id, product_id)

                if device_enumeration:
                    current_device = device_enumeration

                    while current_device:
                        device_list.append({
                            'path': current_device.contents.path.decode('utf-8'),
                            'vendor_id': current_device.contents.vendor_id,
                            'product_id': current_device.contents.product_id,
                        })

                        current_device = current_device.contents.next

                self.hidapi.hid_free_enumeration(device_enumeration)

            return device_list

        def open_device(self, path):
            """
            Opens a HID device by its canonical path on the host system.

            :rtype: Handle
            :return: Device handle if opened successfully, None if open failed.
            """

            with self.mutex:
                if type(path) is not bytes:
                    path = bytes(path, 'utf-8')

                handle = self.hidapi.hid_open_path(path)

                if not handle:
                    raise TransportError("Could not open HID device.")

                self.hidapi.hid_set_nonblocking(handle, 1)

            return handle

        def close_device(self, handle):
            """
            Closes a HID device by its open device handle on the host system.

            :param Handle handle: Device handle to close.
            """
            if handle:
                with self.mutex:
                    self.hidapi.hid_close(handle)

        def send_feature_report(self, handle, data):
            """
            Sends a HID Feature report to an open HID device.

            :param Handle handle: Device handle to access.
            :param bytearray() data: Array of bytes to send to the device, as a
                                     feature report. The first byte of the
                                     report should be the Report ID of the
                                     report being sent.

            :rtype: int
            :return: Number of bytes successfully sent to the device.
            """
            if not handle:
                raise TransportError("No HID device.")

            with self.mutex:
                result = self.hidapi.hid_send_feature_report(handle, bytes(data), len(data))

            if result < 0:
                raise TransportError("Failed to write feature report (%d)" % result)

            return result

        def get_feature_report(self, handle, report_id, length):
            """
            Retrieves a HID Feature report from an open HID device.

            :param Handle handle: Device handle to access.
            :param int report_id: Report ID of the report being read.
            :param int length: Maximum length of the Feature report to read.

            :rtype: bytearray()
            :return: Array of bytes containing the read Feature report. The
                     first byte of the report will be the Report ID of the
                     report that was read.
            """
            if not handle:
                raise TransportError("No HID device.")

            # We may need to oversize our read due a bug in some versions of
            # HIDAPI. Only applied on Mac systems, as this will cause other
            # issues on other platforms.
            read_length = (length + 1) if self.platform_name == 'Darwin' else length

            data = ctypes.create_string_buffer(read_length)
            data[0] = report_id

            with self.mutex:
                result = self.hidapi.hid_get_feature_report(handle, data, len(data))

            if result < 0:
                raise TransportError("Failed to read feature report (%d)" % result)

            if length < read_length and result == read_length:
                # Mac HIDAPI 0.9.0 bug, we read one less than we expected (not including report ID).
                # We requested an over-sized report, so we actually got the amount we wanted.
                return data.raw

            # We read an extra byte (as expected). Just return the first length requested bytes.
            return data.raw[:length]

        def write(self, handle, data):
            """
            Writes a HID Out report to an open HID device.

            :param Handle handle: Device handle to access.
            :param bytearray() data: Array of bytes to send to the device, as an
                                     out report. The first byte of the report
                                     should be the Report ID of the report being
                                     sent.

            :rtype: int
            :return: Number of bytes successfully sent to the device.
            """
            if not handle:
                raise TransportError("No HID device.")

            with self.mutex:
                result = self.hidapi.hid_write(handle, bytes(data), len(data))

            if result < 0:
                raise TransportError("Failed to write out report (%d)" % result)

            return result

        def read(self, handle, length):
            """
            Performs a blocking read of a HID In report from an open HID device.

            :param Handle handle: Device handle to access.
            :param int length: Maximum length of the In report to read.

            :rtype: bytearray()
            :return: Array of bytes containing the read In report. The
                     first byte of the report will be the Report ID of the
                     report that was read.
            """
            if not handle:
                raise TransportError("No HID device.")

            data = ctypes.create_string_buffer(length)

            with self.mutex:
                result = self.hidapi.hid_read(handle, data, len(data))

            if result < 0:
                raise TransportError("Failed to read in report (%d)" % result)
            elif result == 0:
                return None

            return data.raw[:length]

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
            self.mutex = threading.Lock()

        def __del__(self):
            """
            Deletion handler for the HID transport, automatically closing the
            device if it is currently open.
            """
            self.close()

        def __exit__(self):
            """
            Exit handler for the HID transport, automatically closing the
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
            with self.mutex:
                if self.device_handle:
                    return

                self.device_handle = self.hidapi.open_device(self.device_info['path'])

        def close(self):
            """
            Closes the HID device for input/output.

            .. seealso:: See :func:`~~HID.Device.open` for the corresponding
                         open method.
            """
            with self.mutex:
                if self.device_handle:
                    self.hidapi.close_device(self.device_handle)
                    self.device_handle = None

        def connected(self):
            """
            Indicates if the physical HID device this instance is attached to
            is still connected to the host.

            :rtype: bool
            :return: `True` if the device is still connected, `False` otherwise.
            """

            with self.mutex:
                return any([d['path'] == self.device_info['path'] for d in self.hidapi.enumerate()])

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
            with self.mutex:
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
            with self.mutex:
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
            with self.mutex:
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
            with self.mutex:
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
