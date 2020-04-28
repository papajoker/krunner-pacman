#!/usr/bin/bash

echo "ps -aux | grep 'krunner_pacman'"

sudo cp resources/net.kpacman2.service /usr/share/dbus-1/services/
sudo cp resources/kpacman2.service /usr/lib/systemd/user/
sudo cp resources/plasma-runner-kpacman.desktop /usr/share/kservices5/
sudo cp plugin/krunner_pacman.py /usr/lib/qt/plugins/
sudo chmod +x /usr/lib/qt/plugins/krunner_pacman.py

if [[ "$1" == "-l" ]]; then
    sudo rm /usr/share/dbus-1/services/net.kpacman2.service
    sudo rm /usr/lib/qt/plugins/krunner_pacman.py
    echo "python plugin/krunner_pacman.py # load dbus server in other terminal"
    #python plugin/krunner_pacman.py &
fi

if [[ "$1" == "-r" ]]; then
    sudo rm /usr/share/dbus-1/services/net.kpacman2.service
    sudo rm /usr/share/kservices5/plasma-runner-kpacman.desktop
    sudo rm /usr/lib/qt/plugins/krunner_pacman.py
    ps -aux | grep 'krunner_pacman'
fi

kquitapp5 krunner
#kstart5 krunner
qdbus org.kde.krunner /App org.kde.krunner.App.querySingleRunner kpacman pacman
