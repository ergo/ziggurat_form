import collections
import copy

import colander
import peppercorn

from ziggurat_form.widgets import BaseWidget


class ZigguratForm(object):
    def __init__(self, schema_cls, bind_values=None, after_bind_callback=None):
        self.schema_cls = schema_cls
        self.data = {}
        self.untrusted_data = {}
        self.schema_instance = (
            self.schema_instance.bind(**bind_values)
            if bind_values else schema_cls(after_bind=after_bind_callback))
        self.valid = None
        self.errors = collections.defaultdict(list)
        self.set_nodes()

    def paths(self):
        """ A generator which returns each path through the exception
        graph.  Each path is represented as a tuple of exception
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
        for node in self.paths():
            widget = node[-1].widget
            if widget is None:
                widget = BaseWidget()
            if widget:
                widget.update_values(node[-1], self)

    @property
    def field_names(self):
        return [n.name for n in self.schema_instance.children]

    def set_data(self, struct=None, obj=None, **kwargs):
        tmp_struct = {}
        for field in self.field_names:
            if field in struct:
                tmp_struct[field] = copy.deepcopy(struct[field])
            elif hasattr(obj, field):
                tmp_struct[field] = copy.deepcopy(getattr(obj, field))
            elif field in kwargs:
                tmp_struct[field] = copy.deepcopy(kwargs[field])
        self.untrusted_data = peppercorn.parse(tmp_struct.items())

    def validate(self):
        # colander validation
        self.errors = {}
        self.valid = True

        try:
            self.schema_instance.deserialize(self.untrusted_data)
        except colander.Invalid as exc:
            self.valid = False
            self.errors.update(exc.asdict())

        # custom widget validators
        for node in self.paths():
            widget = node[-1].widget
            if widget and widget.validators:
                errors = widget.validate()
                if errors:
                    self.errors[node[-1].name].extend(errors)
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

    def __html__(self):
        return self.render()
