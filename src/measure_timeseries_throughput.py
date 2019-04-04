import os
from time import time
import random
from math import ceil
from argparse import ArgumentParser

import numpy as np
import netCDF4
import h5py
from humanize import naturalsize
from contextdecorator import ContextDecorator


class ThroughputMeter(ContextDecorator):
    def __enter__(self):
        self.t0 = time()
        return self

    def __exit__(self, *exc):
        self.tn = time()

    def bytes_per_second(self, array):
        seconds = self.tn - self.t0
        bytes_ = np.prod(array.shape) * array.dtype.itemsize
        Bps = bytes_ / seconds
        return Bps


class GriddedFile(object):
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        raise NotImplementedError()

    def close(self):
        self.dst.close()

    @property
    def variables(self):
        raise NotImplementedError()

    @property
    def dimensions(self):
        raise NotImplementedError()

    @property
    def xlen(self):
        raise NotImplementedError()

    @property
    def ylen(self):
        raise NotImplementedError()

    def measure(self, method='direct'):
        self.open()
        assert 'lat' in self.dimensions
        assert 'lon' in self.dimensions

        x = ceil(self.xlen / 2) - 1
        y = ceil(self.ylen / 2) - 1
        choices = set(self.variables).intersection({'pr', 'tasmin', 'tasmax'})
        var = random.choice(tuple(choices))

        with ThroughputMeter() as t:
            if method == 'direct':
                a = extract_direct(self.dst, var, x, y)
            elif method == 'iterative':
                a = extract_iterative(self.dst, var, x, y, self.zlen)

        self.close()
        return t.bytes_per_second(a)


class H5Gridded(GriddedFile):
    def open(self):
        self.dst = h5py.File(self.filename, 'r')

    @property
    def xlen(self):
        return self.dst['lon'].size

    @property
    def ylen(self):
        return self.dst['lat'].size

    @property
    def zlen(self):
        return self.dst['time'].size

    @property
    def variables(self):
        return list(self.dst.keys())

    @property
    def dimensions(self):
        return list(set(self.dst.keys()).intersection({'lat', 'lon', 'time'}))


class NCGridded(GriddedFile):
    def open(self):
        self.dst = netCDF4.Dataset(self.filename)

    @property
    def xlen(self):
        return self.dst.dimensions['lon'].size

    @property
    def ylen(self):
        return self.dst.dimensions['lat'].size

    @property
    def zlen(self):
        return self.dst.dimensions['time'].size

    @property
    def variables(self):
        return self.dst.variables.keys()

    @property
    def dimensions(self):
        return list(self.dst.dimensions.keys())


def extract_iterative(dst, var, x, y, zlen):
    a = np.empty(shape=(zlen))
    for i in range(zlen):
        a[i] = dst[var][i, y, x]
    return a


def extract_direct(dst, var, x, y):
    return dst[var][:, y, x]


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('filenames', nargs='*', default=[],
                        help='files on which to measure throughput')
    parser.add_argument('-d', '--directory', metavar='DIR',
                        help='directory from which to choose several files')
    parser.add_argument('-n', '--num_files', metavar='NUM_FILES', default=5)
    parser.add_argument('-i', '--interface', choices=['netcdf4', 'hdf5'],
                        default='netcdf4',
                        help='Which library to use tointerface with the grid')
    parser.add_argument('-m', '--method', choices=['direct', 'iterative'],
                        default='direct',
                        help="Whether to make a single getitem call to the "
                             "grid library or to go step-by-step.")

    args = parser.parse_args()

    if args.directory:
        filenames = []
        choices = os.listdir(args.directory)
        for _ in range(args.num_files):
            f = random.choice(choices)
            filenames.append(os.path.join(args.directory, f))
            choices.remove(f)
    else:
        filenames = args.filenames

    moving_avg = 0.0

    IfaceClass = {'netcdf4': NCGridded, 'hdf5': H5Gridded}[args.interface]

    for i, filename in enumerate(filenames):
        g = IfaceClass(filename)
        throughput = g.measure(method=args.method)
        throughput_str = naturalsize(throughput, binary=True, gnu=True)
        print('{}: {}'.format(filename, throughput_str))

        if moving_avg:
            moving_avg = moving_avg * i / (i+1) + throughput / (i+1)
        else:
            moving_avg = throughput

    print('Average: {}'.format(naturalsize(moving_avg, binary=True, gnu=True)))
