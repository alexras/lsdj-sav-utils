import instrument
import wave
import project

# Byte used to denote run-length encoding
RLE_BYTE = 0xc0

# Byte used to denote special action
SPECIAL_BYTE = 0xe0

# Byte used to denote end of file (appears after special byte)
EOF_BYTE = 0xff

# Byte used to denote default instrument
DEFAULT_INSTR_BYTE = 0xf1

# Byte used to denote default wave
DEFAULT_WAVE_BYTE = 0xf0


RESERVED_BYTES = [SPECIAL_BYTE, RLE_BYTE]

STATE_BYTES = 0
STATE_RLE_BYTE = 1
STATE_RLE_COUNT = 2
STATE_SPECIAL_BYTE = 3
STATE_DEFAULT_INSTR = 4
STATE_DEFAULT_WAVE = 5
STATE_DONE = 6

def split(compressed_data, segment_size, block_factory):
    # Split compressed data into blocks
    segments = []

    current_segment_start = 0
    index = 0
    data_size = len(compressed_data)

    while index < data_size:
        current_byte = compressed_data[index]

        if index < data_size - 1:
            next_byte = compressed_data[index + 1]
        else:
            next_byte = None

        jump_size = 1

        if current_byte == RLE_BYTE:
            assert next_byte is not None, "Expected a command to follow " \
                "RLE byte"
            if next_byte == RLE_BYTE:
                jump_size = 2
            else:
                jump_size = 3

        elif current_byte == SPECIAL_BYTE:
            assert next_byte is not None, "Expected a command to follow " \
                "special byte"

            if next_byte == SPECIAL_BYTE:
                jump_size = 2
            elif next_byte == DEFAULT_INSTR_BYTE or \
                    next_byte == DEFAULT_WAVE_BYTE:
                jump_size = 3
            else:
                assert False, "Encountered unexpected EOF or block " \
                    "switch while segmenting"

        # Need two bytes for the jump or EOF
        if index - current_segment_start + jump_size > segment_size - 2:
            segments.append(compressed_data[
                    current_segment_start:index])

            current_segment_start = index
        else:
            index += jump_size

    # Append the last segment, if any
    if current_segment_start != index:
        segments.append(compressed_data[
                current_segment_start:current_segment_start + index])


    # Make sure that no data was lost while segmenting
    total_segment_length = sum(map(len, segments))
    assert total_segment_length == len(compressed_data), "Lost %d bytes of " \
        "data while segmenting" % (len(compressed_data) - total_segment_length)

    block_ids = []

    for segment in segments:
        block = block_factory.new_block()
        block_ids.append(block.id)

    for (i, segment) in enumerate(segments):
        block = block_factory.blocks[block_ids[i]]

        assert len(block.data) == 0, "Encountered a block with "
        "pre-existing data while writing"

        if i == len(segments) - 1:
            # Write EOF to the end of the segment
            add_eof(segment)
        else:
            # Write a pointer to the next segment
            add_block_switch(segment, block_ids[i + 1])

        # Pad segment with zeroes until it's large enough
        pad(segment, segment_size)

        block.data = segment

    return block_ids

def merge(blocks):
    current_block = blocks[sorted(blocks.keys())[0]]

    compressed_data = []
    eof = False

    ignored_special_commands = [DEFAULT_INSTR_BYTE,
                                DEFAULT_WAVE_BYTE]

    while not eof:
        data_size_to_append = None
        next_block = None

        i = 0
        while i < len(current_block.data) - 1:
            current_byte = current_block.data[i]
            next_byte = current_block.data[i + 1]

            if current_byte == RLE_BYTE:
                if next_byte == RLE_BYTE:
                    i += 2
                else:
                    i += 3
            elif current_byte == SPECIAL_BYTE:
                if next_byte in ignored_special_commands:
                    i += 3
                elif next_byte == SPECIAL_BYTE:
                    i += 2
                else:
                    data_size_to_append = i

                    # hit end of file
                    if next_byte == EOF_BYTE:
                        eof = True
                    else:
                        next_block = blocks[next_byte]

                    break
            else:
                i += 1

        assert data_size_to_append is not None, "Ran off the end of a "\
            "block without encountering a block switch or EOF"

        compressed_data.extend(current_block.data[0:data_size_to_append])

        if not eof:
            assert next_block is not None, "Switched blocks, but did " \
                "not provide the next block to switch to"

            current_block = next_block

    return compressed_data

def add_eof(segment):
    segment.extend([SPECIAL_BYTE, EOF_BYTE])

def add_block_switch(segment, block_id):
    segment.extend([SPECIAL_BYTE, block_id])

def pad(segment, size):
    for i in xrange(size - len(segment)):
        segment.append(0)

    assert len(segment) == size

