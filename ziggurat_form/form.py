import copy
import weakref

import colander
import peppercorn
from ziggurat_form.widgets import (
    FormWidget,
    TextWidget,
    TupleWidget,
    MappingWidget,
    PositionalWidget
)


class ZigguratForm(object):
    def __init__(self, schema_cls, bind_values=None, after_bind_callback=None):
        self.schema_cls = schema_cls
        self.widget = None
        self._non_coerced_data = None
        self._coerced_data_holder = None
        self.validated_data = None
        self.bind_values = bind_values
        self.after_bind_callback = after_bind_callback
        self.valid = None
        if type(self.schema_cls) is colander._SchemaMeta:
            self.schema_instance = self.schema_cls(
                after_bind=self.after_bind_callback)
        else:  # if it's colander.SchemaNode for example
            self.schema_instance = self.schema_cls
            self.schema_instance.after_bind = self.after_bind_callback
        if self.bind_values:
            self.schema_instance = self.schema_instance.bind(
                **self.bind_values)
        self.set_nodes()
        self.schema_errors = {}
        self.widget_errors = {}

    def paths(self):
        """ A generator which returns each path through the node
        graph.  Each path is represented as a tuple of schema
        nodes.  Within each tuple, the leftmost item will represent
        the root schema node, the rightmost item will represent the
        leaf schema node."""

        def traverse(node, stack):
            stack.append(node)

            if not node.children:
                yield tuple(stack)

            for child in node.children:
                for path in traverse(child, stack):
                    yield path

            stack.pop()

        return traverse(self.schema_instance, [])

    def set_nodes(self):
        """ Creates links between widgets and schema nodes """
        self.schema_instance.widget = FormWidget()
        self.schema_instance.widget.node = weakref.proxy(self.schema_instance)
        self.schema_instance.widget.form = weakref.proxy(self)
        self.schema_instance.widget.non_coerced_data = self._non_coerced_data
        self.schema_instance.widget.coerced_data_holder = self._coerced_data_holder
        self.widget = self.schema_instance.widget

        for path in self.paths():
            for i, leaf in enumerate(path):
                if i == 0:
                    continue
                is_mapping = isinstance(leaf.typ, colander.Mapping)
                is_positional = isinstance(leaf.typ, colander.Positional)
                is_tuple = isinstance(leaf.typ, colander.Tuple)
                if leaf.widget:
                    widget = leaf.widget.clone()
                elif is_mapping:
                    widget = MappingWidget()
                elif is_tuple:
                    widget = TupleWidget()
                elif is_positional:
                    widget = PositionalWidget()
                else:
                    widget = TextWidget()

                leaf.widget = widget
                leaf.widget.node = leaf
                leaf.widget.form = self

    def set_data(self, struct=None, obj=None, **kwargs):
        """ Sets the data for form """
        parsed_data = peppercorn.parse(struct.items())
        if '_ziggurat_form_field_' in parsed_data:
            self._non_coerced_data = parsed_data['_ziggurat_form_field_']
        else:
            self._non_coerced_data = parsed_data
        self._coerced_data_holder = copy.deepcopy(self._non_coerced_data)
        self.set_nodes()

        def coerce_recursive(widget, form):
            widget.coerce()
            if widget.children:
                for child_widget in widget.children:
                    coerce_recursive(child_widget, form)

        coerce_recursive(self.widget, self)

        # for field in self.field_names:
        #     if field in struct:
        #         tmp_struct[field] = copy.deepcopy(struct[field])
        #     elif hasattr(obj, field):
        #         tmp_struct[field] = copy.deepcopy(getattr(obj, field))
        #     elif field in kwargs:
        #         tmp_struct[field] = copy.deepcopy(kwargs[field])
        # pprint.pprint(tmp_struct.items())
        # self.non_coerced_data = peppercorn.parse(tmp_struct.items())

    @property
    def non_validated_data(self):
        return self._coerced_data_holder

    def validate(self):
        # colander validation
        self.valid = True

        def validate_widget(widget, form):
            print('validating', widget)
            is_valid = widget.validate()
            if is_valid is False:
                print('INVALID')
                form.valid = False
            if widget.children:
                for child_widget in widget.children:
                    is_valid = validate_widget(child_widget, form)
                    if is_valid is False:
                        print('INVALID')
                        form.valid = False
            return is_valid

        validate_widget(self.widget, self)

        try:
            self.validated_data = self.schema_instance.deserialize(self._coerced_data_holder)
        except colander.Invalid as exc:
            self.valid = False
            self.schema_errors = exc.asdict()
        return self.valid

    # def populate_obj(self, obj):
    #     """
    #     Populates the attributes of the passed `obj` with data from the
    #     deserialized colander data.
    #     """
    #     for node in self.schema_instance.children:
    #         setattr(obj, node.name, self.data[node.name])

    def __iter__(self):
        return iter(self.schema_instance.children)
