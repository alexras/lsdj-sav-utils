import wx, json
from wx.lib.pubsub import pub

import channels, utils

from StaticTextViewField import StaticTextViewField
from ViewField import ViewField

class InstrumentPanel(wx.Panel):
    def __init__(self, parent, channel):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.num_fields = 0
        self.updated_fields = 0

        self.instrument = None

        self.pubsub_channel = channel

        if channel is not None:
            pub.subscribe(self._set_instrument, self.pubsub_channel)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.main_sizer = wx.FlexGridSizer(cols=2, hgap=20, vgap=10)

        if channel is not None:
            self.add_header_gui()

        self.sizer.Add(self.main_sizer, wx.EXPAND | wx.ALL)

        if channel is not None:
            self.add_footer_gui()

        self.SetSizer(self.sizer)

    def _set_instrument(self, data):
        self.instrument = data

    def add_header_gui(self):
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        def header_format(instr):
            return "Instrument %02x" % (instr.index)

        self.instrument_name = StaticTextViewField(self, header_format)
        self.instrument_name.subscribe(self.pubsub_channel)
        self.instrument_name.add_to_sizer(header_sizer, 1, wx.ALL)

        self.sizer.Add(header_sizer, 1, wx.EXPAND | wx.ALL)
        self.sizer.AddSpacer(10)

    def add_footer_gui(self):
        import_button = wx.Button(self, wx.ID_ANY, label="Import ...")
        export_button = wx.Button(self, wx.ID_ANY, label="Export ...")

        self.Bind(wx.EVT_BUTTON, self.import_instrument, import_button)
        self.Bind(wx.EVT_BUTTON, self.export_instrument, export_button)

        bottom_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bottom_buttons_sizer.Add(import_button, 1, wx.EXPAND | wx.ALL)
        bottom_buttons_sizer.AddSpacer(10)
        bottom_buttons_sizer.Add(export_button, 1, wx.EXPAND | wx.ALL)

        self.sizer.AddSpacer(15)
        self.sizer.Add(bottom_buttons_sizer, .2, wx.EXPAND | wx.ALL)
        self.sizer.AddSpacer(5)

    def add_field(self, label_text, control, fields=None):
        label = wx.StaticText(self, label=label_text)

        if fields is None:
            fields = [control]

        self.main_sizer.Add(label, 0, wx.ALL)

        map(lambda x: x.subscribe(self.pubsub_channel), fields)
        self.num_fields += len(fields)

        if isinstance(control, ViewField):
            control.add_to_sizer(self.main_sizer, 0, wx.ALL)
        else:
            self.main_sizer.Add(control, 0, wx.ALL)

    def change_instrument(self, instrument):
        # Reset updated fields count since we're about to start changing fields.
        self.updated_fields = 0
        pub.sendMessage(self.pubsub_channel, data=instrument)

    def import_instrument(self, event):
        def ok_handler(dlg, path):
            with open(path, 'r') as fp:
                self.instrument.import_lsdinst(json.load(fp))

            pub.sendMessage(channels.INSTR_IMPORT, data=self.instrument)

        utils.file_dialog(
            "Load instrument", "*.lsdinst", wx.OPEN, ok_handler)

    def export_instrument(self, event):
        def ok_handler(dlg, path):
            instr_json = self.instrument.export()

            with open(path, 'w') as fp:
                json.dump(instr_json, fp, indent=2)

        if not name_empty(self.instrument.name):
            default_file = '%s.lsdinst' % (self.instrument.name)
        else:
            default_file = ''

        utils.file_dialog(
            "Save instrument as ...", "*.lsdinst", wx.SAVE, ok_handler,
            default_file=default_file)

    def field_changed(self):
        """
        We want to call self.Layout() only when all fields have been updated to
        reflect the new instrument. Each field will call this method on its
        parent, and when all fields have updated, we'll trigger a re-layout.
        """

        self.updated_fields += 1

        if self.updated_fields == self.num_fields:
            self.Layout()