import bread_spec
import bread
import os
import sys
from struct import unpack
import utils
from StringIO import StringIO
from project import Project
import blockutils
from blockutils import BlockReader, BlockWriter, BlockFactory
import filepack
import collections
import bitstring

class SAVFile(object):
    # Start offset of SAV file contents
    START_OFFSET = 0x8000

    HEADER_EMPTY_SECTION_1 = (0x8120, 0x813d)

    # Offset of SRAM initialization check
    SRAM_INIT_CHECK_OFFSET = 0x813e
    SRAM_INIT_CHECK_LENGTH = 2

    # Offset where active file number appears
    ACTIVE_FILE_NUMBER_OFFSET = 0x8140

    # Start of block allocation table
    BAT_START_OFFSET = 0x8141

    # End of block allocation table
    BAT_END_OFFSET = 0x81ff

    # Start index for data blocks
    BLOCKS_START_OFFSET = 0x8000

    # The maximum number of files that the .sav can support
    NUM_FILES = 0x20

    # Max length in bytes of filename
    FILENAME_LENGTH = 8

    # Length in bytes of file version number
    FILE_VERSION_LENGTH = 1

    # Length in bytes of file number
    FILE_NUMBER_LENGTH = 1

    #Constants
    EMPTY_BLOCK = 0xff

    def __init__(self, filename):
        self.projects = []

        fp = open(filename, 'rb')

        self.preamble = fp.read(self.START_OFFSET)

        header_block_data = fp.read(blockutils.BLOCK_SIZE)

        self.header_block = bread.parse(
            header_block_data, bread_spec.compressed_sav_file)

        print self.header_block

        if self.header_block.sram_init_check != 'jk':
            assert False, "SRAM init check bits incorrect " \
                "(should be 'jk', was '%s')" % (
                    self.header_block.sram_init_check)

        self.active_project_number = self.header_block.active_file

        file_blocks = collections.defaultdict(list)

        for block_number, file_number in enumerate(
                self.header_block.block_alloc_table):
            if file_number == self.EMPTY_BLOCK:
                continue

            assert 0 <= file_number <= 0x1f, (
                "File number %x for block %x out of range" %
                (file_number, block_number))

            # The file's header is block 0, so blocks are indexed from 1
            file_blocks[file_number].append(block_number + 1)

        for file_number in file_blocks:
            block_numbers = file_blocks[file_number]
            block_map = {}

            for block_number in block_numbers:
                offset = self.BLOCKS_START_OFFSET + \
                    (block_number * blockutils.BLOCK_SIZE)

                fp.seek(offset, os.SEEK_SET)

                block_data = bytearray(fp.read(blockutils.BLOCK_SIZE))

                block_map[block_number] = blockutils.Block(block_number,
                                                           block_data)

            reader = BlockReader()
            compressed_data = reader.read(block_map)
            raw_data = filepack.decompress(compressed_data)

            project = Project(
                name = self.header_block.filenames[file_number],
                version = self.header_block.file_versions[file_number],
                data = raw_data)

            self.projects.append(project)

        fp.close()

    def __str__(self):

        str_stream = StringIO()

        for project in self.projects:
            print >>str_stream, str(project)

        print >>str_stream, "Active Project: %s" % \
            (self.projects[self.active_project_number])

        str_stream_stringval = str_stream.getvalue()
        str_stream.close()
        return str_stream_stringval

    def save(self, filename):
        print self.header_block

        fp = open(filename, 'wb')

        writer = BlockWriter()
        factory = BlockFactory()

        # Block allocation table doesn't include header block because it's
        # always in use, so have to add additional block to account for header
        num_blocks = self.BAT_END_OFFSET - self.BAT_START_OFFSET + 2

        header_block = factory.new_block()

        block_table = []

        for i in xrange(num_blocks):
            block_table.append(None)

        # First block is the header block, so we should ignore it when creating
        # the block allocation table
        block_table[0] = -1

        for (i, project) in enumerate(self.projects):
            raw_data = project.get_raw_data()
            compressed_data = filepack.compress(raw_data)

            project_block_ids = writer.write(compressed_data, factory)

            print project_block_ids

            for b in project_block_ids:
                block_table[b] = i

        # Bytes up to START_OFFSET will remain the same
        fp.write(self.preamble)

        # Set header block filenames
        for i, project in enumerate(self.projects):
            self.header_block.filenames[i] = project.name

        empty_project_name = '\0' * self.FILENAME_LENGTH

        for i in xrange(self.NUM_FILES - len(self.projects)):
            self.header_block.filenames[i] = empty_project_name

        # Set header block project versions
        for i, project in enumerate(self.projects):
            self.header_block.file_versions[i] = project.version

        for i in xrange(self.NUM_FILES - len(self.projects)):
            self.header_block.file_versions[i] = 0

        self.header_block.active_file = self.active_project_number



        # Ignore the header block when serializing the block allocation table
        for i, b in enumerate(block_table[1:]):
            if b == None:
                file_no = self.EMPTY_BLOCK
            else:
                file_no = b

            self.header_block.block_alloc_table[i] = file_no

        header_block.data = bread.write(
            self.header_block, bread_spec.compressed_sav_file)

        assert len(header_block.data) == blockutils.BLOCK_SIZE, \
            "Header block isn't the expected length; expected 0x%x, got 0x%x" \
            % (blockutils.BLOCK_SIZE, len(header_block.data))

        block_map = factory.blocks

        empty_block_data = []
        for i in xrange(blockutils.BLOCK_SIZE):
            empty_block_data.append(0)

        for i in xrange(num_blocks):
            if i in block_map:
                data_list = block_map[i].data
            else:
                data_list = empty_block_data

            fp.write(data_list)

        fp.close()

if __name__ == "__main__":
    sav = SAVFile(sys.argv[1])
    sav.save(sys.argv[2])
