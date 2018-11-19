from channels import SONG_MODIFIED
import utils

class ProjectModel(object):
    def __init__(self, parent_view, index, project):
        self.index = index
        self.project = project

        self._parent_view = parent_view
        self._modified = False

        channel = SONG_MODIFIED(index)
        channel.subscribe(self.handle_modified)

    @property
    def index_str(self):
        return "%02d" % (self.index + 1)

    @property
    def name(self):
        if self.project is None:
            return '--'
        else:
            return self.project.name

    @property
    def version(self):
        if self.project is None:
            return '--'
        else:
            return utils.printable_decimal_and_hex(self.project.version)

    @property
    def modified(self):
        if self._modified:
            return "Yes"
        else:
            return "No"

    @property
    def size(self):
        if self.project is None:
            return '--'
        else:
            return utils.printable_decimal_and_hex(self.project.size_blks)

    def handle_modified(self, data=None):
        if data is None:
            return

        project = data

        # We're using False to distinguish the un-setting of a project from a
        # None event (frankly I don't remember why None events would exist in
        # the first place, but since we're catching `if data is None` on the
        # previous lines it must be happening _sometime_)
        if data is False:
            self.project = None
        elif project == self.project:
            self._modified = True
        else:
            self.project = project

        self._parent_view.RefreshObjects([self])
