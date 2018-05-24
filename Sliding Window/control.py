import test as test
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('index', type=int, help='the index of the thread')
arg = (parser.parse_args()).index
print arg
numthreads = 2

test.control([arg, numthreads])
