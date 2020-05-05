#!/bin/env python3

"""
https://cgit.kde.org/krunner.git/plain/src/data/org.kde.krunner1.xml
https://api.kde.org/frameworks/krunner/html/runnercontext_8cpp_source.html#l00374
https://techbase.kde.org/Development/Tutorials/Plasma4/AbstractRunner

"""

# qdbus org.kde.krunner /App org.kde.krunner.App.querySingleRunner kpacman pacman

import subprocess
from pathlib import Path
import webbrowser
from dataclasses import dataclass
import configparser
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import pyalpm
from pycman import config


DBusGMainLoop(set_as_default=True)

objpath = "/kpacman"
iface = "org.kde.krunner1"

@dataclass
class Package:
    """minimal alpm package"""
    name: str
    version: str
    desc: str
    url: str
    ico: str
    relevance: float

    def export(self, want_url: bool = False):
        """format for krunner"""
        return (
            self.url if want_url else self.name,
            f"{self.name}\t{self.version}",
            self.ico,
            32,    # type : https://api.kde.org/frameworks/krunner/html/runnercontext_8h_source.html
            self.relevance,
            {"subtext": self.desc}
        )

class Runner(dbus.service.Object):
    def __init__(self):
        """set dbus and load alpm"""
        dbus.service.Object.__init__(self, dbus.service.BusName("net.kpacman2", dbus.SessionBus()), objpath)
        self.alpm = config.init_with_config("/etc/pacman.conf")
        self.local = self.alpm.get_localdb()
        self.pamac = Path('/usr/bin/pamac-manager').is_file()
        self.desc = True       # search in descriptions
        inirc = configparser.ConfigParser()
        inirc.read(f"{Path.home()}/.config/krunnerrc")
        try:
            self.desc = False if inirc['kpacman']['desc'].lower() == "false" else True
        except KeyError:
            pass


    def _getpkgs(self, query: str):
        """find packages by name and description"""

        def setpkg(pkg):
            return Package(
                pkg.name,
                pkg.version,
                pkg.desc,
                pkg.url,
                "system-software-install" if self.local.get_pkg(pkg.name) is not None else "",
                self._setrelevance(pkg, query)
            )

        for repo in self.alpm.get_syncdbs():
            if self.desc:
                for pkg in repo.search(query):
                    yield setpkg(pkg)
            else:
                for pkg in repo.search(""):
                    if not query in pkg.name:
                        continue
                    yield setpkg(pkg)

    def _setrelevance(self, pkg: Package, query: str)->float:
        """display only top 10 by relevance"""
        mini = 0.01
        relevance = mini
        if query == pkg.name:
            relevance = 1
        elif pkg.name.startswith(query) and not "-i18n" in pkg.name:
            relevance = 0.4
        else:
            relevance = 0.2 if query in pkg.name else mini
            if "-i18n" in pkg.name:
                relevance = mini
        return relevance

    @dbus.service.method(iface, in_signature='s', out_signature='a(sssida{sv})')
    def Match(self, query: str):
        """get the matches and returns a packages list"""
        query = query.strip().lower()
        if len(query) < 3:
            return []

        ret = []
        for pkg in self._getpkgs(query):
            ret.append(pkg.export(not self.pamac))
        #print(ret)
        return ret

    @dbus.service.method(iface, in_signature='ss')
    def Run(self, data: str, _action_id: str):
        """click on item"""
        if self.pamac:
            pid = subprocess.Popen(
                ["pamac-manager", f"--details={data}"]
            ).pid
        else:
            webbrowser.open_new_tab(data)
        #print("run...", data, _action_id)


runner = Runner()
loop = GLib.MainLoop()
loop.run()
