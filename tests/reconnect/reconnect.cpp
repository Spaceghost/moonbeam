#include <QGuiApplication>
#include <QQmlEngine>
#include <QQmlContext>
#include <QQmlComponent>
#include <QQuickWindow>
#include <QTest>
#include <QTimer>
#include <QDateTime>
#include "../../app/streaming/reconnectpolicy.h"
#include "../../app/streaming/audio/queuebudget.h"

// Execute the real StreamSegue.qml with deterministic transport signals. No
// server, game, input grab, or live network changes are involved.
class FakeSession : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool canReconnect MEMBER allowed)
    Q_PROPERTY(QStringList launchWarnings READ warnings)
public:
    bool allowed = true;
    bool initialized = true;
    int starts = 0;
    int clones = 0;
    FakeSession* next = nullptr;
    QStringList warnings() const { return {}; }
    Q_INVOKABLE bool initialize(QQuickWindow*) { return initialized; }
    Q_INVOKABLE void start() { starts++; }
    Q_INVOKABLE void cancelReconnect() { allowed = false; emit sessionFinished(0); emit readyForDeletion(); }
    Q_INVOKABLE FakeSession* createReconnectSession() {
        clones++;
        next = new FakeSession;
        QQmlEngine::setObjectOwnership(next, QQmlEngine::CppOwnership);
        return next;
    }
signals:
    void stageStarting(QString);
    void stageFailed(QString, int, QString);
    void connectionStarted();
    void displayLaunchError(QString);
    void quitStarting();
    void sessionFinished(int);
    void readyForDeletion();
};

class UiStub : public QObject {
    Q_OBJECT
    Q_PROPERTY(bool visible MEMBER visible)
    Q_PROPERTY(QString text MEMBER text)
    Q_PROPERTY(bool quitAfter MEMBER quitAfter)
public:
    bool visible = false, quitAfter = false;
    QString text;
    int pops = 0, opens = 0;
    Q_INVOKABLE void pop() { pops++; }
    Q_INVOKABLE void open() { opens++; }
    Q_INVOKABLE void enable() {}
    Q_INVOKABLE void disable() {}
    Q_INVOKABLE void waitForAsyncLoad() {}
    Q_INVOKABLE int getConnectedGamepads() { return 0; }
};

