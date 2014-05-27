import wx, time, random, os
from ObjectListView import ObjectListView

def random_pos(window_dimensions):
    win_width, win_height = window_dimensions
    screen_width, screen_height = wx.DisplaySize()

    padding = 20

    return (random.randint(0, screen_width - win_width - padding),
            random.randint(0, screen_height - win_height - padding))

def new_obj_list_view(parent):
    view = ObjectListView(parent, wx.ID_ANY, style=wx.LC_REPORT)
    enable_single_selection(view, parent)
    view.oddRowsBackColor = wx.LIGHT_GREY

    return view

def _single_select_event_handler(event):
    view = event.GetEventObject()

    selected_objects = view.GetSelectedObjects()

    if len(selected_objects) > 1:
        view.DeselectAll()
        view.SelectObject(selected_objects[0])

def enable_single_selection(obj_list_view, window):
    window.Bind(wx.EVT_LIST_ITEM_SELECTED, _single_select_event_handler,
                obj_list_view)

def file_dialog(message, wildcard, style, ok_handler, default_file = ''):
    default_dir = '.'

    dlg = wx.FileDialog(
        None, message, default_dir, default_file, wildcard, style)

    try:
        if dlg.ShowModal() == wx.ID_OK:
            path = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            ok_handler(dlg, path)
    finally:
        dlg.Destroy()

def make_image(relative_path):
    resource_path = os.getenv("RESOURCEPATH")

    if resource_path is None:
        resource_path = os.path.abspath(os.path.join(__file__, os.pardir))

    absolute_path = os.path.join(resource_path, *relative_path)

    extension = os.path.splitext(relative_path[-1])[1]

    if extension == ".gif":
        file_type = wx.BITMAP_TYPE_GIF
    elif extension == ".png":
        file_type = wx.BITMAP_TYPE_PNG

    return wx.Image(absolute_path, file_type)