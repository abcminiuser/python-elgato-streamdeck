-----------------------------
Default LibUSB HIDAPI Backend
-----------------------------

This is the default and recommended backend - a cross platform library for
communicating with HID devices. Most systems will have this as a system package
available for easy installation.


^^^^^^^
Windows
^^^^^^^

Windows systems requires additional manual installation of a DLL in order to
function. The latest source for the ``hidapi.dll`` DLL is the `releases page of
the libUSB GitHub project <https://github.com/libusb/hidapi/releases>`_.

Place the DLL into a folder that has been added to your system ``%PATH%``
directory list (typically this includes the ``C:\Windows\System32`` folder but
adding a new path would be recommended instead of modiying your Windows
directory).

Ensure you use the correct DLL version for your installed Python version; i.e.
if you are using 32-bit Python, install the 32-bit ``hidapi.dll``.

^^^^^^^^^^^^^^
MacOS (Darwin)
^^^^^^^^^^^^^^

On MacOS systems, you can choose to either compile the `HIDAPI project
<https://github.com/libusb/hidapi/>`_ yourself, or install it via one of the
multiple third party package managers (e.g. ``brew install hidapi``, when using
Homebrew).


^^^^^^^^^^^^^^^^^^^^^
Linux (Ubuntu/Debian)
^^^^^^^^^^^^^^^^^^^^^

On Linux, the ``libhidapi-libusb0`` package is required can can be installed via
the system's package manager.

The following script has been verified working on a Raspberry Pi (Models 2B and
4B) running a stock Debian Buster image, to install all the required
dependencies needed by this project on a fresh system::

    # Ensure system is up to date, upgrade all out of date packages
    sudo apt update && sudo apt dist-upgrade -y

    # Install the pip Python package manager
    sudo apt install -y python3-pip python3-setuptools

    # Install system packages needed for the default LibUSB HIDAPI backend
    sudo apt install -y libudev-dev libusb-1.0-0-dev libhidapi-libusb0

    # Install system packages needed for the Python Pillow package installation
    sudo apt install -y libjpeg-dev zlib1g-dev libopenjp2-7 libtiff5

    # Install python library dependencies
    pip3 install wheel
    pip3 install pillow

    # Add udev rule to allow all users non-root access to Elgato StreamDeck devices:
    sudo tee /etc/udev/rules.d/10-streamdeck.rules << EOF
    	SUBSYSTEMS=="usb", ATTRS{idVendor}=="0fd9", GROUP="users", TAG+="uaccess"
    	EOF

    # Reload udev rules to ensure the new permissions take effect
	sudo udevadm control --reload-rules

    # Install the latest version of the StreamDeck library via pip
    pip3 install streamdeck

Note that after adding the ``udev`` rules, you will need to remove and
re-attach any existing StreamDeck devices to ensure they adopt the new
permissions. This should allow you to access StreamDeck devices *without*
needing root permissions.
