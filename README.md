# NetCDF Best Practices

This tutorial is a description of the best practices for using the NetCDF data format to store and retrieve multidimensional, spatio-temporal data. Examples of data that might lend themselves to such a format include weather model output, climate model output, data from remote sensing over time, etc.

The tutorial consists of the following modules:

* We begin by explaining how NetCDF's store their data by building a general puprose array accessor.
* We follow by showing how the NetCDF C library (and Python bindings) can be used to simplify file access code (and gain some speed up as well).
* We demonstrate iteration techniques for when a single NetCDF file is too large to store in RAM.
* We explain the trade-offs associated with using NetCDF4 chunking
* We demonstrate the performance penalties associated with using NetCDF4 compression

The tutorial is written in Python, using the IPython notebook, however most of the concepts will apply to other languages, since almost all languages use the NetCDF library's C bindings.
