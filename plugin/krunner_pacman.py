#!/bin/env python3

"""
https://cgit.kde.org/krunner.git/plain/src/data/org.kde.krunner1.xml
https://api.kde.org/frameworks/krunner/html/runnercontext_8cpp_source.html#l00374
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

    @dbus.service.method(iface, in_signature='s', out_signature='a(sssida{sv})')
    def Match(self, query: str):
        """This method is used to get the matches and it returns a list of lists/tupels"""
        if len(query) < 3:
            return []
        query = query.lower()
        if not self.alpm:
            self.alpm = config.init_with_config("/etc/pacman.conf")
            self.local = self.alpm.get_localdb()

        pkgs = []
        for repo in self.alpm.get_syncdbs():
            pkgs = pkgs + repo.search(query)

        ret = []
        match = 0.05
        for pkg in pkgs:
            match += 0.01
            relevance = len(query) if query == pkg.name else match
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
        if self.pamac:
            subprocess.Popen(['pamac-manager', f"--details={data}"])
        else:
            webbrowser.open_new_tab(data)
        #print("run...", data, _action_id)


runner = Runner()
loop = GLib.MainLoop()
loop.run()
