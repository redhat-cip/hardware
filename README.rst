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

Networking
==========
* ethtool
* lldp from http://open-lldp.org/
* ibstat if you have infiniband devices from https://www.openfabrics.org/

System
======
* ipmitool from https://sourceforge.net/projects/ipmitool/
* pciutils
* lshw from http://www.ezix.org/project/wiki/HardwareLiSter

Raid controllers
================
* for HP controllers: hpacucli from http://h20564.www2.hpe.com/hpsc/swd/public/detail?swItemId=MTX_d6ebba0f5cd642edace4648b9a
* for Dell controllers: megacli from http://www.avagotech.com/docs-and-downloads/raid-controllers/raid-controllers-common-files/8-07-14_MegaCLI.zip
