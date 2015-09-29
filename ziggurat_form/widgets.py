import colander
import collections
import copy
import webhelpers2.html.tags as tags

from ziggurat_form.exceptions import FormInvalid


class FormField(object):
    def __init__(self, widget_cls, *args, **kwargs):
        self.widget_cls = widget_cls
        self.args = args
        self.kwargs = kwargs

    def produce(self):
        return self.widget_cls(*args, **kwargs)


class BaseWidget(object):
    _marker_type = None

    def __init__(self, custom_label=None, validators=None, data=None, *args, **kwargs):
        self.cloned = False
        self.custom_label = None
        self.args = args
        self.kwargs = kwargs
        self.form = None
        self.validators = validators or []
        self.widget_errors = []
        self.schema_errors = []
        self.position = None
        self.data = data
        self.node = None
        self.parent_widget = None

    @property
    def name(self):
        return self.node.name

    def __str__(self):
        return '<{} {} of {}: p>'.format(
            self.__class__.__name__,
            self.name,
            self.position
        )

    def clone(self):
        clone = copy.deepcopy(self)
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
        return '<{}>'.format(self.name)

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
        p_widget = self.parent_widget
        parent_w_is_mapping = isinstance(p_widget, MappingWidget)
        if not p_widget:
            return
        data = p_widget.get_data_from_parent()

        if self.position:
            if data:
                return data[self.position]
        elif parent_w_is_mapping:
            if data:
                return data.get(self.name)
        else:
            print('wrong', self.name)


class PositionalResultWrapper(BaseWidget):
    def __init__(self, result):
        self.result = result
        self.position = 0

    @property
    def children(self):
        snodes = []

        for it, sw in enumerate(self.result):
            sw.widget.position = it
            for c in sw.children:
                snodes.append(c.widget)
        return snodes



class MappingWidget(BaseWidget):
    _marker_type = 'mapping'

    def __init__(self, *args, **kwargs):
        super(MappingWidget, self).__init__(*args, **kwargs)
        self.subnodes = collections.OrderedDict()

    @property
    def children(self):
        snodes = []
        for item in self.subnodes.values():
            item.parent_widget = self.parent_widget
            snodes.append(item.widget)
        return snodes

    def __call__(self, *args, **kwargs):
        return ''

    def add_as_subnode(self, widget):
        self.subnodes[widget.name] = widget


class FormWidget(MappingWidget):
    name = "__root__"

    def __init__(self, *args, **kwargs):
        super(FormWidget, self).__init__(*args, **kwargs)
        self.data = {}

    def __call__(self, *args, **kwargs):
        return ''

    @property
    def children(self):
        snodes = []
        for item in self.node.children:
            item.widget.parent_widget = self
            snodes.append(item.widget)
        return snodes

    def get_data_from_parent(self):
        return self.data


class PositionalWidget(BaseWidget):
    _marker_type = 'sequence'

    def __init__(self, *args, **kwargs):
        super(PositionalWidget, self).__init__(*args, **kwargs)
        self.child_instances = None

    def __call__(self, *args, **kwargs):
        return ''

    @property
    def children(self):
        if self.child_instances is None:
            self.child_instances = []

            for i in range(1, 5):
                wrapped = PositionalResultWrapper([])
                wrapped.parent_widget = self
                wrapped.position = i
                for i, clone in enumerate(self.node.clone().children):
                    clone.widget.position = i
                    clone.widget.parent_widget = self
                    wrapped.result.append(clone)
                wrapped.node = self.node
                self.child_instances.append(wrapped)

        print(self.child_instances)
        return self.child_instances


class TextWidget(BaseWidget):
    def __call__(self, *args, **kwargs):
        val = self.get_data_from_parent()
        if val is colander.null:
            val = ''
        return tags.text(self.name, val, *args, **kwargs)
