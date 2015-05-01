import os
import math
from time import time
import resource
from collections import namedtuple
from contextlib import contextmanager, ContextDecorator
from tempfile import NamedTemporaryFile

import netCDF4
import numpy as np

def make_netcdf3_file(shape, variable_name='some_variable', dir_=os.getcwd()):

    with NamedTemporaryFile(suffix='.nc', dir=dir_, delete=False) as f:

        nc = netCDF4.Dataset(f.name, 'w', format='NETCDF3_CLASSIC')
        nc.createDimension('x', shape[2])
        nc.createDimension('y', shape[1])
        nc.createDimension('z', shape[0])
        some_var = nc.createVariable('some_variable','f4',('z', 'y', 'x'))

    def trip(x, y, z):
        d = math.sqrt((x - 256) ** 2 + (y - 256) ** 2)
        return math.sin(d / 64) + math.sin(z)
    trip_v = np.vectorize(trip)

    x, y = np.meshgrid(range(shape[2]), range(shape[1]))
    basegrid = trip_v(x, y, 0).astype('float32')

    for z in range(shape[0]):
        a = basegrid + math.sin(z / 32)
        some_var[z,:,:] = a

    nc.close()

    return f.name

MemUsage = namedtuple('MemUsage', 'size resident share text lib data dt')

def get_mem_usage():
    pid = os.getpid()
    with open('/proc/{}/statm'.format(pid)) as f:
        string = f.read()
    return MemUsage._make([int(x) for x in string.split()])    
    
@contextmanager
def mem_limiter(bytes_):
    if get_mem_usage().data > bytes_:
        raise MemoryError("You're already using {} bytes which is over the limit of {} bytes".format(get_mem_usage().data, bytes_))
    yield
    if get_mem_usage().data > bytes_:
        raise MemoryError("FAIL! You're using {} bytes which is over the limit of {} bytes".format(get_mem_usage().data, bytes_))

class ThroughputMeter(ContextDecorator):
    def __enter__(self):
        self.t0 = time()
        return self
    def __exit__(self, *exc):
        self.tn = time()

    def megabytes_per_second(self, array):
        seconds = self.tn - self.t0
        MB = np.prod(array.shape) / 1024 ** 2 * array.dtype.itemsize
        MBps = MB / seconds
        print("{:03.3f} MB in {:03.3} seconds at {:03.3f} MB / sec".format(MB, seconds, MBps))
        return MBps
