#include "gameprofiles.h"
#include <QCryptographicHash>
#include <QSettings>

namespace {
QString group(const QString& hostId, int appId)
{
    return QStringLiteral("gameprofiles/v1/%1/%2")
        .arg(QString::fromLatin1(QCryptographicHash::hash(hostId.toUtf8(), QCryptographicHash::Sha256).toHex()))
        .arg(appId);
}
bool integer(const QVariant& value, int minimum, int maximum)
{
    bool ok = false;
    const double number = value.toDouble(&ok);
    return ok && number >= minimum && number <= maximum && number == int(number);
}
}

QStringList GameProfiles::keys()
{
    return {"width", "height", "fps", "bitrateKbps", "videoCodecConfig",
            "videoDecoderSelection", "rendererSelection", "framePacing", "enableHdr"};
}

bool GameProfiles::valid(const QVariantMap& values)
{
    const auto allowed = keys();
    for (auto it = values.cbegin(); it != values.cend(); ++it) {
        const auto& key = it.key();
        const auto& value = it.value();
        if (!allowed.contains(key)) return false;
        if (key == "width" || key == "height") {
            if (!integer(value, 128, 16384)) return false;
        } else if (key == "fps") {
            if (!integer(value, 10, 480)) return false;
        } else if (key == "bitrateKbps") {
            if (!integer(value, 500, 500000)) return false;
        } else if (key == "videoCodecConfig") {
            if (!integer(value, 0, 4) || value.toInt() == 3) return false;
        } else if (key == "videoDecoderSelection") {
            if (!integer(value, 0, 2)) return false;
        } else if (key == "rendererSelection") {
            if (!integer(value, 0, 4)) return false;
#ifdef Q_OS_LINUX
            if (value.toInt() != 0 && value.toInt() != 1 && value.toInt() != 4) return false;
#elif defined(Q_OS_DARWIN)
            if (value.toInt() == 4) return false;
#else
            if (value.toInt() != 0) return false;
#endif
        } else if (value.userType() != QMetaType::Bool) {
            return false;
        }
    }
    // The SDL presentation path doesn't support HDR. Reject an inconsistent saved profile.
    return !(values.value("rendererSelection").toInt() == 4 && values.value("enableHdr").toBool());
}

QVariantMap GameProfiles::load(const QString& hostId, int appId)
{
    if (hostId.isEmpty() || appId <= 0) return {};
    QSettings settings;
    settings.beginGroup(group(hostId, appId));
    QVariantMap values;
    for (const auto& key : settings.childKeys()) values.insert(key, settings.value(key));
    // INI files store booleans as strings; normalize only the known boolean fields.
    for (const auto& key : {"framePacing", "enableHdr"}) {
        if (values.contains(key)) {
            const auto value = values.value(key).toString();
            if (value != "true" && value != "false") return {};
            values[key] = value == "true";
        }
    }
    return valid(values) ? values : QVariantMap{};
}

bool GameProfiles::save(const QString& hostId, int appId, const QVariantMap& values)
{
    if (hostId.isEmpty() || appId <= 0 || !valid(values)) return false;
    QSettings settings;
    settings.beginGroup(group(hostId, appId));
    settings.remove(QString());
    for (auto it = values.cbegin(); it != values.cend(); ++it) settings.setValue(it.key(), it.value());
    settings.sync();
    return settings.status() == QSettings::NoError;
}
