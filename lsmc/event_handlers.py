import wx, os

from pylsdj.savfile import SAVFile
from pylsdj.project import load_lsdsng, load_srm

import utils

def open_sav(event, projects_window, main_window):
    def ok_handler(dlg, path):
        # When loading the .sav file, we'll update a progress dialog box
        progress_dlg = wx.ProgressDialog(
            "Loading %s" % (path), "Starting import ...", 100)

        sav_obj = None

        def progress_update_function(message, step, total_steps, still_working):
            progress_dlg.Update((step * 100) / total_steps, newmsg = message)

        try:
            sav_obj = SAVFile(path, callback=progress_update_function)
        except ValueError, e:
            utils.show_error_dialog("Failed to load '%s'" % (dlg.GetFilename()),
                                    str(e), projects_window)

        if sav_obj is not None:
            main_window.set_sav(sav_obj)
            main_window.update_models()
            progress_dlg.Destroy()

    # Display an open dialog box so the user can select a .sav file
    utils.file_dialog("Choose a .sav file", '*.sav', wx.OPEN, ok_handler)

def save_sav(event, projects_window, main_window):
    save_sav(main_window.sav_obj)

def save_sav(sav_obj):
    def ok_handler(dlg, path):
        progress_dlg = wx.ProgressDialog(
            "Saving %s" % (path), "Reticulating splines", 100)

        def progress_update_function(message, step, total_steps, still_working):
            progress_dlg.Update((step * 100) / total_steps, newmsg = message)

        sav_obj.save(path, callback=progress_update_function)

    utils.file_dialog("Save .sav as ...", "*.sav", wx.SAVE, ok_handler)

def save_song(event, projects_window, main_window):
    song_to_save = projects_window.sav_project_list.GetSelectedObject()[1]

    save_song(song_to_save)

def save_song(song_to_save):
    def ok_handler(dlg, path):
        song_to_save.save(path)

    utils.file_dialog(
        "Save '%s'" % (song_to_save.name), "*.lsdsng", wx.SAVE, ok_handler)


def get_song_from_windows(projects_window, main_window):
    selected_obj = projects_window.sav_project_list.GetSelectedObject()
    index, current_proj = selected_obj

    if current_proj is not None:
        utils.show_error_dialog(
            "Invalid Selection",
            "Song slot %d is currently occupied and cannot be saved over" %
            (index + 1))
        return

    sav_obj = main_window.get_sav()

    return (index, sav_obj)

def add_song(event, projects_window, main_window):
    index, sav_obj = get_song_from_windows(
        projects_window, main_window)

    def ok_handler(dlg, path):
        try:
            proj = load_lsdsng(path)
            sav_obj.projects[index] = proj
        except Exception, e:
            show_error_dialog("can't load file", 'Error loading file: %s' % (e),
                              None)

    utils.file_dialog("Open .lsdsng", "*.lsdsng", wx.OPEN, ok_handler)

    main_window.update_models()

def add_srm(event, projects_window, main_window):
    index, sav_obj = get_song_from_windows(
        projects_window, main_window)

    def ok_handler(dlg, path):
        try:
            proj = load_srm(path)
            sav_obj.projects[index] = proj
        except Exception, e:
            show_error_dialog(
                "can't load file", 'Error loading file: %s' % (e), None)

    utils.file_dialog("Open .srm", "*.srm", wx.OPEN, ok_handler)

    main_window.update_models()
