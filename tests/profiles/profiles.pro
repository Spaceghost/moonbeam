QT += core gui quick qml testlib
CONFIG += console c++17 testcase
# Exercise metadata for the packaged Linux FFmpeg/Vulkan configuration.
!contains(CONFIG, no_ffmpeg): DEFINES += HAVE_FFMPEG HAVE_LIBPLACEBO_VULKAN
TARGET = profiles-test
INCLUDEPATH += ../../app
SOURCES += profiles.cpp ../../app/settings/gameprofiles.cpp ../../app/settings/streamingpreferences.cpp ../../app/cli/commandlineparser.cpp
HEADERS += ../../app/settings/streamingpreferences.h ../../app/settings/gameprofiles.h
