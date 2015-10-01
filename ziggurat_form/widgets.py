import colander
import logging
import copy
import webhelpers2.html.tags as tags

from ziggurat_form.exceptions import FormInvalid

log = logging.getLogger(__name__)


def while_parent(widget, path):
    if widget.position is not None:
        path.append(str(widget.position))
    else:
        path.append(widget.name)
    if widget.parent_widget and widget.parent_widget.name != '__root__':
        while_parent(widget.parent_widget, path)
    return path


class BaseWidget(object):
    _marker_type = None

    def __init__(self, custom_label=None, validators=None, *args, **kwargs):
        self.cloned = False
        self.custom_label = custom_label
        self.args = args
        self.kwargs = kwargs
        self.form = None
        self.validators = validators or []
        self.widget_errors = []
        self.position = None
        self.node = None
        self.parent_widget = None
        self.required = False

    @property
    def name(self):
        return self.node.name

    def __str__(self):
        return '<{} {} of {}: p: {}>'.format(
            self.__class__.__name__,
            self.name,
            self.parent_widget.name if self.parent_widget else '',
            self.position
        )

    def clone(self):
        clone = copy.copy(self)
        # clone = self.__class__()
        clone.node = self.node
        clone.form = self.form
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
    def children(self):
        return None

    # @property
    # def required(self):
    #     return self.field.required or len(self.validators) > 0

    @property
    def label(self):
        return self.custom_label or self.node.name.replace('_', ' ').capitalize()

    @property
    def schema_errors(self):
        error_path = '.'.join(reversed(while_parent(self, [])))
        errors = self.form.schema_errors.get(error_path)
        if errors:
            return [errors]
        return []

    @property
    def errors(self):
        return self.widget_errors + self.schema_errors

    def __call__(self, *args, **kwargs):
        return '<{}>'.format(self.name)

    @property
    def marker_start(self):
        if self._marker_type is not None:
            return tags.hidden('__start__', '{}:{}'.format(self.name or '_ziggurat_form_field_',
                                                           self._marker_type), id=None)
        return ''

    @property
    def marker_end(self):
        if self._marker_type is not None:
            return tags.hidden('__end__', '{}:{}'.format(self.name or '_ziggurat_form_field_',
                                                         self._marker_type), id=None)
        return ''

    @property
    def data(self):
        p_widget = self.parent_widget
        parent_w_is_mapping = isinstance(p_widget, MappingWidget)

        if not p_widget:
            return

        data = p_widget.data

        if self.position is not None:
            if data and len(data) > self.position:
                return data[self.position]
        elif parent_w_is_mapping:
            if data:
                return data.get(self.name)
        else:
            log.error('something went wrong with field', self.name)


class MappingWidget(BaseWidget):
    _marker_type = 'mapping'

    def __init__(self, *args, **kwargs):
        super(MappingWidget, self).__init__(*args, **kwargs)

    @property
    def children(self):
        snodes = []
        for item in self.node.children:
            cloned = item.clone()
            cloned.widget = cloned.widget.clone()
            cloned.widget.parent_widget = self
            snodes.append(cloned.widget)
        return snodes

    def __call__(self, *args, **kwargs):
        return ''


class FormWidget(MappingWidget):
    _marker_type = None

    name = "__root__"

    def __init__(self, *args, **kwargs):
        super(FormWidget, self).__init__(*args, **kwargs)
        self.root_data = {}

    def __call__(self, *args, **kwargs):
        return ''

    @property
    def data(self):
        return self.root_data


class TupleWidget(BaseWidget):
    _marker_type = 'sequence'

    def __init__(self, *args, **kwargs):
        super(TupleWidget, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return ''

    @property
    def children(self):
        results = []
        for i, item in enumerate(self.node.children):
            cloned = item.clone()
            cloned.widget = cloned.widget.clone()
            cloned.widget.position = i
            cloned.widget.parent_widget = self
            results.append(cloned.widget)

        return results


class PositionalWidget(BaseWidget):
    _marker_type = 'sequence'

    def __init__(self, *args, **kwargs):
        super(PositionalWidget, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        return ''

    @property
    def children(self):
        results = []
        to_create = len(self.data or [])
        for i in range(0, to_create):
            cloned = self.node.children[0].clone()
            cloned.widget = cloned.widget.clone()
            cloned.widget.position = i
            cloned.widget.parent_widget = self
            results.append(cloned.widget)
        return results


class TextWidget(BaseWidget):
    def __call__(self, *args, **kwargs):
        val = self.data
        if val is colander.null:
            val = ''
        return tags.text(self.name, val, *args, **kwargs)
