===============================
hardware
===============================

.. image:: https://img.shields.io/pypi/v/hardware.svg
   :alt: Latest hardware release on the Python Cheeseshop (PyPI)
   :target: https://pypi.python.org/pypi/hardware

Hardware detection and classification utilities

Homepage: https://github.com/redhat-cip/hardware

Features
--------

* detect hardware features of a Linux systems:

  * RAID
  * hard drives
  * IPMI
  * network cards
  * DMI infos
  * memory settings
  * processor features

* filter hardware according to hardware profiles

Install
-------

Installing from pypi::

    pip install -U hardware

Usage
-----

Run the hardware-detect program::

    hardware-detect --human


Runtime dependencies
--------------------
The hardware detection is divided in modules that detects a specific hardware type. Each module have its own dependencies.

Therefore, we cannot enforce installing all the dependencies as some are not relevant regarding a particular hardware type.
To avoid a situation where we cannot use/install hardware because of one of those deps, we do prefer let users installing the one they need.

The hardware detection code will ignore all the missing deps and continue, so not installing a deps is not fatal.

Please find bellow the list of dependencies per module:

Areca
=====
* cli64 from http://www.areca.com.tw/support/s_linux/linux.htm

Logical disks
=============
* hdparm
* smartmontools

Benchmarks
==========
* sysbench 1.0 or newer for CPU and memory benchmarks
* fio for disk benchmarks

Networking
==========
* ethtool
* lldp from http://open-lldp.org/
* ibstat if you have infiniband devices from https://www.openfabrics.org/

System
======
* ipmitool from https://codeberg.org/IPMITool/ipmitool
* pciutils
* lshw from http://www.ezix.org/project/wiki/HardwareLiSter

Raid controllers
================
* for HPE Smart Array controllers: ``ssacli`` from the `HPE SSA CLI <https://support.hpe.com/connect/s/softwaredetails?softwareId=MTX_521fc533ba8f468f9ad9db20e4>`_ (``hpssacli`` and ``hpacucli`` are also detected for older installations)
* for Dell PERC controllers: PERCCLI (``perccli`` or ``perccli64``)
* for other LSI/Broadcom MegaRAID controllers: StorCLI (``storcli`` or ``storcli64``)

The detector searches ``PATH`` and the standard vendor installation directories
``/opt/MegaRAID/perccli`` and ``/opt/MegaRAID/storcli``. MegaCLI is deprecated
upstream but remains supported as a fallback for older installations.
