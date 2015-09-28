import colander
import collections
import copy
import webhelpers2.html.tags as tags

from ziggurat_form.exceptions import FormInvalid


class BaseWidget(object):
    _marker_type = None

    def __init__(self, custom_label=None, validators=None, data=None, *args, **kwargs):
        self.cloned = False
        self.custom_label = None
        self.args = args
        self.kwargs = kwargs
        self.form = None
        self.parent_widget = None
        self.validators = validators or []
        self.widget_errors = []
        self.schema_errors = []
        self.position = None
        self.data = data
        self.node = None

    @property
    def name(self):
        return self.node.name

    def clone(self):
        clone = copy.copy(self)
        clone.cloned = True
        return clone

    def validate(self):
        """
        Return all messages returned by validators, if validator returns True
        then it is considered to pass
        """
        self.widget_errors = []
        for validator in self.validators:
            try:
                validator(self.field, self.form)
            except FormInvalid as exc:
                self.widget_errors.append(exc.message)

        return len(self.widget_errors) == 0

    @property
    def required(self):
        return self.field.required or len(self.validators) > 0

    @property
    def label(self):
        return self.custom_label or self.node.name.replace('_', ' ').capitalize()

    @property
    def errors(self):
        return self.widget_errors + self.schema_errors

    def __call__(self, *args, **kwargs):
        raise Exception('Not implemented')

    @property
    def marker_start(self):
        if self._marker_type:
            return tags.hidden('__start__', '{}:{}'.format(self.field.name or '_ziggurat_form_field_',
                                                           self._marker_type), id=None)
        return ''

    @property
    def marker_end(self):
        if self._marker_type:
            return tags.hidden('__end__', '{}:{}'.format(self.field.name or '_ziggurat_form_field_',
                                                         self._marker_type), id=None)
        return ''

    def get_data_from_parent(self):
        parent_w_is_mapping = isinstance(self.parent_widget, MappingWidget)
        parent_w_is_positional = isinstance(self.parent_widget, PositionalWidget)

        if parent_w_is_positional:
            data = self.parent_widget.get_data_from_parent()
            if data:
                return data[self.position]

        elif parent_w_is_mapping:
            if self.parent_widget.data:
                return self.parent_widget.data[self.name]
            else:
                data = self.parent_widget.get_data_from_parent()
                if data:
                    return data.get(self.name)


class PositionalResultWrapper(object):
    def __init__(self, result):
        self.result = result

    @property
    def children(self):
        return self.result


class MappingWidget(BaseWidget):
    _marker_type = 'mapping'

    def __init__(self, *args, **kwargs):
        super(MappingWidget, self).__init__(*args, **kwargs)
        self.children_widget_dict = collections.OrderedDict()

    @property
    def children(self):
        print(list(self.children_widget_dict.values()))
        return list(self.children_widget_dict.values())

    def __call__(self, *args, **kwargs):
        return ''

    def add_widget(self, widget):
        widget.parent_widget = self
        self.children_widget_dict[widget.name] = widget


class FormWidget(MappingWidget):
    name = "__root__"

    def __call__(self, *args, **kwargs):
        return ''


class PositionalWidget(BaseWidget):
    _marker_type = 'sequence'

    def __init__(self, *args, **kwargs):
        super(PositionalWidget, self).__init__(*args, **kwargs)
        self.children_widgets = []

    def __call__(self, *args, **kwargs):
        return ''

    def add_widget(self, widget):
        widget.parent_widget = self
        self.children_widgets.append(widget)

    @property
    def children(self):
        data = self.get_data_from_parent()
        if not data:
            data = [{}]
        for i, entry in enumerate(data):
            for widget_cls in self.children_widgets:
                cloned = widget_cls.clone()
                cloned.widget.position = i
                yield cloned.widget


class TextWidget(BaseWidget):
    def __call__(self, *args, **kwargs):
        val = self.get_data_from_parent()
        if val is colander.null:
            val = ''
        return tags.text(self.name, val, *args, **kwargs)
