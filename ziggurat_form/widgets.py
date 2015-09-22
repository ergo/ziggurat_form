import webhelpers2.html.tags as tags
from ziggurat_form.exceptions import FormInvalid

class BaseWidget(object):

    def __init__(self, validators=None, *args, **kwargs):
        self.label = None
        self.args = args
        self.kwargs = kwargs
        self.field = None
        self.form = None
        self.validators = validators or []

    def validate(self):
        """
        Return all messages returned by validators, if validator returns True then it is considered to pass
        """
        widget_errors = []
        for validator in self.validators:
            try:
                validator(self.field, self.form)
            except FormInvalid as exc:
                widget_errors.append(exc.message)

        return widget_errors

    @property
    def required(self):
        return self.field.required or len(self.validators) > 0

    def update_values(self, field, form):
        if self.field is None:
            self.field = field
        if self.form is None:
            self.form = form
        if self.label is None:
            self.label = self.field.title or self.field.name.replace('_', ' ').capitalize()

    @property
    def errors(self):
        return self.form.errors.get(self.field.name, [])

    def __call__(self, *args, **kwargs):
        val = ''
        if self.form.data and self.field.name in self.form.data:
            val = self.form.data[self.field.name]
        elif self.form.untrusted_data and self.field.name in self.form.untrusted_data:
            val = self.form.untrusted_data[self.field.name]

        return tags.text(self.field.name, val, *args, **kwargs)
