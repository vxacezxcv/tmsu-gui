#!/usr/bin/python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import subprocess as sp

class Tmsu:
    def __init__(self, tmsu):
        self.tmsu = tmsu

    def info(self):
        try:
            r = self._cmd('info')
        except sp.CalledProcessError as e:
            if e.returncode == 1: # database doesn't exist
                return None
        lines = r.splitlines()
        def psplit(l): return map(lambda x: x.strip(), l.split(':'))
        d = dict(map(psplit, lines))

        return {'root': d['Root path'],
                'size': d['Size'],
                'database':d['Database']}

    def tags(self, fileName=None):
        if fileName:
            # Note: tmsu behaves differently for 'tags' command when used
            # interactively and called from scripts.
            r = self._cmd('tags -n {}'.format(fileName))
            return r.split(':')[1].split()
        return self._cmd('tags').splitlines()

    def tag(self, fileName, tagName):
        try:
            self._cmd('tag {} {}'.format(fileName, tagName))
            return True
        except sp.CalledProcessError as e:
            print("Failed to tag file.")
            return False

    def untag(self, fileName, tagName):
        try:
            self._cmd('untag {} {}'.format(fileName, tagName))
            return True
        except sp.CalledProcessError as e:
            print("Failed to untag file.")
            return False

    def _cmd(self, cmd):
        return sp.check_output('tmsu ' + cmd, shell=True).decode('utf-8')

    @staticmethod
    def findTmsu():
        import shutil
        tmsu =  shutil.which("tmsu")
        if tmsu:
            return Tmsu(tmsu)
        else:
            return None

class MyWindow(Gtk.Window):
    def __init__(self, tmsu, fileName):
        Gtk.Window.__init__(self, title="Tags")

        self.tmsu = tmsu
        self.fileName = fileName

        self.set_size_request(300, 400)
        self.vbox = Gtk.Box(parent = self,
                            orientation = Gtk.Orientation.VERTICAL)
        self.store = Gtk.ListStore(str, bool)


        # tag name column
        self.list_widget = Gtk.TreeView(self.store)
        col = Gtk.TreeViewColumn("Tags", Gtk.CellRendererText(editable=True), text=0)
        col.set_expand(True)
        self.list_widget.append_column(col)

        # 'tagged' checkbox column
        cell = Gtk.CellRendererToggle()
        cell.connect("toggled", self.on_cell_toggled)
        col = Gtk.TreeViewColumn("Checked", cell, active=1)
        self.list_widget.append_column(col)
        self.vbox.pack_start(self.list_widget, True, True, 0)

        hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
        self.tag_edit = Gtk.Entry()
        self.add_button = Gtk.Button(label = "Add")
        hbox.pack_start(self.tag_edit, True, True, 0)
        hbox.pack_end(self.add_button, False, False, 0)
        self.vbox.pack_end(hbox, False, False, 0)

        self.loadTags()

    def on_cell_toggled(self, widget, path):
        tagName = self.store[path][0]
        isTagged = self.store[path][1]
        if not isTagged:
            r = self.tagFile(tagName)
        else:
            r = self.untagFile(tagName)

        # toggle
        if r: self.store[path][1] = not self.store[path][1]

    def tagFile(self, tagName):
        if not self.tmsu.tag(self.fileName, tagName):
            self.displayError("Failed to tag file.")
            return False
        return True

    def untagFile(self, tagName):
        if not self.tmsu.untag(self.fileName, tagName):
            self.displayError("Failed to untag file.")
            return False
        return True

    def loadTags(self):
        allTags = self.tmsu.tags()
        fileTags = self.tmsu.tags(self.fileName)
        for tag in allTags:
            self.store.append([tag, tag in fileTags])

    def displayError(self, msg):
        dialog = Gtk.MessageDialog(
            self, Gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.CLOSE, msg)
        dialog.run()
        dialog.destroy()

if __name__ == "__main__":
    err = None
    tmsu = Tmsu.findTmsu()
    if not tmsu:
        err = "tmsu executable not found!"
    elif tmsu.info() == None:
        err = "No tmsu database is found."

    if err:
        dialog = Gtk.MessageDialog(
            None, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, err)
        dialog.run()
    else:
        print(tmsu.info())
        print(tmsu.tags("testfile"))
        win = MyWindow(tmsu, "testfile2")
        win.connect('delete-event', Gtk.main_quit)
        win.show_all()
        Gtk.main()