import webhelpers2.html.tags as tags

from ziggurat_form.exceptions import FormInvalid


class BaseWidget(object):

    _marker_type = None

    def __init__(self, validators=None, *args, **kwargs):
        self.label = None
        self.args = args
        self.kwargs = kwargs
        self.field = None
        self.form = None
        self.validators = validators or []
        self.widget_errors = []
        self.schema_errors = []

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
            return tags.hidden('__start__', '{}:{}'.format(self.field.name, self._marker_type), id=None)
        return ''

    @property
    def marker_end(self):
        if self._marker_type:
            return tags.hidden('__end__', '{}:{}'.format(self.field.name, self._marker_type), id=None)
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
        val = ''
        if self.form.data and self.field.name in self.form.data:
            val = self.form.data[self.field.name]
        elif (self.form.untrusted_data and
                      self.field.name in self.form.untrusted_data):
            val = self.form.untrusted_data[self.field.name]

        return tags.text(self.field.name, val, *args, **kwargs)
