#!/bin/env python3

"""
https://cgit.kde.org/krunner.git/plain/src/data/org.kde.krunner1.xml
https://api.kde.org/frameworks/krunner/html/runnercontext_8cpp_source.html#l00374
https://techbase.kde.org/Development/Tutorials/Plasma4/AbstractRunner

or a framework ? https://github.com/Shihira/krunner-bridge
"""

# qdbus org.kde.krunner /App org.kde.krunner.App.querySingleRunner kpacman pacman

import subprocess
from pathlib import Path
import webbrowser
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import pyalpm
from pycman import config


DBusGMainLoop(set_as_default=True)

objpath = "/kpacman"
iface = "org.kde.krunner1"

class Runner(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(self, dbus.service.BusName("net.kpacman2", dbus.SessionBus()), objpath)
        self.alpm = None
        self.local = None
        self.pamac = Path('/usr/bin/pamac-manager').is_file()

    def _getpkgs(self, query: str):
        pkgs = []
        for repo in self.alpm.get_syncdbs():
            pkgs = pkgs + repo.search(query)
        return pkgs

    @dbus.service.method(iface, in_signature='s', out_signature='a(sssida{sv})')
    def Match(self, query: str):
        """This method is used to get the matches and it returns a list"""
        query = query.strip().lower()
        if len(query) < 3:
            return []

        if not self.alpm:
            self.alpm = config.init_with_config("/etc/pacman.conf")
            self.local = self.alpm.get_localdb()

        pkgs = self._getpkgs(query)

        ret = []
        match = 0.1
        for pkg in pkgs:
            relevance = match
            if query == pkg.name:
                relevance = 1
            elif pkg.name.startswith(query):
                relevance = 0.5
            else:
                relevance = 0.2 if query in pkg.name else match
            ico = "system-software-install" if self.local.get_pkg(pkg.name) else ""
            data = pkg.name if self.pamac else pkg.url
            ret.append((
                data,
                f"{pkg.name}\t{pkg.version}",
                ico,
                32,    # type : https://api.kde.org/frameworks/krunner/html/runnercontext_8h_source.html
                relevance,
                {"subtext": pkg.desc, "urls": pkg.url}
            ))
        return ret

    @dbus.service.method(iface, in_signature='ss')
    def Run(self, data: str, _action_id: str):
        """click on item"""
        if self.pamac:
            subprocess.Popen(['pamac-manager', f"--details={data}"])
        else:
            webbrowser.open_new_tab(data)
        #print("run...", data, _action_id)


runner = Runner()
loop = GLib.MainLoop()
loop.run()
