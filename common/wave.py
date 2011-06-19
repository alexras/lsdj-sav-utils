from rich_comparable_mixin import RichComparableMixin

# Binary data for default wave
DEFAULT = [0x8e, 0xcd, 0xcc, 0xbb, 0xaa, 0xa9, 0x99, 0x88, 0x87, 0x76,
           0x66, 0x55, 0x54, 0x43, 0x32, 0x31]

# Frames per wave
NUM_FRAMES = 16

class Wave(RichComparableMixin):
    def __init__(self):
        self.frames = []
