#include <QWidget>
#include <QVBoxLayout>
#include <QString>
#include <QStringList>
#include <KPluginFactory>
#include <KPluginMetaData>
#include <KParts/ReadOnlyPart>
#include <kde_terminal_interface.h>
#include <cstdlib>
#include <unordered_map>
#include <QObject>

static std::unordered_map<QWidget*, TerminalInterface*> g_ifaces;

static void register_iface(QWidget* widget, TerminalInterface* iface) {
    if (!widget || !iface) {
        return;
    }
    g_ifaces[widget] = iface;
    QObject::connect(widget, &QObject::destroyed, [widget]() {
        g_ifaces.erase(widget);
    });
}

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

    QWidget* widget = result.plugin->widget();
    if (parent) {
        auto layout = new QVBoxLayout(parent);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->addWidget(widget);
        parent->setLayout(layout);
    }

    TerminalInterface* iface = qobject_cast<TerminalInterface*>(result.plugin);
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
        register_iface(widget, iface);
    }

    return widget;
}

extern "C" QWidget* createKonsoleShellWidget(const char* shell,
                                              QWidget* parent = nullptr) {
    auto result = KPluginFactory::instantiatePlugin<KParts::ReadOnlyPart>(
        KPluginMetaData(QStringLiteral("konsolepart")), parent);
    if (!result.plugin) {
        return nullptr;
    }

    QWidget* widget = result.plugin->widget();
    if (parent) {
        auto layout = new QVBoxLayout(parent);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->addWidget(widget);
        parent->setLayout(layout);
    }

    TerminalInterface* iface = qobject_cast<TerminalInterface*>(result.plugin);
    if (iface) {
        const char* env_shell = shell && shell[0] ? shell : std::getenv("SHELL");
        QString prog = env_shell ? QString::fromUtf8(env_shell)
                                 : QStringLiteral("bash");
        iface->startProgram(prog, QStringList());
        register_iface(widget, iface);
    }

    return widget;
}

extern "C" void sendInputToWidget(QWidget* widget, const char* input) {
    auto it = g_ifaces.find(widget);
    if (it == g_ifaces.end() || !it->second || !input) {
        return;
    }
    it->second->sendInput(QString::fromUtf8(input));
    it->second->sendInput(QStringLiteral("\n"));
}
