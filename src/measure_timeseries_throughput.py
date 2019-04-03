import random
from math import ceil
from argparse import ArgumentParser

from netCDF4 import Dataset
from humanize import naturalsize

from utils import ThroughputMeter


def measure(filename):
    dst = Dataset(filename)
    assert 'lat' in dst.dimensions
    assert 'lon' in dst.dimensions

    x = ceil(dst.dimensions['lon'].size / 2) - 1
    y = ceil(dst.dimensions['lat'].size / 2) - 1
    choices = set(dst.variables.keys()).intersection({'pr', 'tasmin', 'tasmax'})
    var = random.choice(tuple(choices))

    with ThroughputMeter() as t:
        a = dst[var][:,y,x]
    
    dst.close()
    return t.megabytes_per_second(a) * 2**20


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('filenames', nargs='+',
                        help='files on which to measure throughput')
    args = parser.parse_args()

    for filename in args.filenames:
        throughput = measure(filename)
        throughput = naturalsize(throughput, binary=True, gnu=True)
        print('{}: {}'.format(filename, throughput))
