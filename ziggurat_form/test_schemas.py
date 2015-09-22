import colander
from ziggurat_form.widgets import BaseWidget, FormInvalid
choices = (
    ('', '- Select -'),
    ('habanero', 'Habanero'),
    ('jalapeno', 'Jalapeno'),
    ('chipotle', 'Chipotle')
)


class Friend(colander.TupleSchema):
    rank = colander.SchemaNode(colander.Int(),
                               validator=colander.Range(0, 9999))
    name = colander.SchemaNode(colander.String())

class Phone(colander.MappingSchema):
    location = colander.SchemaNode(colander.String(),
                                   validator=colander.OneOf(['home', 'work']))
    number = colander.SchemaNode(colander.String())

class Friends(colander.SequenceSchema):
    friend = Friend()

class Phones(colander.SequenceSchema):
    phone = Phone()

class Person(colander.MappingSchema):
    name = colander.SchemaNode(colander.String())
    age = colander.SchemaNode(colander.Int(),
                              validator=colander.Range(0, 200))
    friends = Friends()
    phones = Phones()


class AddressSchema(colander.MappingSchema):
    street = colander.SchemaNode(colander.String(),
                                    validator=colander.Length(min=3))
    city = colander.SchemaNode(colander.String(),
                                   validator=colander.Length(min=3))

    person = Friend()


def test_validator(field, form):
    print('validating', field, form)
    raise FormInvalid("Custom validation error")
    return True

class UserSchema(colander.MappingSchema):
    user_name = colander.SchemaNode(colander.String(),
                                    validator=colander.Length(min=3),
                                    widget=BaseWidget())
    password = colander.SchemaNode(colander.String(),
                                   validator=colander.Length(min=3),
                                   title='Lilu Dallas Multipass!',
                                   description="Korben nice!",
                                   zorg='Not nice!',
                                   widget=BaseWidget())
    email = colander.SchemaNode(colander.String(),
                                validator=colander.Length(min=3))

    friend = AddressSchema()

    optional_field = colander.SchemaNode(colander.String(), missing='OK',
                                         widget=BaseWidget(validators=[test_validator]))

