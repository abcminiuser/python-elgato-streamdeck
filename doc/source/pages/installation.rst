********************
Library Installation
********************

To install this library via the `pip` package manager, simply run
``pip install streamdeck`` from a terminal.

The included examples require the PIL fork `pillow`, although it can be
swapped out if desired by the user application for any other image manipulation
library. This can also be installed with `pip` via ``pip install pillow``.

=================
HID Backend Setup
=================

The library core is structured so that it can use one of (potentially) several
alternative HID backend libraries for the actual low level device
communications. You will need to install the dependencies appropriate to your
chosen backend for the library to work correctly.

**Backends:**

.. toctree::
    :glob:
    :maxdepth: 1

    backend_libusb_hidapi.rst
