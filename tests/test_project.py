import json, os, sys, math

sys.path.append(
    os.path.dirname(os.path.abspath(os.path.join(__file__, os.path.pardir))))

import common.filepack as filepack
from common.project import Project


def test_read_write_project():
    with open("test_data/sample_song_compressed.json") as fp:
        song_data_compressed = json.load(fp)

    song_data = filepack.decompress(song_data_compressed)
    song_name = "UNTOLDST"
    song_version = 23

    proj = Project(song_name, song_version, song_data)
    empty_instruments = [i for i in xrange(len(proj.song.instruments.alloc_table)) if proj.song.instruments.alloc_table[i] == 0]

    # for instrument_id in empty_instruments:
    #     print map(hex, song_data[0x3080 + 16 * instrument_id: 0x3080 + 16 * (instrument_id + 1)])

    assert proj.name == song_name
    assert proj.version == song_version

    raw_data = proj.get_raw_data()
    myhex = lambda x: "0x%02x" % (x)

    recompressed = filepack.compress(raw_data)

    assert math.fabs(len(recompressed) - len(song_data_compressed)) < 512

    # Do comparison based on parsed object, since the actual input data can
    # contain noise
    proj_from_raw_data = Project(song_name, song_version, raw_data)

    assert proj_from_raw_data._song_data == proj._song_data
