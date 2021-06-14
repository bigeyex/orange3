from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import (
    QFormLayout, QCheckBox, QLineEdit, QWidget, QVBoxLayout, QLabel
)
from orangecanvas.application.settings import UserSettingsDialog, FormLayout
from orangecanvas.document.usagestatistics import UsageStatistics
from orangecanvas.utils.overlay import NotificationOverlay

from orangewidget.workflow.mainwindow import OWCanvasMainWindow


class OUserSettingsDialog(UserSettingsDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        w = self.widget(0)  # 'General' tab
        layout = w.layout()
        assert isinstance(layout, QFormLayout)
        cb = QCheckBox(_("Automatically check for updates"))
        cb.setAttribute(Qt.WA_LayoutUsesWidgetRect)

        layout.addRow("Updates", cb)
        self.bind(cb, "checked", "startup/check-updates")

        # Reporting Tab
        tab = QWidget()
        self.addTab(tab, _("Reporting"),
                    toolTip="Settings related to reporting")

        form = FormLayout()
        line_edit_mid = QLineEdit()
        self.bind(line_edit_mid, "text", "reporting/machine-id")
        form.addRow("Machine ID:", line_edit_mid)

        box = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        cb1 = QCheckBox(
            _("Share"),
            toolTip=_(
                "Share anonymous usage statistics to improve Orange")
        )
        self.bind(cb1, "checked", "reporting/send-statistics")
        cb1.clicked.connect(UsageStatistics.set_enabled)
        layout.addWidget(cb1)
        box.setLayout(layout)
        form.addRow(_("Anonymous Statistics"), box)
        label = QLabel("<a "
                       "href=\"https://orange.biolab.si/statistics-more-info\">"
                       "More info..."
                       "</a>")
        label.setOpenExternalLinks(True)
        form.addRow(_(""), label)

        tab.setLayout(form)

        # Notifications Tab
        tab = QWidget()
        self.addTab(tab, _("Notifications"),
                    toolTip="Settings related to notifications")

        form = FormLayout()

        box = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        cb = QCheckBox(
            _("Enable notifications"), self,
            toolTip="Pull and display a notification feed."
        )
        self.bind(cb, "checked", "notifications/check-notifications")

        layout.addWidget(cb)
        box.setLayout(layout)
        form.addRow(_("On startup"), box)

        notifs = QWidget(self, objectName="notifications-group")
        notifs.setLayout(QVBoxLayout())
        notifs.layout().setContentsMargins(0, 0, 0, 0)

        cb1 = QCheckBox(_("Announcements"), self,
                        toolTip="Show notifications about Biolab announcements.\n"
                                "This entails events and courses hosted by the developers of "
                                "Orange.")

        cb2 = QCheckBox(_("Blog posts"), self,
                        toolTip="Show notifications about blog posts.\n"
                                "We'll only send you the highlights.")
        cb3 = QCheckBox(_("New features"), self,
                        toolTip="Show notifications about new features in Orange when a new "
                                "version is downloaded and installed,\n"
                                "should the new version entail notable updates.")

        self.bind(cb1, "checked", "notifications/announcements")
        self.bind(cb2, "checked", "notifications/blog")
        self.bind(cb3, "checked", "notifications/new-features")

        notifs.layout().addWidget(cb1)
        notifs.layout().addWidget(cb2)
        notifs.layout().addWidget(cb3)

        form.addRow(_("Show notifications about"), notifs)
        tab.setLayout(form)


class MainWindow(OWCanvasMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notification_overlay = NotificationOverlay(self.scheme_widget)
        self.notification_server = None

    def open_canvas_settings(self):
        # type: () -> None
        """Reimplemented."""
        dlg = OUserSettingsDialog(self, windowTitle=_("Preferences"))
        dlg.show()
        status = dlg.exec()
        if status == 0:
            self.user_preferences_changed_notify_all()

    def set_notification_server(self, notif_server):
        self.notification_server = notif_server

        # populate notification overlay with current notifications
        for notif in self.notification_server.getNotificationQueue():
            self.notification_overlay.addNotification(notif)

        notif_server.newNotification.connect(self.notification_overlay.addNotification)
        notif_server.nextNotification.connect(self.notification_overlay.nextWidget)

    def create_new_window(self):  # type: () -> CanvasMainWindow
        window = super().create_new_window()
        window.set_notification_server(self.notification_server)
        return window
