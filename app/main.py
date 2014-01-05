#!/usr/bin/env python

import wx, functools, event_handlers
from ObjectListView import ObjectListView, ColumnDefn

import common.utils as cu

app = wx.App(False)

class ProjectsWindow(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        # List the projects in the currently loaded .sav
        self.sav_project_list = ObjectListView(
            self, wx.ID_ANY, style=wx.LC_REPORT)
        self.sav_project_list.SetEmptyListMsg("No .sav loaded")

        def string_getter(x, attr):
            if x[1] is None:
                return "--"
            else:
                obj_attr = getattr(x[1], attr)

                if isinstance(obj_attr, (int, float, long, complex)):
                    return cu.printable_decimal_and_hex(obj_attr)
                else:
                    return obj_attr
        index_col = ColumnDefn("#", "left", 40, lambda x: "%d" % (x[0]))

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
            [index_col, name_col, version_col, size_col])

        export_proj_button = wx.Button(
            self, wx.ID_ANY, label="Export Selected as .lsdsng")
        add_proj_button = wx.Button(
            self, wx.ID_ANY, label="Add Song as .lsdsng")

        buttons_layout = wx.BoxSizer(wx.VERTICAL)
        for i, button in enumerate([add_proj_button, export_proj_button]):
            buttons_layout.Add(button, i, wx.EXPAND)
            buttons_layout.AddSpacer(10)

        window_layout = wx.BoxSizer(wx.HORIZONTAL)
        window_layout.Add(self.sav_project_list, 1, wx.EXPAND | wx.ALL)
        window_layout.AddSpacer(10)
        window_layout.Add(buttons_layout)
        window_layout.AddSpacer(10)

        self.SetSizer(window_layout)

    def update_models(self, sav_obj):
        self.sav_project_list.SetObjects(
            [(i, sav_obj.projects[i]) for i in sorted(sav_obj.projects.keys())])

class MainNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=wx.BK_DEFAULT)
        self.sav_obj = None

        self.songs_window = ProjectsWindow(self)

        self.AddPage(self.songs_window, "Songs")

        # Event binding
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.on_page_changing)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_page_changed)

    def on_page_changing(self, event):
        print "page changing ", event.GetOldSelection(), event.NewSelection(), self.GetSelection()
        event.Skip()

    def on_page_changed(self, event):
        print "page changed ", event.GetOldSelection(), event.NewSelection(), self.GetSelection()
        event.Skip()

    def update_models(self, sav_obj):
        self.sav_obj = sav_obj
        self.songs_window.update_models(sav_obj)

class MenuBar(wx.MenuBar):
    def __init__(self, parent):
        wx.MenuBar.__init__(self)
        self.parent = parent

        file_menu = wx.Menu()
        file_menu.Append(101, "&Open .sav ...", "Open a .sav file")

        self.Bind(wx.EVT_MENU, functools.partial(
            event_handlers.open_sav, main_window=parent.notebook))

        self.Append(file_menu, "&File")

class MainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "LSDJ .sav Utils", size=(600,400))

        panel = wx.Panel(self)
        self.notebook = MainNotebook(panel)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)

        panel.SetSizer(sizer)

        self.SetMenuBar(MenuBar(self))

        # Display
        self.Layout()
        self.Show()

starting_window = MainWindow()
app.MainLoop()
