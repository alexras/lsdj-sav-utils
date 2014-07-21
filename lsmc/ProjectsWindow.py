import wx, functools, event_handlers
from ObjectListView import ColumnDefn

import utils
import common.utils as cu
from SongWindow import SongWindow

from channels import SONG_MODIFIED

class ProjectsWindow(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        # List the projects in the currently loaded .sav
        self.sav_project_list = utils.new_obj_list_view(self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.open_song,
                  self.sav_project_list)

        self.sav_project_list.SetEmptyListMsg("No .sav loaded")

        # Keep track of the projects to whose channels you're subscribing to
        # avoid subscribing multiple times
        self.subscribed_projects = {}

        def string_getter(x, attr):
            if x[1] is None:
                return "--"
            else:
                obj_attr = getattr(x[1], attr)

                if isinstance(obj_attr, (int, float, long, complex)):
                    return cu.printable_decimal_and_hex(obj_attr)
                else:
                    return obj_attr

        def modified_getter(x):
            if x[1] is not None and x[1].modified:
                return "Yes"
            else:
                return "No"

        index_col = ColumnDefn("#", "center", 30, lambda x: "%02d" % (x[0] + 1))

        mod_col = ColumnDefn("Modified", "center", 60, modified_getter)

        name_col = ColumnDefn(
            "Song Name", "left", 200,
            functools.partial(string_getter, attr="name"), isSpaceFilling=True)
        name_col.freeSpaceProportion = 2

        version_col = ColumnDefn(
            "Version", "left", 50,
            functools.partial(string_getter, attr="version"),
            isSpaceFilling=True)
        version_col.freeSpaceProportion = 1

        size_col = ColumnDefn(
            "Size (Blocks)", "left", 100,
            functools.partial(string_getter, attr="size_blks"),
            isSpaceFilling=True)

        size_col.freeSpaceProportion = 1
        self.sav_project_list.SetColumns(
            [mod_col, index_col, name_col, version_col, size_col])

        self.open_sav_button = self.new_button(
            "Open .sav File ...", event_handlers.open_sav)

        self.save_sav_button = self.new_button(
            "Save .sav File as ...", event_handlers.save_sav,
            start_disabled=True)

        self.add_song_button = self.new_button(
            "Add Song as .lsdsng ...", event_handlers.add_song,
            start_disabled=True)

        self.export_song_button = self.new_button(
            "Export Selected as .lsdsng ...", event_handlers.save_song,
            start_disabled=True)

        self.open_song_button = self.new_button(
            "Open Song ...", self.open_song, start_disabled=True,
            internal_handler=True)

        self.Bind(
            wx.EVT_LIST_ITEM_SELECTED, self.handle_song_selection_changed,
            self.sav_project_list)
        self.Bind(
            wx.EVT_LIST_ITEM_DESELECTED, self.handle_song_selection_changed,
            self.sav_project_list)

        buttons_layout = wx.BoxSizer(wx.VERTICAL)

        def add_side_button(btn):
            buttons_layout.Add(btn, 1, flag=wx.EXPAND | wx.ALL)
            buttons_layout.AddSpacer(10)

        buttons_layout.AddSpacer(20)
        add_side_button(self.open_sav_button)
        add_side_button(self.save_sav_button)
        buttons_layout.AddSpacer(20)

        add_side_button(self.add_song_button)
        buttons_layout.AddSpacer(20)

        add_side_button(self.open_song_button)
        add_side_button(self.export_song_button)

        window_layout = wx.BoxSizer(wx.HORIZONTAL)
        window_layout.Add(self.sav_project_list, 1, wx.EXPAND | wx.ALL)
        window_layout.AddSpacer(10)
        window_layout.Add(buttons_layout)
        window_layout.AddSpacer(10)

        self.SetSizer(window_layout)

    def new_button(self, label, evt_button_handler, start_disabled=False,
                   internal_handler=False):
        btn = wx.Button(self, wx.ID_ANY, label=label)

        if start_disabled:
            btn.Disable()

        if internal_handler:
            handler = evt_button_handler
        else:
            handler = functools.partial(
                evt_button_handler, projects_window=self,
                main_window=self.GetGrandParent())

        self.Bind(wx.EVT_BUTTON, handler, btn)

        return btn

    def get_project_list(self):
        sav_obj = self.GetGrandParent().sav_obj

        if sav_obj is None:
            return None

        return sav_obj.project_list

    def update_models(self, data=None):
        project_list = self.get_project_list()

        if project_list is None:
            return

        self.sav_project_list.SetObjects(project_list)

        for index, project in project_list:
            if project is not None and project not in self.subscribed_projects:
                self.subscribed_projects[project] = True
                channel = SONG_MODIFIED(project)
                channel.subscribe(self.update_models)


    def handle_song_selection_changed(self, event):
        selected_objects = self.sav_project_list.GetSelectedObjects()

        full_song_buttons = [self.export_song_button, self.open_song_button]
        empty_song_buttons = [self.add_song_button]

        if len(selected_objects) > 0:
            if len(filter(lambda x: x[1] is None, selected_objects)) > 0:
                map(lambda x: x.Disable(), full_song_buttons)
                map(lambda x: x.Enable(), empty_song_buttons)
            else:
                map(lambda x: x.Enable(), full_song_buttons)
                map(lambda x: x.Disable(), empty_song_buttons)
        else:
            map(lambda x: x.Disable(), full_song_buttons)
            map(lambda x: x.Disable(), empty_song_buttons)

        # Make sure event propagation can continue
        event.Skip()

    def handle_close(self, event):
        try:
            if self.projects_modified():
                message = (
                    'Some songs have been modified. Unsaved hanges to the '
                    '.sav file will be lost. Save the .sav file '
                    'before closing?')
                title = ('Save .sav file?')

                save_prompt = wx.MessageDialog(
                    self, message, title, wx.YES_NO | wx.ICON_QUESTION)

                if save_prompt.ShowModal() == wx.ID_YES:
                    event_handlers.save_sav(self.GetGrandParent().sav_obj)
        finally:
            self.Destroy()

    def projects_modified(self):
        project_list = self.get_project_list()

        if project_list is not None:
            for index, project in self.get_project_list():
                if project is not None and project.modified:
                    return True
        return False

    def open_song(self, event):
        selected_objects = self.sav_project_list.GetSelectedObjects()

        if len(selected_objects) != 1:
            return

        proj = selected_objects[0][1]

        if proj is None:
            return

        song_window = SongWindow(self, proj)
