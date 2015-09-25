import copy
import colander
import peppercorn
import weakref
import pprint

from ziggurat_form.widgets import MappingWidget, PositionalWidget, TextWidget

class ZigguratForm(object):
    def __init__(self, schema_cls, bind_values=None, after_bind_callback=None):
        self.schema_cls = schema_cls
        self.data = {}
        self.untrusted_data = None
        self.flattened_data = {}
        self.schema_instance = schema_cls(after_bind=after_bind_callback)
        if bind_values:
            self.schema_instance = self.schema_instance.bind(**bind_values)
        self.valid = None
        self.set_nodes()

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
        for path in self.paths():
            dotted_path = '.'.join([l.name for l in path])[1:]
            for leaf in path:
                if leaf.widget is None:
                    if isinstance(leaf.typ, colander.Mapping):
                        leaf.widget = MappingWidget()
                    elif isinstance(leaf.typ, colander.Positional):
                        leaf.widget = PositionalWidget()
                    else:
                        leaf.widget = TextWidget()

                leaf.widget = leaf.widget.clone()

                if leaf.widget:
                    leaf.widget.update_values(weakref.proxy(leaf),
                                              weakref.proxy(self))
            if path[-1].widget:
                path[-1].widget.dotted_path = dotted_path


    @property
    def field_names(self):
        return [n.name for n in self.schema_instance.children]

    def set_data(self, struct=None, obj=None, **kwargs):
        parsed_data = peppercorn.parse(struct.items())
        if '_ziggurat_form_field_' in parsed_data:
            self.untrusted_data = parsed_data['_ziggurat_form_field_']
        else:
            self.untrusted_data = parsed_data
        if self.untrusted_data:
            self.flattened_data = self.schema_instance.flatten(self.untrusted_data)
            print(self.flattened_data)
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
            self.schema_instance.deserialize(self.untrusted_data)
        except colander.Invalid as exc:
            self.valid = False
            for path in exc.paths():
                leaf = path[-1]
                if leaf.node.widget:
                    leaf.node.widget.schema_errors = list(leaf.asdict().values())

        # custom widget validators
        for path in self.paths():
            leaf = path[-1]
            if leaf.widget and leaf.widget.validators:
                if not leaf.widget.validate():
                    self.valid = False

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
