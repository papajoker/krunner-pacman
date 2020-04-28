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
import gi
gi.require_version('Pamac', '9.0')
from gi.repository import Pamac
from gi.repository import GLib


DBusGMainLoop(set_as_default=True)

objpath = "/kpacman"
iface = "org.kde.krunner1"

class Runner(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(self, dbus.service.BusName("net.kpacman2", dbus.SessionBus()), objpath)
        config = Pamac.Config(conf_path="/etc/pamac.conf")
        config.set_enable_aur(False)
        self.db = Pamac.Database(config=config)

    @dbus.service.method(iface, in_signature='s', out_signature='a(sssida{sv})')
    def Match(self, query: str):
        """This method is used to get the matches and it returns a list"""
        query = query.strip().lower()
        if len(query) < 3:
            return []

        ret = []
        match = 0.01
        for pkg in self.db.search_pkgs(query):
            relevance = match
            name = pkg.get_name()
            if query == name:
                relevance = 1
            elif name.startswith(query) and not "-i18n" in name:
                relevance = 0.4
            else:
                relevance = 0.2 if query in name else match
                if "-i18n" in name:
                    relevance = 0.02
            ico = "system-software-install" if pkg.get_reason() else ""
            ret.append((
                name,
                f"{name}\t{pkg.get_version()}",
                ico,
                32,    # type : https://api.kde.org/frameworks/krunner/html/runnercontext_8h_source.html
                relevance,
                {"subtext": pkg.get_desc()}
            ))
        return ret

    @dbus.service.method(iface, in_signature='ss')
    def Run(self, data: str, _action_id: str):
        """click on item"""
        subprocess.Popen(['pamac-manager', f"--details={data}"])
        #print("run...", data, _action_id)


runner = Runner()
loop = GLib.MainLoop()
loop.run()
