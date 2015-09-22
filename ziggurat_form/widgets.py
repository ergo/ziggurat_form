import webhelpers2.html.tags as tags

class BaseWidget(object):

    def __init__(self, label=None, *args, **kwargs):
        self.label = label
        self.args = args
        self.kwargs = kwargs
        self.field = None
        self.form = None

    def update_values(self, field, form):
        if self.field is None:
            self.field = field
        if self.form is None:
            self.form = form
        if self.label is None:
            self.label = self.field.name.replace('_', ' ').capitalize()

    @property
    def errors(self):
        return self.form.errors.get(self.field.name, '')

    def __call__(self, *args, **kwargs):
        val = ''
        if self.form.data and self.field.name in self.form.data:
            val = self.form.data[self.field.name]
        elif self.form.untrusted_data and self.field.name in self.form.untrusted_data:
            val = self.form.untrusted_data[self.field.name]

        return tags.text(self.field.name, val, *args, **kwargs)
