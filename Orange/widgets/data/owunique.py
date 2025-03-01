from operator import itemgetter

import numpy as np

from AnyQt.QtCore import Qt

from Orange.data import Table
from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.itemmodels import DomainModel
from Orange.widgets.utils.widgetpreview import WidgetPreview


class OWUnique(widget.OWWidget):
    name = _('Unique')
    icon = 'icons/Unique.svg'
    description = _('Filter instances unique by specified key attribute(s).')

    class Inputs:
        data = widget.Input("Data", Table)

    class Outputs:
        data = widget.Output("Data", Table)

    want_main_area = False

    TIEBREAKERS = {_('Last instance'): itemgetter(-1),
                   _('First instance'): itemgetter(0),
                   _('Middle instance'): lambda seq: seq[len(seq) // 2],
                   _('Random instance'): np.random.choice,
                   _('Discard non-unique instances'):
                   lambda seq: seq[0] if len(seq) == 1 else None}

    settingsHandler = settings.DomainContextHandler()
    selected_vars = settings.ContextSetting([])
    tiebreaker = settings.Setting(next(iter(TIEBREAKERS)))
    autocommit = settings.Setting(True)

    def __init__(self):
        # Commit is thunked because autocommit redefines it
        # pylint: disable=unnecessary-lambda
        super().__init__()
        self.data = None

        self.var_model = DomainModel(parent=self, order=DomainModel.MIXED)
        var_list = gui.listView(
            self.controlArea, self, "selected_vars", box=_("Group by"),
            model=self.var_model, callback=lambda: self.commit())
        var_list.setSelectionMode(var_list.ExtendedSelection)

        gui.comboBox(
            self.controlArea, self, 'tiebreaker', box=True,
            label=_('Instance to select in each group:'),
            items=tuple(self.TIEBREAKERS),
            callback=lambda: self.commit(), sendSelectedValue=True)
        gui.auto_commit(
            self.controlArea, self, 'autocommit', 'Commit',
            orientation=Qt.Horizontal)

    @Inputs.data
    def set_data(self, data):
        self.closeContext()
        self.data = data
        self.selected_vars = []
        if data:
            self.var_model.set_domain(data.domain)
            self.selected_vars = self.var_model[:]
            self.openContext(data.domain)
        else:
            self.var_model.set_domain(None)

        self.unconditional_commit()

    def commit(self):
        if self.data is None:
            self.Outputs.data.send(None)
        else:
            self.Outputs.data.send(self._compute_unique_data())

    def _compute_unique_data(self):
        uniques = {}
        keys = zip(*[self.data.get_column_view(attr)[0]
                     for attr in self.selected_vars or self.var_model])
        for i, key in enumerate(keys):
            uniques.setdefault(key, []).append(i)

        choose = self.TIEBREAKERS[self.tiebreaker]
        selection = sorted(
            x for x in (choose(inds) for inds in uniques.values())
            if x is not None)
        if selection:
            return self.data[selection]
        else:
            return None


if __name__ == "__main__":  # pragma: no cover
    WidgetPreview(OWUnique).run(Table("iris"))
