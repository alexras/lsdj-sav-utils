#!/usr/bin/env python

from itertools import izip
import os, sys
from optparse import OptionParser

def binary_diff(file1, file2, start_offset = 0):
    fp1 = open(file1, 'rb')
    fp2 = open(file2, 'rb')

    file1_size = os.path.getsize(file1)
    file2_size = os.path.getsize(file2)

    if file1_size != file2_size:
        print "File sizes differ"
        return

    bytes_read = start_offset

    fp1.seek(start_offset)
    fp2.seek(start_offset)

    while bytes_read < file1_size:
        byte1 = fp1.read(1)
        byte2 = fp2.read(1)

        if byte1 != byte2:
            print "First difference at offset 0x%x" % (bytes_read)
            print ""
            print "Area of first difference:"
            fp1.seek(-8, os.SEEK_CUR)
            fp2.seek(-8, os.SEEK_CUR)

            region1 = fp1.read(16)
            region2 = fp2.read(16)

            print [x for x in region1]
            print [x for x in region2]
            break
        else:
            bytes_read += 1


def main():
    optionParser = OptionParser(usage="usage: %prog [options] <file1> <file2>")
    optionParser.add_option("--start_offset", "-s", default=0, type=int,
                            help="offset at which to start comparing the files")

    (options, args) = optionParser.parse_args()

    if len(args) != 2:
        optionParser.error("Incorrect argument count")

    for filename in args:
        if not os.path.exists(filename):
            sys.exit("Can't find file '%s'" % (filename))

    binary_diff(*args,start_offset = options.start_offset)

if __name__ == "__main__":
    main()
