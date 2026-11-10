QT += core gui quick qml testlib
CONFIG += console c++17 testcase
TARGET = profiles-test
INCLUDEPATH += ../../app
SOURCES += profiles.cpp ../../app/settings/gameprofiles.cpp ../../app/settings/streamingpreferences.cpp ../../app/cli/commandlineparser.cpp
HEADERS += ../../app/settings/streamingpreferences.h ../../app/settings/gameprofiles.h
