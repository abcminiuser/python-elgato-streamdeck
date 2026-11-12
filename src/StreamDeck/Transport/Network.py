#         Python Stream Deck Library
#      Released under the MIT license
#
#   dean [at] fourwalledcubicle [dot] com
#         www.fourwalledcubicle.com
#

import functools
import itertools
import queue
import socket
import struct
import threading
import time

from .Transport import Transport, TransportError


class Network(Transport):
    """
    Network transport layer, for StreamDeck devices attached to an Elgato
    Stream Deck Network Dock. Docked devices can be discovered via mDNS.
    """

    SERVICE_TYPE = "_elg._tcp.local."
    DISCOVERY_TIME = 2.0

    # Discovery results are reused for this long, by both enumerate() and
    # Device.connected(), as each browse blocks for DISCOVERY_TIME.
    DISCOVERY_CACHE_TIME = 10.0

    class Protocol:
        """
        Messages to and from the Network Dock are 32 bytes: a 16 byte header
        and a 16 byte payload as follows:

        offset  size  field
        0       4     magic 43 93 8a 41
        4       2     flags (u16 LE)
        6       1     operation
        7       1     reserved?
        8       4     message ID (u32 LE), echoed in responses
        12      4     payload length (u32 LE)

        The actual data are the same format the device uses over USB (HID).
        """

        MAGIC = b"\x43\x93\x8a\x41"
        HEADER = struct.Struct("<4sHBBII")

        FLAG_HID = 0x8000
        FLAG_RESPONSE = 0x0100

        OP_WRITE = 0
        OP_SET_FEATURE = 1
        OP_GET_FEATURE = 2

        MAX_MESSAGE_ID = 0xFFFFFFFF

        @classmethod
        def encode(cls, payload, op=0, flags=0, msg_id=0):
            return cls.HEADER.pack(cls.MAGIC, flags, op, 0, msg_id, len(payload)) + bytes(payload)

        @classmethod
        def decode(cls, buffer):
            """
            Removes all complete frames from the start of the given bytearray,
            returning them as a list of (flags, op, msg_id, payload) tuples.
            """
            frames = []

            while len(buffer) >= cls.HEADER.size:
                magic, flags, op, _, msg_id, length = cls.HEADER.unpack_from(buffer)
                if magic != cls.MAGIC:
                    raise TransportError("Invalid frame received from network device.")

                end = cls.HEADER.size + length
                if len(buffer) < end:
                    break

                frames.append((flags, op, msg_id, bytes(buffer[cls.HEADER.size : end])))
                del buffer[:end]

            return frames

    class Device(Transport.Device):
        # The dock drops clients that send nothing for a few seconds.
        KEEPALIVE_INTERVAL = 1.0
        TIMEOUT = 3.0

        # The dock sends a status message every few seconds; a connection
        # that stays silent for longer than this is considered dead.
        DEAD_PEER_TIMEOUT = 10.0

        # The dock expects get-feature requests padded to its report buffer size.
        GET_FEATURE_REQUEST_LENGTH = 512

        class Connection:
            """Single TCP connection to the dock.
            
            A new instance is created on every open(), such that other
            connections do not affect one another.
            """

            def __init__(self, sock):
                self.socket = sock
                self.stop = threading.Event()
                self.send_lock = threading.Lock()
                self.pending_lock = threading.Lock()
                self.pending = dict()
                self.input_reports = queue.Queue()
                self.threads = []

            def shutdown(self):
                """Marks the connection dead and unblocks any thread using the socket."""
                self.stop.set()

                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

        def __init__(self, host, port, vendor_id, product_id, is_present):
            self.host = host
            self.port = port
            self._vendor_id = vendor_id
            self._product_id = product_id
            self.is_present = is_present
            print(is_present)

            self.mutex = threading.Lock()
            self.connection = None
            self.message_ids = itertools.count()

        def __del__(self):
            self.close()

        def __exit__(self, type, value, traceback):
            self.close()

        def open(self):
            with self.mutex:
                if self.connection:
                    return

                try:
                    sock = socket.create_connection((self.host, self.port), self.TIMEOUT)
                except OSError as e:
                    raise TransportError(f"Could not connect to {self.path()}.") from e

                # Keep a timeout: it bounds blocked sends, and lets the reader
                # notice a dead peer.
                sock.settimeout(self.TIMEOUT)

                connection = Network.Device.Connection(sock)
                connection.threads = [
                    threading.Thread(target=self._reader, args=(connection,), daemon=True),
                    threading.Thread(target=self._keepalive, args=(connection,), daemon=True),
                ]
                self.connection = connection

            for thread in connection.threads:
                thread.start()

        def close(self):
            with self.mutex:
                connection, self.connection = self.connection, None

            if connection is None:
                return

            connection.shutdown()

            for thread in connection.threads:
                if thread is not threading.current_thread():
                    thread.join(timeout=self.TIMEOUT)

            connection.socket.close()

        def is_open(self):
            with self.mutex:
                return self.connection is not None

        def connected(self):
            with self.mutex:
                connection = self.connection

            if connection is not None and connection.stop.is_set():
                return False

            # The dock stops advertising a device when it is undocked.
            print(f"{self.is_present()=}")
            return self.is_present()

        def vendor_id(self):
            return self._vendor_id

        def product_id(self):
            return self._product_id

        def path(self):
            return f"{self.host}:{self.port}"

        def write_feature(self, payload):
            self._send(self._open_connection(), payload, Network.Protocol.OP_SET_FEATURE)
            return len(payload)

        def read_feature(self, report_id, length):
            connection = self._open_connection()
            msg_id = self._next_message_id()
            response = queue.Queue(maxsize=1)

            with connection.pending_lock:
                connection.pending[msg_id] = response

            try:
                request = bytearray(max(length, self.GET_FEATURE_REQUEST_LENGTH))
                request[0] = report_id
                self._send(connection, request, Network.Protocol.OP_GET_FEATURE, msg_id)

                payload = response.get(timeout=self.TIMEOUT)
            except queue.Empty:
                raise TransportError(f"No response reading feature report {report_id}.") from None
            finally:
                with connection.pending_lock:
                    connection.pending.pop(msg_id, None)

            if payload is None:
                raise TransportError("Network device disconnected.")

            return payload[:length]

        def write(self, payload):
            self._send(self._open_connection(), payload, Network.Protocol.OP_WRITE)
            return len(payload)

        def read(self, length):  # pyright: ignore[reportIncompatibleMethodOverride]
            # As with USB, returns None when no report is waiting.
            with self.mutex:
                connection = self.connection

            if connection is None:
                raise TransportError("Network device is not open.")

            try:
                payload = connection.input_reports.get_nowait()
            except queue.Empty:
                if connection.stop.is_set():
                    raise TransportError("Network device disconnected.") from None
                return None

            if payload is None:
                raise TransportError("Network device disconnected.")

            return payload[:length]

        def _open_connection(self):
            with self.mutex:
                connection = self.connection

            if connection is None:
                raise TransportError("Network device is not open.")
            if connection.stop.is_set():
                raise TransportError("Network device disconnected.")

            return connection

        def _next_message_id(self):
            # IDs are a u32 on the wire; wrap around, skipping 0.
            return next(self.message_ids) % Network.Protocol.MAX_MESSAGE_ID + 1

        def _send(self, connection, payload, op, msg_id=None):
            if msg_id is None:
                msg_id = self._next_message_id()

            frame = Network.Protocol.encode(payload, op, Network.Protocol.FLAG_HID, msg_id)

            with connection.send_lock:
                try:
                    connection.socket.sendall(frame)
                except OSError as e:
                    # A partially sent frame leaves the stream unusable.
                    connection.shutdown()
                    raise TransportError("Failed to send to network device.") from e

        def _keepalive(self, connection):
            keepalive = Network.Protocol.encode(b"")

            while not connection.stop.wait(self.KEEPALIVE_INTERVAL):
                with connection.send_lock:
                    try:
                        connection.socket.sendall(keepalive)
                    except OSError:
                        connection.shutdown()
                        break

        def _reader(self, connection):
            buffer = bytearray()
            last_received = time.monotonic()

            try:
                while not connection.stop.is_set():
                    try:
                        data = connection.socket.recv(65536)
                    except TimeoutError:
                        if time.monotonic() - last_received > self.DEAD_PEER_TIMEOUT:
                            break
                        continue

                    if not data:
                        break

                    last_received = time.monotonic()
                    buffer += data
                    for flags, op, msg_id, payload in Network.Protocol.decode(buffer):
                        self._dispatch(connection, flags, op, msg_id, payload)
            except (OSError, TransportError):
                pass
            finally:
                connection.shutdown()
                connection.input_reports.put(None)

                with connection.pending_lock:
                    pending = list(connection.pending.values())
                for response in pending:
                    try:
                        response.put_nowait(None)
                    except queue.Full:
                        pass

        def _dispatch(self, connection, flags, op, msg_id, payload):
            if not flags & Network.Protocol.FLAG_HID:
                # Dock status messages (e.g. connected client count); not HID traffic.
                return

            if flags & Network.Protocol.FLAG_RESPONSE:
                with connection.pending_lock:
                    response = connection.pending.get(msg_id)

                if response is not None:
                    try:
                        response.put_nowait(payload)
                    except queue.Full:
                        pass
            elif op == Network.Protocol.OP_WRITE:
                connection.input_reports.put(payload)

    def __init__(self):
        self.services = dict()
        self.services_time = None
        self.discovery_lock = threading.Lock()

    @staticmethod
    def probe():
        import zeroconf  # noqa: F401

    @staticmethod
    def _parse_service(info):
        """
        Returns (host, port, vid, pid) for a docked device's service info, or
        None if the service is not a usable docked device.
        """
        from zeroconf import IPVersion

        if info is None:
            return None

        properties = {k.decode(): v.decode() for k, v in info.properties.items() if v is not None}

        # Only docked devices advertise a USB VID/PID; the dock itself does not.
        if "vid" not in properties or "pid" not in properties:
            return None

        # Prefer IPv4: an IPv6 link-local address cannot be connected to
        # without its interface scope.
        addresses = info.parsed_addresses(IPVersion.V4Only) or info.parsed_addresses()
        if not addresses:
            return None

        return (addresses[0], info.port, int(properties["vid"], 16), int(properties["pid"], 16))

    def _discover(self):
        from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

        services = dict()

        class Listener(ServiceListener):
            def add_service(self, zc, type_, name):
                try:
                    service = Network._parse_service(zc.get_service_info(type_, name))
                except (UnicodeDecodeError, ValueError):
                    # Malformed TXT records, e.g. from an unrelated device.
                    service = None

                if service is not None:
                    services[name] = service
                else:
                    services.pop(name, None)

            update_service = add_service

            def remove_service(self, zc, type_, name):
                services.pop(name, None)

        zc = Zeroconf()
        try:
            ServiceBrowser(zc, Network.SERVICE_TYPE, Listener())
            time.sleep(self.DISCOVERY_TIME)
        finally:
            zc.close()

        return services

    def _get_services(self):
        # TODO: this fails after a couple of iterations
        with self.discovery_lock:
            now = time.monotonic()
            if self.services_time is None or now - self.services_time > self.DISCOVERY_CACHE_TIME:
                self.services = self._discover()
                self.services_time = time.monotonic()

            return self.services

    def _is_present(self, name):
        return name in self._get_services()

    def enumerate(self, vid, pid):
        return [
            Network.Device(
                host, port, service_vid, service_pid, functools.partial(self._is_present, name)
            )
            for name, (host, port, service_vid, service_pid) in self._get_services().items()
            if (vid is None or vid == service_vid) and (pid is None or pid == service_pid)
        ]
