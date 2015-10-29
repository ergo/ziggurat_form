import copy
import logging

import colander
import webhelpers2.html.tags as tags
from ziggurat_form.exceptions import FormInvalid

log = logging.getLogger(__name__)


def while_parent(widget, path):
    if widget.position is not None:
        path.append(str(widget.position))
    else:
        path.append(widget.name)
    if widget.parent_widget and not isinstance(widget.parent_widget, FormWidget):
        while_parent(widget.parent_widget, path)
    return path


class DummyNode(object):
    def __init__(self, name, widget=None):
        self.name = name
        self.widget = widget


class BaseWidget(object):
    _marker_type = None

    def __init__(self, custom_label=None, validators=None,
                 blank_widget_data=False, *args, **kwargs):
        self.cloned = False
        self.custom_label = custom_label
        self.args = args
        self.kwargs = kwargs
        self.form = None
        self.validators = validators or []
        self.position = None
        self.node = None
        self.parent_widget = None
        self.required = False
        self.blank_widget_data = blank_widget_data

    @property
    def name(self):
        return self.node.name or ''

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

    def coerce(self):
        pass

    def validate(self):
        """
        Return all messages returned by validators, if validator returns True
        then it is considered to pass
        """
        errors = []
        for validator in self.validators:
            try:
                validator(self)
            except FormInvalid as exc:
                errors.append(exc.message)

        self.form.widget_errors[self.error_path] = errors
        return len(errors) == 0

    @property
    def children(self):
        return None

    # @property
    # def required(self):
    #     return self.field.required or len(self.validators) > 0

    @property
    def label(self):
        return self.custom_label \
               or self.node.name.replace('_', ' ').capitalize()

    @property
    def error_path(self):
        path = '.'.join(reversed(while_parent(self, [])))
        if path.startswith('.'):
            return path[1:]
        return path

    @property
    def schema_errors(self):
        errors = self.form.schema_errors.get(self.error_path)
        if errors:
            return [errors]
        return []

    @property
    def widget_errors(self):
        errors = self.form.widget_errors.get(self.error_path)
        return errors or []

    @property
    def errors(self):
        return self.widget_errors + self.schema_errors

    def __call__(self, *args, **kwargs):
        return '<{}>'.format(self.name)

    @property
    def marker_start(self):
        if self._marker_type is not None:
            return tags.hidden(
                '__start__',
                '{}:{}'.format(self.name, self._marker_type),
                id=None)
        return ''

    @property
    def marker_end(self):
        if self._marker_type is not None:
            return tags.hidden(
                '__end__', '{}:{}'.format(self.name, self._marker_type),
                id=None)
        return ''

    @property
    def data(self):
        p_widget = self.parent_widget
        parent_is_mapping = isinstance(p_widget, MappingWidget)

        if not p_widget:
            return

        data = p_widget.data

        if self.position is not None:
            if data and len(data) > self.position:
                return data[self.position]
        elif parent_is_mapping:
            if data and hasattr(data, 'get'):
                return data.get(self.name)
            elif data:
                return data
        else:
            log.error('something went wrong with field {}'.format(self.name))

    @property
    def coerced_data(self):
        p_widget = self.parent_widget
        parent_is_mapping = isinstance(p_widget, MappingWidget)

        if not p_widget:
            return

        data = p_widget.coerced_data

        if self.position is not None:
            if data and len(data) > self.position:
                return data[self.position]
        elif parent_is_mapping:
            if data and hasattr(data, 'get'):
                return data.get(self.name)
        else:
            log.error('something went wrong with field {}'.format(self.name))


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
        self.non_coerced_data = {}

    def __call__(self, *args, **kwargs):
        return ''

    @property
    def data(self):
        return self.non_coerced_data

    @property
    def coerced_data(self):
        return self.coerced_data_holder


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
        to_create = len(self.data or [1])
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
        if val is colander.null or self.blank_widget_data:
            val = ''
        return tags.text(self.name, val, *args, **kwargs)


class TextAreaWidget(BaseWidget):
    def __call__(self, *args, **kwargs):
        val = self.data
        if val is colander.null or self.blank_widget_data:
            val = ''
        return tags.textarea(self.name, val, *args, **kwargs)


class PasswordWidget(BaseWidget):
    def __call__(self, *args, **kwargs):
        val = self.data
        if val is colander.null or self.blank_widget_data:
            val = ''
        return tags.password(self.name, val, *args, **kwargs)


class CheckboxWidget(BaseWidget):
    def __call__(self, *args, **kwargs):
        val = self.data
        checked = True
        if val is colander.null or not val or self.blank_widget_data:
            checked = False
        return tags.hidden(self.name, '', *args, **kwargs) \
               + tags.checkbox(self.name, u'1', checked, *args, **kwargs)


class HiddenWidget(BaseWidget):

    @property
    def label(self):
        return ''

    def __call__(self, *args, **kwargs):
        val = self.data
        if val is colander.null or self.blank_widget_data:
            val = ''
        return tags.hidden(self.name, val, *args, **kwargs)


class SelectWidget(BaseWidget):

    def convert(self, values):
        return [tags.Option(*reversed(option))
                for option in values]

    def get_options(self, values):
        options = []
        if hasattr(values, 'items'):
            for group, option in values.items():
                options.append(
                    tags.OptGroup(
                        group, self.convert(option)
                    )
                )
        else:
            options = self.convert(values)
        return options

    def __call__(self, values, *args, **kwargs):
        val = self.data
        if val is colander.null or self.blank_widget_data:
            val = ''
        kwargs['options'] = self.get_options(values)
        return tags.select(self.name, val, *args, **kwargs)


def confirm_validator(field):
    confirm_data = field.data
    original_data = field.parent_widget.data.get(field.name[:-8])
    if confirm_data != original_data:
        raise FormInvalid("Confirm field does not match")
    return True


class ConfirmWidget(MappingWidget):
    _marker_type = 'mapping'

    def __init__(self, widget_to_confirm, blank_confirm_widget=True, *args, **kwargs):
        super(ConfirmWidget, self).__init__(*args, **kwargs)
        self.widget_to_confirm = widget_to_confirm
        self.org_node = None
        self.blank_confirm_widget = blank_confirm_widget

    def coerce(self):
        if hasattr(self.coerced_data, 'get'):
            to_replace = self.coerced_data.get(self.name)
        else:
            to_replace = self.coerced_data
        self.parent_widget.coerced_data[self.name] = to_replace

    @property
    def children(self):
        self.widget_to_confirm.node = self.node
        self.widget_to_confirm.form = self.form
        self.widget_to_confirm.parent_widget = self

        confirm_node = self.widget_to_confirm.clone()
        confirm_node.blank_widget_data = self.blank_confirm_widget
        confirm_node.node = DummyNode(self.node.name + '_confirm')
        confirm_node.validators = [confirm_validator]

        snodes = [
            self.widget_to_confirm,
            confirm_node
        ]
        return snodes
