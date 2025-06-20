#include <QWidget>
#include <QVBoxLayout>
#include <QString>
#include <QStringList>
#include <KPluginFactory>
#include <KPluginMetaData>
#include <KParts/ReadOnlyPart>
#include <kde_terminal_interface.h>

extern "C" QWidget* createKonsoleSshWidget(const char* user,
                                            const char* host,
                                            int port,
                                            const char* key,
                                            const char* initial_cmd,
                                            QWidget* parent = nullptr) {
    auto result = KPluginFactory::instantiatePlugin<KParts::ReadOnlyPart>(
        KPluginMetaData(QStringLiteral("konsolepart")), parent);
    if (!result.plugin) {
        return nullptr;
    }

    KParts::ReadOnlyPart* part = result.plugin.release();
    QWidget* widget = part->widget();
    if (parent) {
        auto layout = new QVBoxLayout(parent);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->addWidget(widget);
        parent->setLayout(layout);
    }

    TerminalInterface* iface = qobject_cast<TerminalInterface*>(part);
    if (iface) {
        QStringList args;
        if (key && key[0]) {
            args << "-i" << QString::fromUtf8(key);
        }
        args << QString::fromUtf8(user) + "@" + QString::fromUtf8(host);
        args << "-p" << QString::number(port);
        iface->startProgram(QStringLiteral("ssh"), args);
        if (initial_cmd && initial_cmd[0]) {
            iface->sendInput(QString::fromUtf8(initial_cmd));
            iface->sendInput(QStringLiteral("\n"));
        }
    }

    return widget;
}
