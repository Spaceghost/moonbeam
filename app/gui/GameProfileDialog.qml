import QtQuick 2.9
import QtQuick.Controls 2.5
import QtQuick.Layouts 1.3
import StreamingPreferences 1.0

NavigableDialog {
    id: editor
    property var profileModel
    property int appIndex: -1
    property string gameName
    property bool hasProfile: false
    property var codecs: [
        {text: qsTr("Automatic"), value: 0}, {text: "H.264", value: 1},
        {text: "HEVC", value: 2}, {text: "AV1", value: 4}]
    property var decoders: [
        {text: qsTr("Automatic"), value: 0}, {text: qsTr("Hardware"), value: 1},
        {text: qsTr("Software"), value: 2}]
    property var rendererCandidates: Qt.platform.os === "linux" ? [
        {text: qsTr("Automatic"), value: 0}, {text: "SDL", value: 4}, {text: "Vulkan", value: 1}
    ] : Qt.platform.os === "osx" ? [
        {text: qsTr("Automatic"), value: 0}, {text: "Vulkan", value: 1},
        {text: "Metal", value: 2}, {text: "AVSampleBufferDisplayLayer", value: 3}
    ] : [{text: qsTr("Automatic"), value: 0}]

    property var renderers: rendererCandidates.filter(function(renderer) {
        return StreamingPreferences.availableRenderers().indexOf(renderer.value) >= 0
    })
    property int selectedRenderer: rendererBox.currentIndex >= 0 ? renderers[rendererBox.currentIndex].value : 0

    title: qsTr("Stream settings — %1").arg(gameName)
    width: Math.min(600, window.width - 32)
    height: Math.min(660, window.height - 32)

    function selected(model, value) {
        for (var i = 0; i < model.length; ++i) if (model[i].value === value) return i
        return 0
    }
    function edit(index, name) {
        appIndex = index
        gameName = name
        var profile = profileModel.getStreamProfile(index)
        hasProfile = Object.keys(profile).length > 0
        function value(key) {
            return profile[key] !== undefined ? profile[key] : StreamingPreferences[key]
        }
        widthBox.value = value("width")
        heightBox.value = value("height")
        fpsBox.value = value("fps")
        bitrateBox.value = value("bitrateKbps")
        codecBox.currentIndex = selected(codecs, value("videoCodecConfig"))
        decoderBox.currentIndex = selected(decoders, value("videoDecoderSelection"))
        rendererBox.currentIndex = selected(renderers, value("rendererSelection"))
        pacingBox.checked = value("framePacing")
        hdrBox.checked = value("enableHdr") && renderers[rendererBox.currentIndex].value !== 4
        errorLabel.text = ""
        open()
    }
    function saveProfile() {
        var values = {
            width: widthBox.value, height: heightBox.value, fps: fpsBox.value,
            bitrateKbps: bitrateBox.value, videoCodecConfig: codecs[codecBox.currentIndex].value,
            videoDecoderSelection: decoders[decoderBox.currentIndex].value,
            rendererSelection: renderers[rendererBox.currentIndex].value,
            framePacing: pacingBox.checked, enableHdr: hdrBox.checked
        }
        if (profileModel.saveStreamProfile(appIndex, values)) close()
        else errorLabel.text = qsTr("Could not save this profile. Check the values and try again.")
    }
    function resetProfile() {
        if (profileModel.saveStreamProfile(appIndex, {})) close()
        else errorLabel.text = qsTr("Could not restore global settings. Try again.")
    }

    contentItem: ScrollView {
        clip: true
        ColumnLayout {
            width: editor.availableWidth
            spacing: 12
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                text: editor.hasProfile ? qsTr("These settings apply only to this game on this PC.") :
                                         qsTr("Using global settings. Save to create a profile for this game on this PC.")
            }
            Label { text: qsTr("Resolution") }
            RowLayout {
                SpinBox { id: widthBox; objectName: "profileWidth"; from: 128; to: 16384; editable: true }
                Label { text: "×" }
                SpinBox { id: heightBox; objectName: "profileHeight"; from: 128; to: 16384; editable: true }
            }
            Label { text: qsTr("Frame rate (FPS)") }
            SpinBox { id: fpsBox; objectName: "profileFps"; from: 10; to: 480; editable: true }
            Label { text: qsTr("Video bitrate (Mbps)") }
            SpinBox {
                id: bitrateBox
                objectName: "profileBitrate"
                from: 500; to: 500000; stepSize: 500; editable: true
                validator: DoubleValidator { bottom: 0.5; top: 500; decimals: 1 }
                textFromValue: function(value, locale) { return Number(value / 1000).toLocaleString(locale, 'f', 1) }
                valueFromText: function(text, locale) { return Math.round(Number.fromLocaleString(locale, text) * 1000) }
            }
            Label { text: qsTr("Video codec") }
            ComboBox { id: codecBox; objectName: "profileCodec"; model: editor.codecs; textRole: "text" }
            Label { text: qsTr("Video decoder") }
            ComboBox { id: decoderBox; objectName: "profileDecoder"; model: editor.decoders; textRole: "text" }
            Label { text: qsTr("Renderer"); visible: editor.renderers.length > 1 }
            ComboBox {
                id: rendererBox
                visible: editor.renderers.length > 1
                objectName: "profileRenderer"
                model: editor.renderers
                textRole: "text"
                onActivated: if (editor.renderers[currentIndex].value === 4) hdrBox.checked = false
            }
            Label {
                Layout.fillWidth: true
                wrapMode: Text.Wrap
                visible: editor.selectedRenderer === 4
                text: qsTr("SDL uses compatibility presentation and does not support HDR. Hardware decoding with SDL is an opt-in option on NVIDIA Wayland.")
            }
            CheckBox { id: pacingBox; objectName: "profilePacing"; text: qsTr("Frame pacing") }
            CheckBox {
                id: hdrBox
                objectName: "profileHdr"
                text: qsTr("HDR")
                enabled: editor.selectedRenderer !== 4
            }
            Label { id: errorLabel; Layout.fillWidth: true; wrapMode: Text.Wrap; visible: text.length > 0 }
        }
    }
    footer: DialogButtonBox {
        standardButtons: DialogButtonBox.Save | DialogButtonBox.Cancel
        Button { text: qsTr("Use global settings"); DialogButtonBox.buttonRole: DialogButtonBox.ResetRole }
        onAccepted: editor.saveProfile()
        onRejected: editor.close()
        onReset: editor.resetProfile()
    }
}
