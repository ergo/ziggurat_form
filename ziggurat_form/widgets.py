import copy
import webhelpers2.html.tags as tags

from ziggurat_form.exceptions import FormInvalid

class BaseWidget(object):

    _marker_type = None

    def __init__(self, validators=None, cloned=False, *args, **kwargs):
        self.cloned = cloned
        self.label = None
        self.dotted_path = ''
        self.args = args
        self.kwargs = kwargs
        self.field = None
        self.form = None
        self.validators = validators or []
        self.widget_errors = []
        self.schema_errors = []

    def clone(self):
        clone = copy.copy(self)
        clone.cloned = True
        clone.field = None
        clone.form = None
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

    def update_values(self, field, form):
        if self.field is None:
            self.field = field
        if self.form is None:
            self.form = form
        if self.label is None:
            self.label = (
                self.field.title or
                self.field.name.replace('_', ' ').capitalize())

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

class MappingWidget(BaseWidget):

    _marker_type = 'mapping'

    def __call__(self, *args, **kwargs):
        return ''

class PositionalWidget(BaseWidget):

    _marker_type = 'sequence'

    def __call__(self, *args, **kwargs):
        return ''

class TextWidget(BaseWidget):

    def __call__(self, *args, **kwargs):
        val = self.form.flattened_data.get(self.dotted_path)

        return tags.text(self.field.name, val, *args, **kwargs)