def decompress(compressed_data):
    raw_data = []

    state = STATE_BYTES

    rle_byte_value = None

    data_size = len(compressed_data)

    for index in xrange(len(compressed_data)):
        data_byte = compressed_data[index]

        if state == STATE_BYTES:
            if data_byte == RLE_BYTE:
                state = STATE_RLE_BYTE
            elif data_byte == SPECIAL_BYTE:
                state = STATE_SPECIAL_BYTE
            else:
                raw_data.append(data_byte)

        elif state == STATE_RLE_BYTE:
            if data_byte == RLE_BYTE:
                raw_data.append(data_byte)
                state = STATE_BYTES
            else:
                rle_byte_value = data_byte
                state = STATE_RLE_COUNT

        elif state == STATE_RLE_COUNT:
            for i in xrange(data_byte):
                raw_data.append(rle_byte_value)
            state = STATE_BYTES

        elif state == STATE_SPECIAL_BYTE:
            if data_byte == SPECIAL_BYTE:
                raw_data.append(data_byte)
                state = STATE_BYTES
            elif data_byte == DEFAULT_INSTR_BYTE:
                state = STATE_DEFAULT_INSTR
            elif data_byte == DEFAULT_WAVE_BYTE:
                state = STATE_DEFAULT_WAVE
            else:
                assert False, "Didn't expect to encounter special "\
                    "instruction byte 0x%x while decompressing" % \
                    (data_byte)

        elif state == STATE_DEFAULT_INSTR:
            for i in xrange(data_byte):
                raw_data.extend(instrument.DEFAULT)

            state = STATE_BYTES
        elif state == STATE_DEFAULT_WAVE:
            for i in xrange(data_byte):
                raw_data.extend(wave.DEFAULT)

            state = STATE_BYTES
        else:
            assert False, "Encountered invalid state %d" % \
                (state) # pragma: no cover

    return raw_data


def compress(raw_data):
    compressed_data = []

    data_index = 0
    data_size = len(raw_data)

    data_index = _compress_rle_region(
        raw_data, data_size, compressed_data, data_index,
        min(project.INSTR_PARAMS[0], data_size))

    if data_index == data_size:
        return compressed_data

    data_index = _compress_default_region(
        raw_data, data_size, compressed_data, data_index,
        project.INSTR_PARAMS[0], project.INSTR_PARAMS[1],
        instrument.DEFAULT, instrument.NUM_PARAMS,
        DEFAULT_INSTR_BYTE)

    if data_index == data_size:
        return compressed_data
    else:
        assert data_index == project.INSTR_PARAMS[1] + 1

    data_index = _compress_rle_region(
        raw_data, data_size, compressed_data, data_index,
        min(project.WAVE_FRAMES[0], data_size))

    if data_index == data_size:
        return compressed_data

    data_index = _compress_default_region(
        raw_data, data_size, compressed_data, data_index,
        project.WAVE_FRAMES[0], project.WAVE_FRAMES[1],
        wave.DEFAULT, wave.NUM_FRAMES,
        DEFAULT_WAVE_BYTE)

    if data_index == data_size:
        return compressed_data
    else:
        assert data_index == project.WAVE_FRAMES[1] + 1

    data_index = _compress_rle_region(
        raw_data, data_size, compressed_data, data_index,
        data_size)

    return compressed_data

def _compress_default_region(raw_data, data_size, compressed_data, data_index,
                             start_data_index, end_data_index, default,
                             default_length, default_special_byte):
    assert data_index == start_data_index

    # For each instrument/wave, figure out whether it's a default or not

    is_default = []

    for index in xrange(start_data_index, min(end_data_index, data_size),
                        default_length):
        if raw_data[index:index + default_length] == default:
            is_default.append(True)
        else:
            is_default.append(False)

    # To compress adjacent default instruments together, as well as to allow
    # maximum compression where defaults are not present, compress the list of
    # booleans derived above into a runlength-encoded format

    last_default_setting = None
    count = 0
    compressed_default_mapping = []

    for default_setting in is_default:
        if (last_default_setting == None or
            last_default_setting == default_setting):

            last_default_setting = default_setting
            count += 1
        else:
            compressed_default_mapping.append((last_default_setting, count))
            last_default_setting = default_setting
            count = 1

    compressed_default_mapping.append((last_default_setting, count))

    assert sum([x[1] for x in compressed_default_mapping]) == len(is_default)

    for (default_setting, count) in compressed_default_mapping:
        if default_setting:
            compressed_data.extend([SPECIAL_BYTE, default_special_byte,
                                    count])

            data_index += default_length * count
        else:
            data_index = _compress_rle_region(
                raw_data, data_size, compressed_data, data_index,
                data_index + count * default_length)

    return data_index

def _compress_rle_region(raw_data, raw_data_size, compressed_data, data_index,
                         end_data_index):
    while data_index < end_data_index:
        data_index = _compress_rle(raw_data, raw_data_size, data_index,
                                   compressed_data, end_data_index)

    return data_index

def _compress_rle(raw_data, raw_data_size,
                  data_index, compressed_data, end_data_index):
    current_byte = raw_data[data_index]

    # RLE encoding byte is uncompressible, so don't attempt to compress it
    if current_byte == RLE_BYTE:
        compressed_data.extend([RLE_BYTE, RLE_BYTE])
        return data_index + 1


    # Do a lookahead to see how many identical bytes are at this
    # point in the stream
    lookahead_index = data_index

    # If you're dealing with the special byte, it makes sense to encode
    # if two or more special bytes occur in succession, since you'll
    # have to double up those bytes in a non-RLE encoding anyway.

    while (lookahead_index < end_data_index
           and lookahead_index < raw_data_size
           and raw_data[lookahead_index] == current_byte
           and lookahead_index - data_index < 255):
        lookahead_index += 1

    num_occurrences = lookahead_index - data_index

    assert num_occurrences > 0

    if current_byte == SPECIAL_BYTE:
        if num_occurrences > 1:
            compressed_data.extend([RLE_BYTE, current_byte,
                                    num_occurrences])
        else:
            compressed_data.extend([SPECIAL_BYTE, SPECIAL_BYTE])

    # If you've got more than three occurrences of the same non-special
    # byte, it makes sense to run-length encode
    elif num_occurrences > 3:
        compressed_data.extend([RLE_BYTE, current_byte, num_occurrences])
    else:
        for i in xrange(num_occurrences):
            compressed_data.append(current_byte)

    return data_index + num_occurrences
