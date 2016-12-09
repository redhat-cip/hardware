===============================
hardware
===============================

.. image:: https://img.shields.io/pypi/v/hardware.svg
   :alt: Latest hardware release on the Python Cheeseshop (PyPI)
   :target: https://pypi.python.org/pypi/hardware

.. image:: https://travis-ci.org/redhat-cip/hardware.svg?branch=master
   :alt: Build status of hardware on Travis CI
   :target: https://travis-ci.org/redhat-cip/hardware

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

Usage
-----

Run the hardware-detect program::

    hardware-detect --human
