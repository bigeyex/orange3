from AnyQt.QtWidgets import QFrame

from Orange.data import Table
from Orange.preprocess.remove import Remove
from Orange.widgets import gui, widget
from Orange.widgets.settings import Setting
from Orange.widgets.utils.sql import check_sql_input
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import Input, Output


class OWPurgeDomain(widget.OWWidget):
    name = _("Purge Domain")
    description = _("Remove redundant values and features from the dataset. " \
                  "Sort values.")
    icon = "icons/PurgeDomain.svg"
    category = "Data"
    keywords = ["remove", "delete", "unused"]

    class Inputs:
        data = Input("Data", Table)

    class Outputs:
        data = Output("Data", Table)

    removeValues = Setting(1)
    removeAttributes = Setting(1)
    removeClasses = Setting(1)
    removeClassAttribute = Setting(1)
    removeMetaAttributeValues = Setting(1)
    removeMetaAttributes = Setting(1)
    autoSend = Setting(True)
    sortValues = Setting(True)
    sortClasses = Setting(True)

    want_main_area = False
    resizing_enabled = False

    feature_options = (('sortValues', _('Sort categorical feature values')),
                       ('removeValues', _('Remove unused feature values')),
                       ('removeAttributes', _('Remove constant features')))

    class_options = (('sortClasses', _('Sort categorical class values')),
                     ('removeClasses', _('Remove unused class variable values')),
                     ('removeClassAttribute', _('Remove constant class variables')))

    meta_options = (('removeMetaAttributeValues', _('Remove unused meta attribute values')),
                    ('removeMetaAttributes', _('Remove constant meta attributes')))

    stat_labels = ((_('Sorted features'), 'resortedAttrs'),
                   (_('Reduced features'), 'reducedAttrs'),
                   (_('Removed features'), 'removedAttrs'),
                   (_('Sorted classes'), 'resortedClasses'),
                   (_('Reduced classes'), 'reducedClasses'),
                   (_('Removed classes'), 'removedClasses'),
                   (_('Reduced metas'), 'reducedMetas'),
                   (_('Removed metas'), 'removedMetas'))

    def __init__(self):
        super().__init__()
        self.data = None

        self.removedAttrs = "-"
        self.reducedAttrs = "-"
        self.resortedAttrs = "-"
        self.removedClasses = "-"
        self.reducedClasses = "-"
        self.resortedClasses = "-"
        self.removedMetas = "-"
        self.reducedMetas = "-"

        def add_line(parent):
            frame = QFrame()
            frame.setFrameShape(QFrame.HLine)
            frame.setFrameShadow(QFrame.Sunken)
            parent.layout().addWidget(frame)

        boxAt = gui.vBox(self.controlArea, _("Features"))
        for value, label in self.feature_options:
            gui.checkBox(boxAt, self, value, label,
                         callback=self.optionsChanged)
        add_line(boxAt)
        gui.label(boxAt, self,
                  _("Sorted: %(resortedAttrs)s, "
                  "reduced: %(reducedAttrs)s, removed: %(removedAttrs)s"))

        boxAt = gui.vBox(self.controlArea, "Classes")
        for value, label in self.class_options:
            gui.checkBox(boxAt, self, value, label,
                         callback=self.optionsChanged)
        add_line(boxAt)
        gui.label(boxAt, self,
                  _("Sorted: %(resortedClasses)s,"
                  "reduced: %(reducedClasses)s, removed: %(removedClasses)s"))

        boxAt = gui.vBox(self.controlArea, "Meta attributes")
        for value, label in self.meta_options:
            gui.checkBox(boxAt, self, value, label,
                         callback=self.optionsChanged)
        add_line(boxAt)
        gui.label(boxAt, self,
                  _("Reduced: %(reducedMetas)s, removed: %(removedMetas)s"))

        gui.auto_send(self.buttonsArea, self, "autoSend")

    @Inputs.data
    @check_sql_input
    def setData(self, dataset):
        if dataset is not None:
            self.data = dataset
            self.unconditional_commit()
        else:
            self.removedAttrs = "-"
            self.reducedAttrs = "-"
            self.resortedAttrs = "-"
            self.removedClasses = "-"
            self.reducedClasses = "-"
            self.resortedClasses = "-"
            self.removedMetas = "-"
            self.reducedMetas = "-"
            self.Outputs.data.send(None)
            self.data = None

    def optionsChanged(self):
        self.commit()

    def commit(self):
        if self.data is None:
            return

        attr_flags = sum([Remove.SortValues * self.sortValues,
                          Remove.RemoveConstant * self.removeAttributes,
                          Remove.RemoveUnusedValues * self.removeValues])
        class_flags = sum([Remove.SortValues * self.sortClasses,
                           Remove.RemoveConstant * self.removeClassAttribute,
                           Remove.RemoveUnusedValues * self.removeClasses])
        meta_flags = sum([Remove.RemoveConstant * self.removeMetaAttributes,
                          Remove.RemoveUnusedValues * self.removeMetaAttributeValues])
        remover = Remove(attr_flags, class_flags, meta_flags)
        cleaned = remover(self.data)
        attr_res, class_res, meta_res = \
            remover.attr_results, remover.class_results, remover.meta_results

        self.removedAttrs = attr_res['removed']
        self.reducedAttrs = attr_res['reduced']
        self.resortedAttrs = attr_res['sorted']

        self.removedClasses = class_res['removed']
        self.reducedClasses = class_res['reduced']
        self.resortedClasses = class_res['sorted']

        self.removedMetas = meta_res['removed']
        self.reducedMetas = meta_res['reduced']

        self.Outputs.data.send(cleaned)

    def send_report(self):
        def list_opts(opts):
            return "; ".join(label.lower()
                             for value, label in opts
                             if getattr(self, value)) or "no changes"

        self.report_items(_("Settings"), (
            (_("Features"), list_opts(self.feature_options)),
            (_("Classes"), list_opts(self.class_options)),
            (_("Metas"), list_opts(self.meta_options))))
        if self.data:
            self.report_items("Statistics", (
                (label, getattr(self, value))
                for label, value in self.stat_labels
            ))


if __name__ == "__main__":  # pragma: no cover
    data = Table.from_url("https://datasets.biolab.si/core/car.tab")
    subset = [inst for inst in data if inst["buying"] == "v-high"]
    subset = Table(data.domain, subset)
    # The "buying" should be removed and the class "y" reduced
    WidgetPreview(OWPurgeDomain).run(subset)
