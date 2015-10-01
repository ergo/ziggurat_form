import copy
import colander
import peppercorn
import weakref
import types
import pprint

from ziggurat_form.widgets import MappingWidget, PositionalWidget, TextWidget, FormWidget, TupleWidget


class ZigguratForm(object):
    def __init__(self, schema_cls, bind_values=None, after_bind_callback=None):
        self.schema_cls = schema_cls
        self.untrusted_data = None
        self.deserialized_data = None
        self.bind_values = bind_values
        self.after_bind_callback = after_bind_callback
        self.valid = None
        self.schema_instance = self.schema_cls(after_bind=self.after_bind_callback)
        if self.bind_values:
            self.schema_instance = self.schema_instance.bind(**self.bind_values)
        self.set_nodes()
        self.schema_errors = {}

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
        self.schema_instance.widget = FormWidget()
        self.schema_instance.widget.node = weakref.proxy(self.schema_instance)
        self.schema_instance.widget.form = weakref.proxy(self)
        for path in self.paths():
            for i, leaf in enumerate(path):
                if i == 0:
                    continue
                is_mapping = isinstance(leaf.typ, colander.Mapping)
                is_positional = isinstance(leaf.typ, colander.Positional)
                is_tuple = isinstance(leaf.typ, colander.Tuple)
                if is_mapping:
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

        self.widget = self.schema_instance.widget
        self.widget.root_data = self.untrusted_data

    def set_data(self, struct=None, obj=None, **kwargs):
        parsed_data = peppercorn.parse(struct.items())
        if '_ziggurat_form_field_' in parsed_data:
            self.untrusted_data = parsed_data['_ziggurat_form_field_']
        else:
            self.untrusted_data = parsed_data
        self.set_nodes()

        # for field in self.field_names:
        #     if field in struct:
        #         tmp_struct[field] = copy.deepcopy(struct[field])
        #     elif hasattr(obj, field):
        #         tmp_struct[field] = copy.deepcopy(getattr(obj, field))
        #     elif field in kwargs:
        #         tmp_struct[field] = copy.deepcopy(kwargs[field])
        # pprint.pprint(tmp_struct.items())
        # self.untrusted_data = peppercorn.parse(tmp_struct.items())

    def validate(self):
        # colander validation
        self.valid = True
        try:
            self.deserialized_data = self.schema_instance.deserialize(
                self.untrusted_data)
        except colander.Invalid as exc:
            self.valid = False
            self.schema_errors = exc.asdict()

        # # custom widget validators
        # for path in self.paths():
        #     leaf = path[-1]
        #     if leaf.widget and leaf.widget.validators:
        #         if not leaf.widget.validate():
        #             self.valid = False

        return self.valid

    def populate_obj(self, obj):
        """
        Populates the attributes of the passed `obj` with data from the
        deserialized colander data.
        """
        for node in self.schema_instance.children:
            setattr(obj, node.name, self.data[node.name])

    def __iter__(self):
        return iter(self.schema_instance.children)
