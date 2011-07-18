import os, sys

sys.path.append(
    os.path.dirname(os.path.abspath(os.path.join(__file__, os.path.pardir))))

import unittest
import common.filepack as filepack
import common.instrument as instrument
import common.blockutils as bl
import common.wave as wave
import common.project as project

class FilePackTest(unittest.TestCase):
    def test_basic_compress_decompress(self):
        data = [i % 10 for i in xrange(5000)]

        compressed = filepack.compress(data)

        decompressed = filepack.decompress(compressed)

        self.assertEqual(data, decompressed)

    def test_rle_compress(self):
        data = [0xde for i in xrange(150)]
        data.extend([0xfe for i in xrange(220)])
        data.append(42)
        data.append(17)

        compressed = filepack.compress(data)

        reference = [filepack.RLE_BYTE, 0xde, 150,
                     filepack.RLE_BYTE, 0xfe, 220,
                     42, 17]

        self.assertEqual(compressed, reference)

        decompressed = filepack.decompress(compressed)

        self.assertEqual(decompressed, data)

    def test_short_rle_compress(self):
        data = [0xde, 0xde, 42, 17, 12]

        compressed = filepack.compress(data)

        self.assertEqual(compressed, data)


    def test_rle_special_byte(self):
        data = [filepack.RLE_BYTE, filepack.RLE_BYTE,
                filepack.SPECIAL_BYTE, filepack.SPECIAL_BYTE,
                filepack.RLE_BYTE, filepack.SPECIAL_BYTE]

        reference = [filepack.RLE_BYTE, filepack.RLE_BYTE, filepack.RLE_BYTE,
                     filepack.RLE_BYTE, filepack.RLE_BYTE,
                     filepack.SPECIAL_BYTE, 2, filepack.RLE_BYTE,
                     filepack.RLE_BYTE, filepack.SPECIAL_BYTE,
                     filepack.SPECIAL_BYTE]

        compressed = filepack.compress(data)

        self.assertEqual(compressed, reference)

        decompressed = filepack.decompress(compressed)

        self.assertEqual(decompressed, data)

    def test_default_instr_compress(self):
        data = []

        data.extend([0] * project.INSTR_PARAMS[0])

        for i in xrange(42):
            data.extend(instrument.DEFAULT)

        compressed = filepack.compress(data)

        reference = []

        self.extend_compressed_zeroes(reference, project.INSTR_PARAMS[0])

        reference.extend([filepack.SPECIAL_BYTE,
                          filepack.DEFAULT_INSTR_BYTE, 42])

        self.assertEqual(compressed, reference)

        decompressed = filepack.decompress(compressed)

        self.assertEqual(data, decompressed)

    def test_compress_default_region(self):
        data = []
        data.extend([0] * (instrument.NUM_PARAMS * 2))

        for i in xrange(4):
            data.extend(instrument.DEFAULT)

        data.extend([0] * (instrument.NUM_PARAMS * 3))

        data.extend(instrument.DEFAULT)

        compressed = []

        filepack._compress_default_region(
            data, len(data), compressed, 0, 0, len(data),
            instrument.DEFAULT, instrument.NUM_PARAMS,
            filepack.DEFAULT_INSTR_BYTE)

        reference = [filepack.RLE_BYTE, 0, instrument.NUM_PARAMS * 2,
                     filepack.SPECIAL_BYTE, filepack.DEFAULT_INSTR_BYTE, 4,
                     filepack.RLE_BYTE, 0, instrument.NUM_PARAMS * 3,
                     filepack.SPECIAL_BYTE, filepack.DEFAULT_INSTR_BYTE, 1]

        self.assertEqual(compressed, reference)

    def test_default_wave_compress(self):
        data = []

        data.extend([0] * project.WAVE_FRAMES[0])

        for i in xrange(33):
            data.extend(wave.DEFAULT)

        compressed = filepack.compress(data)

        reference = []

        self.extend_compressed_zeroes(reference, project.WAVE_FRAMES[0])

        reference.extend([filepack.SPECIAL_BYTE,
                          filepack.DEFAULT_WAVE_BYTE, 33])

        print
        print compressed[138:154]
        print reference[138:154]
        for i in xrange(len(compressed)):
            if compressed[i] != reference[i]:
                print i
                assert False
        self.assertEqual(compressed, reference)

        decompressed = filepack.decompress(compressed)

        self.assertEqual(data, decompressed)

    def extend_compressed_zeroes(self, data, num_zeroes):
        for i in xrange(num_zeroes / 255):
            data.extend([filepack.RLE_BYTE, 0, 255])

        data.extend([filepack.RLE_BYTE, 0, num_zeroes % 255])

    # def test_large_rle_compress(self):
    #     data = []

    #     for i in xrange(275):
    #         data.append(42)

    #     compressed = filepack.compress(data)

    #     reference = [filepack.RLE_BYTE, 42, 255, filepack.RLE_BYTE, 42, 20]

    #     self.assertEqual(compressed, reference)

    #     decompressed = filepack.decompress(compressed)

    #     self.assertEqual(data, decompressed)

    # def test_bad_rle_split(self):
    #     data = [filepack.RLE_BYTE]

    #     factory = bl.BlockFactory()

    #     self.assertRaises(AssertionError, filepack.split, data, bl.BLOCK_SIZE,
    #                       factory)

    # def test_bad_special_byte_split(self):
    #     data = [filepack.SPECIAL_BYTE]

    #     factory = bl.BlockFactory()

    #     self.assertRaises(AssertionError, filepack.split, data, bl.BLOCK_SIZE,
    #                       factory)

    # def test_block_jump_during_split_asserts(self):
    #     data = [filepack.SPECIAL_BYTE, 47]

    #     factory = bl.BlockFactory()

    #     self.assertRaises(AssertionError, filepack.split, data, bl.BLOCK_SIZE,
    #                       factory)

    # def test_special_byte_on_block_boundary(self):
    #     data = [42, 17, filepack.SPECIAL_BYTE, filepack.SPECIAL_BYTE,
    #             100, 36]

    #     factory = bl.BlockFactory()

    #     filepack.split(data, 5, factory)

    #     self.assertEqual(len(factory.blocks), 3)
    #     self.assertEqual(factory.blocks[0].data,
    #                      [42, 17, filepack.SPECIAL_BYTE, 1, 0])
    #     self.assertEqual(factory.blocks[1].data,
    #                      [filepack.SPECIAL_BYTE, filepack.SPECIAL_BYTE, 100,
    #                       filepack.SPECIAL_BYTE, 2])
    #     self.assertEqual(factory.blocks[2].data,
    #                      [36, filepack.SPECIAL_BYTE, filepack.EOF_BYTE, 0, 0])

    # def test_rle_byte_on_block_boundary(self):
    #     data = [42, 17, filepack.RLE_BYTE, filepack.RLE_BYTE,
    #             100, 36]

    #     factory = bl.BlockFactory()

    #     filepack.split(data, 5, factory)

    #     self.assertEqual(len(factory.blocks), 3)
    #     self.assertEqual(factory.blocks[0].data,
    #                      [42, 17, filepack.SPECIAL_BYTE, 1, 0])
    #     self.assertEqual(factory.blocks[1].data,
    #                      [filepack.RLE_BYTE, filepack.RLE_BYTE, 100,
    #                       filepack.SPECIAL_BYTE, 2])
    #     self.assertEqual(factory.blocks[2].data,
    #                      [36, filepack.SPECIAL_BYTE, filepack.EOF_BYTE, 0, 0])

    # def test_full_rle_on_block_boundary(self):
    #     data = [42, filepack.RLE_BYTE, 55, 4, 22, 3]

    #     factory = bl.BlockFactory()

    #     filepack.split(data, 5, factory)

    #     self.assertEqual(len(factory.blocks), 3)
    #     self.assertEqual(factory.blocks[0].data,
    #                      [42, filepack.SPECIAL_BYTE, 1, 0, 0])
    #     self.assertEqual(factory.blocks[1].data,
    #                      [filepack.RLE_BYTE, 55, 4, filepack.SPECIAL_BYTE, 2])
    #     self.assertEqual(factory.blocks[2].data,
    #                      [22, 3, filepack.SPECIAL_BYTE, filepack.EOF_BYTE, 0])

    # def test_default_on_block_boundary(self):
    #     data = [42, filepack.SPECIAL_BYTE, filepack.DEFAULT_INSTR_BYTE, 3, 2, 5]

    #     factory = bl.BlockFactory()

    #     filepack.split(data, 5, factory)

    #     self.assertEqual(len(factory.blocks), 3)
    #     self.assertEqual(factory.blocks[0].data,
    #                      [42, filepack.SPECIAL_BYTE, 1, 0, 0])
    #     self.assertEqual(factory.blocks[1].data,
    #                      [filepack.SPECIAL_BYTE, filepack.DEFAULT_INSTR_BYTE, 3,
    #                       filepack.SPECIAL_BYTE, 2])
    #     self.assertEqual(factory.blocks[2].data,
    #                      [2, 5, filepack.SPECIAL_BYTE, filepack.EOF_BYTE, 0])

    # def test_merge_with_rle_byte(self):
    #     factory = bl.BlockFactory()

    #     block1 = factory.new_block()
    #     block1.data = [filepack.RLE_BYTE, filepack.RLE_BYTE, 2, 1, 3,
    #                    filepack.SPECIAL_BYTE, 1, 0, 0]
    #     block2 = factory.new_block()
    #     block2.data = [4, 3, 6, filepack.SPECIAL_BYTE, filepack.EOF_BYTE]

    #     data = filepack.merge(factory.blocks)

    #     self.assertEqual(data, [filepack.RLE_BYTE, filepack.RLE_BYTE, 2, 1, 3,
    #                             4, 3, 6])

    # def test_merge_with_full_rle(self):
    #     factory = bl.BlockFactory()
    #     block1 = factory.new_block()
    #     block1.data = [filepack.RLE_BYTE, 42, 17, 1, 1, 4,
    #                    filepack.SPECIAL_BYTE, 1, 0, 0]
    #     block2 = factory.new_block()
    #     block2.data = [4, 4, 42, filepack.SPECIAL_BYTE, filepack.EOF_BYTE]

    #     data = filepack.merge(factory.blocks)

    #     self.assertEqual(data, [filepack.RLE_BYTE, 42, 17, 1, 1, 4, 4, 4, 42])

    # def test_merge_with_special_byte(self):
    #     factory = bl.BlockFactory()

    #     block1 = factory.new_block()
    #     block1.data = [filepack.SPECIAL_BYTE, filepack.SPECIAL_BYTE, 2, 1, 3,
    #                    filepack.SPECIAL_BYTE, 1, 0, 0]
    #     block2 = factory.new_block()
    #     block2.data = [4, 3, 6, filepack.SPECIAL_BYTE, filepack.EOF_BYTE]

    #     data = filepack.merge(factory.blocks)

    #     self.assertEqual(data, [filepack.SPECIAL_BYTE, filepack.SPECIAL_BYTE,
    #                             2, 1, 3, 4, 3, 6])


    # def test_merge_with_special_command(self):
    #     factory = bl.BlockFactory()

    #     block1 = factory.new_block()
    #     block1.data = [filepack.SPECIAL_BYTE, filepack.DEFAULT_INSTR_BYTE, 4, 6,
    #                    1, 93, filepack.SPECIAL_BYTE, 1, 0, 0]
    #     block2 = factory.new_block()
    #     block2.data = [3, 3, 33, filepack.SPECIAL_BYTE, filepack.EOF_BYTE]

    #     data = filepack.merge(factory.blocks)

    #     self.assertEquals(data, [filepack.SPECIAL_BYTE,
    #                              filepack.DEFAULT_INSTR_BYTE, 4, 6,
    #                              1, 93, 3, 3, 33])

    # def test_decompress_bogus_special_byte_asserts(self):
    #     data = [filepack.SPECIAL_BYTE, filepack.EOF_BYTE]

    #     self.assertRaises(AssertionError, filepack.decompress, data)

    # def test_weird_rle_compress(self):
    #     data = [0x1b, 0xc0, 0x00, 0x0f, 0x1d, 0xc0, 0x00, 0x0f, 0x1e, 0xc0,
    #             0x00, 0x0f, 0x20, 0xc0, 0x00, 0x1f, 0x22, 0x00, 0x00, 0x00,
    #             0x1e, 0x00, 0x1b, 0x00, 0x00, 0x00, 0x1e, 0x00, 0x00, 0x00,
    #             0x1d, 0x00, 0x00, 0x00, 0x19, 0x00, 0x00, 0x00, 0x20, 0x00,
    #             0x00, 0x00, 0x20, 0x00, 0x1e, 0x00, 0x1d, 0x00, 0x1b, 0x00,
    #             0x00, 0x00, 0x17, 0x00, 0x19, 0x00, 0x00, 0x00, 0x1b, 0x00,
    #             0x00, 0x00, 0x1e, 0x00, 0x1d, 0x00, 0x00, 0x00, 0x19, 0x00,
    #             0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x1d, 0x00, 0x00, 0x00,
    #             0x1e, 0x00, 0x00, 0x00, 0x1b, 0x00, 0x1e, 0x00, 0x00, 0x00,
    #             0x22, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x1d, 0x00,
    #             0x00, 0x00, 0x25, 0x00, 0x00, 0x00, 0x20, 0xc0, 0x00, 0x05,
    #             0x23, 0x00, 0x00, 0x00, 0x25, 0x00, 0x23, 0x00, 0x00, 0x00,
    #             0x1e, 0xc0, 0x00, 0x05, 0x20, 0x00, 0x00, 0x00, 0x1d, 0x00,
    #             0x19, 0x00, 0x00, 0x00, 0x1d, 0xc0, 0x00, 0x05, 0x20, 0x00,
    #             0x00, 0x00, 0x1d, 0x00, 0x19, 0x00, 0x00, 0x00, 0x1d, 0x00,
    #             0x00, 0x00, 0x1b, 0x00, 0x1b, 0x00, 0x00, 0x00, 0x16, 0x00,
    #             0x00, 0x00, 0x1b, 0x00, 0x00, 0x00, 0x1e, 0x00, 0x00, 0x00,
    #             0x1d, 0x00, 0x00, 0x00, 0x19, 0x00, 0x20, 0x00, 0x00, 0x00,
    #             0x1d, 0xc0, 0x00, 0x05, 0x1b, 0x00, 0x00, 0x00, 0x03, 0x00,
    #             0x03, 0x00, 0x00, 0x00, 0x03, 0x00, 0x03, 0x00, 0x1b, 0x19,
    #             0x03, 0xc0, 0x00, 0x0d, 0x03, 0x01, 0x0f, 0xc0, 0x00, 0x0f,
    #             0x19, 0xc0, 0x00, 0x1f, 0x1e, 0x00, 0x00, 0x00, 0x23, 0x00,
    #             0x1e, 0x00, 0x00, 0x00, 0x1b, 0xc0, 0x00, 0x05, 0x1d, 0x00,
    #             0x00, 0x00, 0x20, 0x00, 0x1d, 0x00, 0x00, 0x00, 0x19, 0xc0,
    #             0x00, 0x05, 0x1b, 0xc0, 0x00, 0x8f, 0x31, 0x00, 0x1b, 0x00,
    #             0x31, 0x00, 0x1b, 0x00, 0x31, 0x00, 0x1b, 0x00, 0x31, 0x00,
    #             0x1b, 0x00, 0x31, 0x00, 0x19, 0x00, 0x31, 0x00, 0x19, 0x00,
    #             0x31, 0x00, 0x19, 0x00, 0x31, 0x00, 0x19, 0x00, 0x31, 0x00,
    #             0x17, 0x00, 0x31, 0x00, 0x17, 0x00, 0x31, 0x00, 0x17, 0x00,
    #             0x31, 0x00, 0x17, 0x00, 0x31, 0xc0, 0x00, 0x09, 0x31, 0xc0,
    #             0x00, 0x05, 0x31, 0x00, 0x31, 0xc0, 0x00, 0x07, 0x31, 0xc0,
    #             0x00, 0x05, 0x31, 0x00, 0x0f, 0x00, 0x31, 0x00, 0x0f, 0x00,
    #             0x31, 0x00, 0x0f, 0x00, 0x31, 0x00, 0x0f, 0x00, 0x31, 0xc0,
    #             0x00, 0x9f, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
    #             0x01, 0x01, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00,
    #             0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x00,
    #             0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x00,
    #             0x01, 0x00, 0xc0, 0x01, 0x08, 0x00, 0x00, 0xc0, 0x01, 0x0e,
    #             0xc0, 0x00, 0x10, 0x01, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff,
    #             0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0,
    #             0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00,
    #             0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff,
    #             0xc0, 0x00, 0xab, 0xc0, 0xff, 0x40, 0xc0, 0x00, 0x60, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06,
    #             0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x06, 0x06, 0xc0, 0x00, 0x0e, 0x06, 0x06, 0xc0, 0x00,
    #             0x0e, 0x7f, 0x7f, 0x20, 0x31, 0x7f, 0x7f, 0x20, 0x30, 0x7f,
    #             0x7f, 0x20, 0x30, 0x7f, 0x7f, 0x20, 0x30, 0x7f, 0x10, 0x21,
    #             0x30, 0x7f, 0x10, 0x21, 0x30, 0x7f, 0x7f, 0x20, 0x30, 0x7f,
    #             0x7f, 0x20, 0x30, 0x7f, 0x10, 0x21, 0x30, 0x7f, 0x10, 0x21,
    #             0x30, 0x7f, 0x7f, 0x20, 0x30, 0x7f, 0x7f, 0x20, 0x30, 0x7f,
    #             0x11, 0x22, 0x31, 0x7f, 0x12, 0x22, 0x30, 0x7f, 0x13, 0x22,
    #             0x30, 0x7f, 0x12, 0x22, 0x30, 0x7f, 0x7f, 0x20, 0x30, 0x7f,
    #             0x7f, 0x20, 0x30, 0x7f, 0x7f, 0x20, 0x30, 0x7f, 0x7f, 0x20,
    #             0x30, 0x7e, 0x7e, 0x23, 0x32, 0xc0, 0xff, 0xff, 0xc0, 0xff,
    #             0xff, 0xc0, 0xff, 0xff, 0xc0, 0xff, 0xaf, 0xc0, 0x00, 0xff,
    #             0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0,
    #             0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00,
    #             0x47, 0x43, 0x20, 0x33, 0x20, 0x43, 0x23, 0x33, 0x20, 0x44,
    #             0x20, 0x33, 0x20, 0x44, 0x23, 0x33, 0x20, 0x45, 0x20, 0x33,
    #             0x20, 0x46, 0x20, 0x33, 0x20, 0x46, 0x23, 0x33, 0x20, 0x47,
    #             0x20, 0x33, 0x20, 0x47, 0x23, 0x33, 0x20, 0x41, 0x20, 0x33,
    #             0x20, 0x41, 0x23, 0x33, 0x20, 0x42, 0x20, 0x33, 0x20, 0x43,
    #             0x20, 0x34, 0x20, 0x43, 0x23, 0x34, 0x20, 0x44, 0x20, 0x34,
    #             0x20, 0x44, 0x23, 0x34, 0x20, 0x45, 0x20, 0x34, 0x20, 0x46,
    #             0x20, 0x34, 0x20, 0x46, 0x23, 0x34, 0x20, 0x47, 0x20, 0x34,
    #             0x20, 0x47, 0x23, 0x34, 0x20, 0x41, 0x20, 0x34, 0x20, 0x41,
    #             0x23, 0x34, 0x20, 0x42, 0x20, 0x34, 0x20, 0x43, 0x20, 0x35,
    #             0x20, 0x43, 0x23, 0x35, 0x20, 0x44, 0x20, 0x35, 0x20, 0x44,
    #             0x23, 0x35, 0x20, 0x45, 0x20, 0x35, 0x20, 0x46, 0x20, 0x35,
    #             0x20, 0x46, 0x23, 0x35, 0x20, 0x47, 0x20, 0x35, 0x20, 0x47,
    #             0x23, 0x35, 0x20, 0x41, 0x20, 0x35, 0x20, 0x41, 0x23, 0x35,
    #             0x20, 0x42, 0x20, 0x35, 0x20, 0x43, 0x20, 0x36, 0x20, 0x43,
    #             0x23, 0x36, 0x20, 0x44, 0x20, 0x36, 0x20, 0x44, 0x23, 0x36,
    #             0x20, 0x45, 0x20, 0x36, 0x20, 0x46, 0x20, 0x36, 0x20, 0x72,
    #             0x62, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xa7, 0xc0, 0x01, 0x09,
    #             0xc0, 0x00, 0x17, 0x01, 0x01, 0x01, 0xc0, 0x00, 0x0d, 0x01,
    #             0x01, 0x01, 0xc0, 0x00, 0x0d, 0x01, 0x01, 0xc0, 0x00, 0x0e,
    #             0xc0, 0x01, 0x05, 0xc0, 0x00, 0x0c, 0x01, 0x02, 0x02, 0xc0,
    #             0xff, 0x0c, 0x05, 0x06, 0x07, 0x08, 0xc0, 0xff, 0x0c, 0x09,
    #             0x0a, 0x0b, 0x0c, 0xc0, 0xff, 0x0c, 0x02, 0x03, 0x00, 0x00,
    #             0xc0, 0xff, 0x0c, 0x09, 0x0a, 0x0b, 0x0d, 0xc0, 0xff, 0x0c,
    #             0x0e, 0x0f, 0x15, 0x16, 0xc0, 0xff, 0x0c, 0x17, 0xc0, 0xfe,
    #             0x0f, 0xc0, 0xff, 0x90, 0xc0, 0x11, 0x04, 0xc0, 0xff, 0x0c,
    #             0x12, 0x12, 0x13, 0x13, 0xc0, 0xff, 0x0c, 0xc0, 0x13, 0x04,
    #             0xc0, 0xff, 0x0c, 0x12, 0x12, 0x13, 0x13, 0xc0, 0xff, 0xcc,
    #             0x20, 0x21, 0x22, 0x21, 0xc0, 0xff, 0x0c, 0x23, 0x24, 0x23,
    #             0x24, 0xc0, 0xff, 0x0c, 0xc0, 0x25, 0x04, 0xc0, 0xff, 0x0c,
    #             0x26, 0xc0, 0xfe, 0x0f, 0xc0, 0xff, 0xc0, 0x30, 0x31, 0x31,
    #             0x32, 0x00, 0xc0, 0xff, 0x0c, 0xfe, 0xfe, 0xfe,
    #             0x33, 0xc0, 0xff, 0x0c, 0x35, 0xc0, 0xfe, 0x0f, 0xc0, 0xff,
    #             0xff, 0xc0, 0xff, 0xff, 0xc0, 0xff, 0xff, 0xc0, 0xff, 0xff,
    #             0xc0, 0xff, 0xb4, 0xc0, 0xfe, 0x0b, 0xee, 0xee, 0xc0, 0xfe,
    #             0x07, 0xc0, 0xff, 0x0c, 0x00, 0x00, 0x00, 0x02, 0xc0, 0x00,
    #             0x2c, 0x04, 0x00, 0x08, 0x0a, 0xc0, 0x00, 0xec, 0xfe, 0xfe,
    #             0xc0, 0x00, 0x0e, 0x0c, 0x0c, 0xc0, 0x00, 0xff, 0xc0, 0x00,
    #             0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff, 0xc0, 0x00, 0xff,
    #             0xc0, 0x00, 0xff, 0xc0, 0x00, 0xd5, 0x88, 0x00, 0x3f, 0xff,
    #             0x00, 0x22, 0x83, 0x00, 0x00, 0xd0, 0x00, 0x00, 0x00, 0xf3]

    #     decompressed = filepack.decompress(data)

    #     recompressed = filepack.compress(decompressed)
    #     print
    #     print ["%x" % x for x in data[0x440:0x44f]]
    #     print ["%x" % x for x in recompressed[0x440:0x44f]]

    #     for i in xrange(max(len(data), len(recompressed))):
    #         self.assertEqual(data[i], recompressed[i])


if __name__ == "__main__":
    unittest.main()