class ReconnectTest : public QObject {
    Q_OBJECT
    QString source;
public:
    explicit ReconnectTest(QString path) : source(path) {}
private slots:
    void audioQueueBudget() {
        const unsigned stereo = 48000 * 2 * 4;
        QVERIFY(AudioQueueBudget::fits(9 * 1920, 1920, stereo));
        QVERIFY(!AudioQueueBudget::fits(10 * 1920, 1920, stereo));
        QVERIFY(AudioQueueBudget::fits(4 * 3840, 3840, stereo));
        QVERIFY(!AudioQueueBudget::fits(5 * 3840, 3840, stereo));
        QVERIFY(!AudioQueueBudget::fits(stereo / 20 - 1, 2, stereo));
        QVERIFY(AudioQueueBudget::fits(48000 * 8 * 4 / 25, 48000 * 8 * 4 / 100, 48000 * 8 * 4));
        QVERIFY(!AudioQueueBudget::fits(0, 1, 0));
        QVERIFY(!AudioQueueBudget::fits(0, stereo, stereo));
    }
    void terminationPolicy() {
        for (int code : {ML_ERROR_GRACEFUL_TERMINATION, ML_ERROR_PROTECTED_CONTENT,
                         ML_ERROR_FRAME_CONVERSION, ML_ERROR_UNEXPECTED_EARLY_TERMINATION})
            QVERIFY(!ReconnectPolicy::canRetryTermination(code));
        for (int code : {-1, 11, ML_ERROR_NO_VIDEO_TRAFFIC, ML_ERROR_NO_VIDEO_FRAME})
            QVERIFY(ReconnectPolicy::canRetryTermination(code));
    }
    void lifecycle_data() {
        QTest::addColumn<QString>("scenario");
        for (auto name : {"recover", "cancel-wait", "cancel-cleanup", "cancel-connecting",
                          "limit", "intentional", "stable-reset", "retry-failure"})
            QTest::newRow(name) << QString(name);
    }
    void lifecycle() {
        QFETCH(QString, scenario);
        QQmlEngine engine;
        QQuickWindow window;
        UiStub stack, dialog, toolbar;
        FakeSession original;
        engine.rootContext()->setContextProperty("window", &window);
        engine.rootContext()->setContextProperty("stackView", &stack);
        engine.rootContext()->setContextProperty("streamSegueErrorDialog", &dialog);
        engine.rootContext()->setContextProperty("toolBar", &toolbar);
        QQmlComponent component(&engine, QUrl::fromLocalFile(source));
        QVERIFY2(component.isReady(), qPrintable(component.errorString()));
        QScopedPointer<QObject> item(component.create());
        QVERIFY2(item, qPrintable(component.errorString()));
        item->setProperty("session", QVariant::fromValue(&original));
        item->setProperty("appName", "Test game");
        QVERIFY(QMetaObject::invokeMethod(item.data(), "hookSession"));
        if (scenario == "limit") item->setProperty("retryAttempts", 12);
        if (scenario == "intentional") original.allowed = false;
        if (scenario == "stable-reset") {
            item->setProperty("retryAttempts", 12);
            item->setProperty("connectedAt", QDateTime::currentMSecsSinceEpoch() - 31000.0);
        }
        dialog.text = scenario == "intentional" ? "" : "Network lost";
        emit original.sessionFinished(0);
        if (scenario == "limit" || scenario == "intentional") {
            QCOMPARE(stack.pops, 1);
            QCOMPARE(dialog.opens, scenario == "limit" ? 1 : 0);
            emit original.readyForDeletion();
            QCOMPARE(original.clones, 0);
            return;
        }
        QCOMPARE(stack.pops, 0);
        QVERIFY(item->property("retryPending").toBool());
        QCOMPARE(original.clones, 0); // Never start before old transport teardown.
        QCOMPARE(item->property("retryAttempts").toInt(), 1);
        if (scenario == "cancel-cleanup") {
            QVERIFY(QMetaObject::invokeMethod(item.data(), "cancelReconnect"));
            emit original.readyForDeletion();
            QCOMPARE(original.clones, 0);
            QCOMPARE(stack.pops, 1);
            return;
        }
        emit original.readyForDeletion();
        QCOMPARE(original.clones, 1);
        QScopedPointer<FakeSession> next(original.next);
        auto timer = item->findChild<QObject*>("reconnectTimer");
        QVERIFY(timer);
        if (scenario == "cancel-wait") {
            QVERIFY(QMetaObject::invokeMethod(item.data(), "cancelReconnect"));
            QTest::qWait(20);
            QCOMPARE(next->starts, 0);
            QCOMPARE(stack.pops, 1);
            return;
        }
        timer->setProperty("interval", 1);
        QTRY_COMPARE(next->starts, 1);
        QVERIFY(dialog.text.isEmpty());
        if (scenario == "cancel-connecting") {
            QVERIFY(QMetaObject::invokeMethod(item.data(), "cancelReconnect"));
            QCOMPARE(stack.pops, 1);
            QCOMPARE(dialog.opens, 0);
            return;
        }
        if (scenario == "retry-failure") {
            dialog.text = "Host unreachable";
            emit next->sessionFinished(0);
            QCOMPARE(item->property("retryAttempts").toInt(), 2);
            QCOMPARE(stack.pops, 0);
            // Cancel before cleanup so we don't create another fake object.
            QVERIFY(QMetaObject::invokeMethod(item.data(), "cancelReconnect"));
            emit next->readyForDeletion();
            QCOMPARE(stack.pops, 1);
            return;
        }
        emit next->connectionStarted();
        QVERIFY(!window.isVisible());
        QVERIFY(!item->property("retryConnecting").toBool());
        next->allowed = false; // User intentionally disconnects recovered stream.
        emit next->sessionFinished(0);
        emit next->readyForDeletion();
        QCOMPARE(stack.pops, 1);
        QCOMPARE(dialog.opens, 0);
    }
};

int main(int argc, char** argv) {
    QGuiApplication app(argc, argv);
    qmlRegisterType<FakeSession>("Session", 1, 0, "Session");
    qmlRegisterSingletonType<UiStub>("SdlGamepadKeyNavigation", 1, 0, "SdlGamepadKeyNavigation",
        [](QQmlEngine*, QJSEngine*) -> QObject* { return new UiStub; });
    qmlRegisterSingletonType<UiStub>("SystemProperties", 1, 0, "SystemProperties",
        [](QQmlEngine*, QJSEngine*) -> QObject* { return new UiStub; });
    ReconnectTest test(qEnvironmentVariable("STREAM_SEGUE_SOURCE"));
    return QTest::qExec(&test, argc, argv);
}
#include "reconnect.moc"
