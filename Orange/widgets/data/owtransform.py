from typing import Optional

from Orange.data import Table
from Orange.widgets import gui
from Orange.widgets.report.report import describe_data
from Orange.widgets.utils.sql import check_sql_input
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import OWWidget, Input, Output, Msg


class OWTransform(OWWidget):
    name = _("Apply Domain")
    description = _("Applies template domain on data table.")
    icon = "icons/Transform.svg"
    priority = 2110
    keywords = ["transform"]

    class Inputs:
        data = Input("Data", Table, default=True)
        template_data = Input("Template Data", Table)

    class Outputs:
        transformed_data = Output("Transformed Data", Table)

    class Error(OWWidget.Error):
        error = Msg(_("An error occurred while transforming data.\n{}"))

    resizing_enabled = False
    want_main_area = False
    buttons_area_orientation = None

    def __init__(self):
        super().__init__()
        self.data = None  # type: Optional[Table]
        self.template_data = None  # type: Optional[Table]
        self.transformed_info = describe_data(None)  # type: OrderedDict

        info_box = gui.widgetBox(self.controlArea, _("Info"))
        self.input_label = gui.widgetLabel(info_box, "")
        self.template_label = gui.widgetLabel(info_box, "")
        self.output_label = gui.widgetLabel(info_box, "")
        self.set_input_label_text()
        self.set_template_label_text()

    def set_input_label_text(self):
        text = _("No data on input.")
        if self.data:
            text = _("Input data with {:,} instances and {:,} features.").format(
                len(self.data),
                len(self.data.domain.attributes))
        self.input_label.setText(text)

    def set_template_label_text(self):
        text = _("No template data on input.")
        if self.data and self.template_data:
            text = _("Template domain applied.")
        elif self.template_data:
            text = _("Template data includes {:,} features.").format(
                len(self.template_data.domain.attributes))
        self.template_label.setText(text)

    def set_output_label_text(self, data):
        text = ""
        if data:
            text = _("Output data includes {:,} features.").format(
                len(data.domain.attributes))
        self.output_label.setText(text)

    @Inputs.data
    @check_sql_input
    def set_data(self, data):
        self.data = data
        self.set_input_label_text()

    @Inputs.template_data
    @check_sql_input
    def set_template_data(self, data):
        self.template_data = data

    def handleNewSignals(self):
        self.apply()

    def apply(self):
        self.clear_messages()
        transformed_data = None
        if self.data and self.template_data:
            try:
                transformed_data = self.data.transform(self.template_data.domain)
            except Exception as ex:  # pylint: disable=broad-except
                self.Error.error(ex)

        data = transformed_data
        self.transformed_info = describe_data(data)
        self.Outputs.transformed_data.send(data)
        self.set_template_label_text()
        self.set_output_label_text(data)

    def send_report(self):
        if self.data:
            self.report_data(_("Data"), self.data)
        if self.template_data:
            self.report_domain(_("Template data"), self.template_data.domain)
        if self.transformed_info:
            self.report_items(_("Transformed data"), self.transformed_info)


if __name__ == "__main__":  # pragma: no cover
    from Orange.preprocess import Discretize

    table = Table("iris")
    WidgetPreview(OWTransform).run(
        set_data=table, set_template_data=Discretize()(table))
