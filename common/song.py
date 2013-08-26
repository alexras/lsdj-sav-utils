from utils import assert_index_sane
import bread
import bread_spec

from instruments import Pulse, Wave, Noise, Kit
from synth import Synth
from table import Table
from phrase import Phrase
from chain import Chain
from speech_instrument import SpeechInstrument

# Number of channels
NUM_CHANNELS = 4

class AllocTable(object):
    def __init__(self, song, alloc_table, object_class):
        self.alloc_table = alloc_table

        self.access_objects = []

        for index in xrange(len(alloc_table)):
            self.access_objects.append(object_class(song, index))

    def __getitem__(self, index):
        assert_index_sane(index, len(self.alloc_table))

        if not self.alloc_table[index]:
            return None

        return self.access_objects[index]

    def allocate(self, index):
        self.alloc_table[index] = True

class Instruments(object):
    classes = {
        "pulse": Pulse,
        "wave": Wave,
        "kit": Kit,
        "noise": Noise
    }

    specs = {
        "pulse": bread_spec.pulse_instrument,
        "wave": bread_spec.wave_instrument,
        "kit": bread_spec.kit_instrument,
        "noise": bread_spec.noise_instrument
    }

    def __init__(self, song):
        self.song = song
        self.alloc_table = song.song_data.instr_alloc_table
        self.access_objects = []

        for index in xrange(len(self.alloc_table)):
            instrument_type = song.song_data.instruments[index].instrument_type
            self.access_objects.append(Instruments.classes[instrument_type])

    def set_instrument_type(self, index, instrument_type):
        assert instrument_type in Instruments.classes, (
            "Invalid instrument type '%s'" % (instrument_type))

        assert_index_sane(index, len(self.song.song_data.instruments))

        # Need to change the structure of the song's data to match the new
        # instrument type. We'll do this by creating the raw data for an
        # instrument of the appropriate type, parsing a new instrument out of
        # it, and sticking that into the appropriate place in the song's data.

        instrument_length = len(self.song.song_data.instruments[index])

        instrument_type_index = Instruments.classes.keys().index(
            instrument_type)

        empty_bytes = bytearray([instrument_type_index] +
                                ([0] * (instrument_length - 1)))

        parsed_instrument = bread.parse(
            empty_bytes, Instruments.specs[instrument_type])

        self.song.song_data.instruments[index] = parsed_instrument

        # Finally, we have to make sure that the appropriate access object is
        # being used

        self.access_objects[index] = Instruments.classes(instrument_type)

    def __getitem__(self, index):
        assert_index_sane(index, len(self.alloc_table))

        if not self.alloc_table[index]:
            return None

        return self.access_objects[index]

    def allocate(self, index, instrument_type):
        self.alloc_table[index] = True
        self.set_instrument_type(index, instrument_type)


class Grooves(object):
    def __init__(self, song):
        self.song = song

    def __getitem__(self, index):
        assert_index_sane(index, len(self.song.song_data.grooves))

        return self.song.song_data.grooves[index]

class Sequence(object):
    PU1 = "pu1"
    PU2 = "pu2"
    WAV = "wav"
    NOI = "noi"

    def __init__(self, song):
        self.song = song

    def __getitem__(self, index):
        assert_index_sane(index, len(self.song.song_data.song))
        raw_chain = self.song.song_data.song[index]

        chain_objs = {}

        for channel in [Sequence.PU1, Sequence.PU2, Sequence.WAV, Sequence.NOI]:
            chain_number = getattr(raw_chain, channel)

            chain = self.song.chains[chain_number]

            if chain is not None:
                chain_objs[channel] = chain

        return chain_objs

    def __setitem__(self, index, value_dict):
        assert_index_sane(index, len(self.song.song_data.song))

        for channel in value_dict:
            assert (channel in [Sequence.PU1, Sequence.PU2, Sequence.WAV,
                                Sequence.NOI]), \
                ("Channel '%d' is not a valid channel" % (channel))

            chain = value_dict[channel]
            chain_number = chain.index

            assert_index_sane(chain_number,
                              len(self.song.song_data.chain_alloc_table))

            assert self.song.song_data.chain_alloc_table[chain_number], (
                "Assigning a chain (%d) that has not been allocated" % (
                    chain_number))

            setattr(self.song.song_data.song[index], channel, chain_number)

class Synths(object):
    def __init__(self, song):
        self.song = song

    def __getitem__(self, index):
        assert_index_sane(index, len(self.song.song_data.softsynth_params))

        return Synth(self.song, index)

class Song(object):
    """A song consists of a sequence of chains, one per channel.
    """
    def __init__(self, song_data):
        # Check checksums
        assert song_data.mem_init_flag_1 == 'rb'
        assert song_data.mem_init_flag_2 == 'rb'
        assert song_data.mem_init_flag_3 == 'rb'

        # Everything we do to the song or any of its components should update
        # the song data object, so that we can rely on bread's writer to write
        # it back out in the right format
        self.song_data = song_data

        self._instruments = Instruments(self)

        # Stitch together allocated tables
        self._tables = AllocTable(
            song = self,
            alloc_table = self.song_data.table_alloc_table,
            object_class = Table)

        # Stitch together allocated phrases
        self._phrases = AllocTable(
            song = self,
            alloc_table = self.song_data.phrase_alloc_table,
            object_class = Phrase)

        # Stitch together allocated chains
        self._chains = AllocTable(
            song = self,
            alloc_table = self.song_data.chain_alloc_table,
            object_class = Chain)

        self._grooves = Grooves(self)
        self._speech_instrument = SpeechInstrument(self)
        self._synths = Synths(self)

    @property
    def instruments(self):
        return self._instruments

    @property
    def phrases(self):
        return self._phrases

    @property
    def chains(self):
        return self._chains

    @property
    def grooves(self):
        return self._grooves

    @property
    def speech_instrument(self):
        return self._speech_instrument

    @property
    def synths(self):
        return self._synths

    @property
    def clock(self):
        return Clock(self.song_data.clock)

    @property
    def global_clock(self):
        return Clock(self.song_data.global_clock)

    @property
    def song_version(self):
        return self.song_data.version

    @song_version.setter
    def song_version(self, version):
        self.song_data.version = version

# For fields with a one-to-one correspondence with song data, we'll
# programmatically insert properties to avoid repetition
for field in ["tempo", "tune_setting", "key_delay", "key_repeat",
              "font", "sync_setting", "colorset", "clone",
              "file_changed", "power_save", "prelisten", "bookmarks",
              "wave_synth_overwrite_lock"]:
    def field_getter(self):
        return getattr(self.song_data, field)

    def field_setter(self, value):
        setattr(self.song_data, field, value)

    setattr(Song, field, property(fset=field_setter, fget=field_getter))
