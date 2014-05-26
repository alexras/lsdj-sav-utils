import wx
from wx.lib.pubsub import pub

import channels

from ImageSetViewField import ImageSetViewField
from ReadOnlyTextViewField import ReadOnlyTextViewField
from viewutils import instr_attr, one_digit_hex_format, two_digit_hex_format, \
    within

WAVE_IMAGES = {
    "sawtooth": wx.Image("images/synth_saw.gif", wx.BITMAP_TYPE_GIF),
    "square": wx.Image("images/synth_square.gif", wx.BITMAP_TYPE_GIF),
    "sine": wx.Image("images/synth_sine.gif", wx.BITMAP_TYPE_GIF)
}

def add_field(parent, label_text, control, sizer):
    label = wx.StaticText(parent, label=label_text)

    sizer.Add(label, 0, wx.ALL)

    control.subscribe(channels.SYNTH_CHANGE)

    control.add_to_sizer(sizer, 0, wx.ALL)


class RangeFieldsSubPanel(wx.Panel):
    def __init__(self, parent, range_param):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.hpos = 0

        self.sizer = wx.GridBagSizer(hgap=20, vgap=7)

        self.sizer.Add(wx.StaticText(self, label=range_param.capitalize()),
                       pos=(0,0), span=(1,2))
        self.hpos += 1

        self.volume = ReadOnlyTextViewField(
            self, within(range_param, two_digit_hex_format("volume")))
        self.filter_cutoff = ReadOnlyTextViewField(
            self, within(range_param, two_digit_hex_format(
                "filter_cutoff")))
        self.phase_amount = ReadOnlyTextViewField(
            self, within(range_param, two_digit_hex_format(
                "phase_amount")))
        self.vertical_shift = ReadOnlyTextViewField(
            self, within(range_param, two_digit_hex_format(
                "vertical_shift")))

        self.add_field("Volume", self.volume, self.sizer)
        self.add_field("Cutoff", self.filter_cutoff, self.sizer)
        self.add_field("Phase", self.phase_amount, self.sizer)
        self.add_field("VShift", self.vertical_shift, self.sizer)

        self.SetSizer(self.sizer)

    def add_field(self, label_text, control, sizer):
        label = wx.StaticText(self, label=label_text)

        sizer.Add(label, pos=(self.hpos, 0), flag=wx.ALL)
        control.subscribe(channels.SYNTH_CHANGE)
        control.add_to_sizer(sizer, pos=(self.hpos, 1), flag=wx.ALL)

        self.hpos += 1

    def field_changed(self):
        pass


class SelectedSynthPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        pub.subscribe(self.handle_synth_changed, channels.SYNTH_CHANGE)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        main_params_sizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=7)

        self.wave_type = ImageSetViewField(
            self, instr_attr("waveform"), WAVE_IMAGES)
        self.filter_type = ReadOnlyTextViewField(
            self, instr_attr("filter_type"))
        self.resonance = ReadOnlyTextViewField(
            self, one_digit_hex_format("filter_resonance"))
        self.distortion = ReadOnlyTextViewField(
            self, instr_attr("distortion"))
        self.phase_type = ReadOnlyTextViewField(
            self, instr_attr("phase_type"))

        self.add_field("Wave", self.wave_type, main_params_sizer)
        self.add_field("Filter", self.filter_type, main_params_sizer)
        self.add_field("Q", self.resonance, main_params_sizer)
        self.add_field("Dist", self.distortion, main_params_sizer)
        self.add_field("Phase", self.phase_type, main_params_sizer)

        self.sizer.Add(main_params_sizer, 1, wx.ALL | wx.EXPAND)

        self.start_range_params = RangeFieldsSubPanel(self, "start")
        self.end_range_params = RangeFieldsSubPanel(self, "end")

        self.sizer.Add(self.start_range_params, 1, wx.ALL | wx.EXPAND)
        self.sizer.Add(self.end_range_params, 1, wx.ALL | wx.EXPAND)

        self.SetSizer(self.sizer)
        self.Layout()

    def field_changed(self):
        pass

    def handle_synth_changed(self, data):
        synth = data
        self.Layout()

    def add_field(self, label_text, control, sizer):
        label = wx.StaticText(self, label=label_text)

        sizer.Add(label, 0, wx.ALL)
        control.subscribe(channels.SYNTH_CHANGE)
        control.add_to_sizer(sizer, 0, wx.ALL)
