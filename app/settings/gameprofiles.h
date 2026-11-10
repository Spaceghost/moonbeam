#pragma once
#include <QString>
#include <QVariantMap>

// Profiles contain stream options only; pairing and host credentials stay in their existing store.
namespace GameProfiles {
QVariantMap load(const QString& hostId, int appId);
bool save(const QString& hostId, int appId, const QVariantMap& values);
QStringList keys();
bool valid(const QVariantMap& values);
}
