#include <QGuiApplication>
#include <QSettings>
#include <QTemporaryDir>
#include <QTest>
#include <QQmlComponent>
#include <QQmlContext>
#include <QQuickItem>
#include <QQuickWindow>
#include "settings/gameprofiles.h"
#include "settings/streamingpreferences.h"
#include "cli/commandlineparser.h"

// Window-system queries are the platform boundary; all preference and parser code is production code.
namespace WMUtils { bool isRunningWayland() { return false; } bool isGpuSlow() { return false; } }

class ProfileModel : public QObject {
    Q_OBJECT
public:
    Q_INVOKABLE QVariantMap getStreamProfile(int id) { return GameProfiles::load("host-ui", id + 1); }
    Q_INVOKABLE bool saveStreamProfile(int id, const QVariantMap& values) { return GameProfiles::save("host-ui", id + 1, values); }
    Q_INVOKABLE void forceActiveFocus() {}
};

class ProfileTest : public QObject {
    Q_OBJECT
private slots:
    void init() { QSettings().clear(); StreamingPreferences::get()->reload(); }
    void isolationAndReset() {
        QVariantMap values{{"width",2560},{"height",1440},{"fps",120},{"bitrateKbps",45000},
                           {"framePacing",true},{"enableHdr",false}};
        QVERIFY(GameProfiles::save("host-a", 7, values));
        QCOMPARE(GameProfiles::load("host-a", 7), values);
        QVERIFY(GameProfiles::load("host-b", 7).isEmpty());
        QVERIFY(GameProfiles::load("host-a", 8).isEmpty());
        QCOMPARE(StreamingPreferences::get()->width, 1920);
        QVERIFY(GameProfiles::save("host-a", 7, {}));
        QVERIFY(GameProfiles::load("host-a", 7).isEmpty());
    }
    void rejectInvalidAtomic() {
        QVERIFY(GameProfiles::save("host", 1, {{"fps",120}}));
        for (const QVariantMap& invalid : {QVariantMap{{"fps",-1}}, QVariantMap{{"fps",120.5}},
                QVariantMap{{"width",100000}}, QVariantMap{{"bitrateKbps",0}},
                QVariantMap{{"videoCodecConfig",3}}, QVariantMap{{"pairingKey","private"}},
                QVariantMap{{"rendererSelection",4},{"enableHdr",true}}, QVariantMap{{"enableHdr","yes"}}}) {
            QVERIFY(!GameProfiles::save("host", 1, invalid));
            QCOMPARE(GameProfiles::load("host", 1).value("fps").toInt(), 120);
        }
        QVERIFY(!GameProfiles::save("", 1, {{"fps",120}}));
        QVERIFY(!GameProfiles::save("host", 0, {{"fps",120}}));
    }
    void snapshotAndReconnect() {
        auto global = StreamingPreferences::get();
        QVERIFY(GameProfiles::save("host", 7, {{"width",2560},{"fps",120}}));
        QScopedPointer<StreamingPreferences> first(StreamingPreferences::forApp(global,"host",7));
        QCOMPARE(first->width,2560); QCOMPARE(first->height,1080); QCOMPARE(first->fps,120);
        QCOMPARE(global->width,1920); QCOMPARE(global->fps,60);
        QVERIFY(GameProfiles::save("host",7,{{"fps",30}}));
        QScopedPointer<StreamingPreferences> retry(StreamingPreferences::forApp(first.data(),"host",7,false));
        QCOMPARE(retry->width,2560); QCOMPARE(retry->fps,120);
        global->fps=144;
        QCOMPARE(first->fps,120); QCOMPARE(retry->fps,120);
    }
    void cliWins() {
        auto global = StreamingPreferences::get();
        QVERIFY(GameProfiles::save("host",7,{{"width",2560},{"height",1440},{"fps",120},
                                            {"bitrateKbps",45000},{"videoDecoderSelection",1}}));
        QScopedPointer<StreamingPreferences> base(StreamingPreferences::forApp(global,{},0,false));
        StreamCommandLineParser parser;
        parser.parse({"moonbeam","stream","host","game","--fps","90","--video-decoder","software"},base.data());
        QScopedPointer<StreamingPreferences> effective(StreamingPreferences::forApp(base.data(),"host",7));
        QCOMPARE(effective->width,2560); QCOMPARE(effective->height,1440); QCOMPARE(effective->fps,90);
        QCOMPARE(effective->videoDecoderSelection, StreamingPreferences::VDS_FORCE_SOFTWARE);
        QCOMPARE(effective->bitrateKbps,StreamingPreferences::getDefaultBitrate(2560,1440,90,false));
        QCOMPARE(global->fps,60);
        parser.parse({"moonbeam","stream","host","game","--no-game-profile","--bitrate","18000"},base.data());
        QScopedPointer<StreamingPreferences> disabled(StreamingPreferences::forApp(base.data(),"host",7));
        QCOMPARE(disabled->width,1920); QCOMPARE(disabled->bitrateKbps,18000);
    }
    void selftestOptions() {
        QScopedPointer<StreamingPreferences> base(StreamingPreferences::forApp(StreamingPreferences::get(),{},0,false));
        StreamCommandLineParser parser;
        parser.parse({"moonbeam","selftest","--video-decoder","hardware","--video-renderer","sdl","--resolution","2560x1440"},base.data(),false);
        QCOMPARE(base->videoDecoderSelection,StreamingPreferences::VDS_FORCE_HARDWARE);
        QCOMPARE(base->rendererSelection,StreamingPreferences::RS_SDL);
        QCOMPARE(base->width,2560); QCOMPARE(base->height,1440);
    }
    void editor() {
        QQmlEngine engine;
        QQuickWindow window; window.resize(1000,900);
        ProfileModel model;
        engine.rootContext()->setContextProperty("window",&window);
        engine.rootContext()->setContextProperty("stackView",&model);
        engine.rootContext()->setContextProperty("profileBackend",&model);
        const auto source=qEnvironmentVariable("GAME_PROFILE_SOURCE");
        QVERIFY(!source.isEmpty());
        QQmlComponent component(&engine);
        component.setData("import QtQuick 2.9\nItem { GameProfileDialog { objectName: \"editor\"; profileModel: profileBackend } }",QUrl::fromLocalFile(source));
        QVERIFY2(component.isReady(),qPrintable(component.errorString()));
        QScopedPointer<QObject> root(component.create());
        QVERIFY2(root,qPrintable(component.errorString()));
        qobject_cast<QQuickItem*>(root.data())->setParentItem(window.contentItem());
        auto editor=root->findChild<QObject*>("editor"); QVERIFY(editor);
        QVERIFY(QMetaObject::invokeMethod(editor,"edit",Q_ARG(QVariant,0),Q_ARG(QVariant,QString("Test game"))));
        QCOMPARE(editor->findChild<QObject*>("profileFps")->property("value").toInt(),60);
        editor->findChild<QObject*>("profileFps")->setProperty("value",120);
        QVERIFY(QMetaObject::invokeMethod(editor,"saveProfile"));
        QCOMPARE(GameProfiles::load("host-ui",1).value("fps").toInt(),120);
        QCOMPARE(StreamingPreferences::get()->fps,60);
        QVERIFY(QMetaObject::invokeMethod(editor,"resetProfile"));
        QVERIFY(GameProfiles::load("host-ui",1).isEmpty());
    }
};
int main(int argc,char** argv) {
    QGuiApplication app(argc,argv);
    QTemporaryDir directory;
    QSettings::setDefaultFormat(QSettings::IniFormat);
    QSettings::setPath(QSettings::IniFormat,QSettings::UserScope,directory.path());
    QCoreApplication::setOrganizationName("Moonbeam tests"); QCoreApplication::setApplicationName("Profiles");
    qmlRegisterSingletonType<StreamingPreferences>("StreamingPreferences",1,0,"StreamingPreferences",
        [](QQmlEngine* engine,QJSEngine*) -> QObject* {
            auto prefs=StreamingPreferences::get(engine);
            QQmlEngine::setObjectOwnership(prefs,QQmlEngine::CppOwnership);
            return prefs;
        });
    ProfileTest test;
    return QTest::qExec(&test,argc,argv);
}
#include "profiles.moc"
