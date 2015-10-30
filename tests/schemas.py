import colander
from ziggurat_form.widgets import (
    TextWidget,
    FormInvalid,
    ConfirmWidget,
    PasswordWidget,
)


def username_validator(field):
    if field.data == 'admin':
        return True

    raise FormInvalid('Custom validation message: Needs to be "admin"')


class UserLoginSchema(colander.MappingSchema):
    username = colander.SchemaNode(
        colander.String(), validator=colander.Length(min=3),
        widget=TextWidget(validators=[username_validator]),
        description='Value of "admin" will pass')

    password = colander.SchemaNode(
        colander.String(), validator=colander.Length(min=3),
        widget=PasswordWidget())


class UserRegisterSchema(colander.MappingSchema):
    username = colander.SchemaNode(
        colander.String(), validator=colander.Length(min=3),
        widget=TextWidget(validators=[username_validator]),
        description='Value of "admin" will pass')

    password = colander.SchemaNode(
        colander.String(), validator=colander.Length(min=3),
        widget=ConfirmWidget(PasswordWidget()))

    email = colander.SchemaNode(colander.String(), validator=colander.Email())


class GroupSchema(colander.MappingSchema):
    foo = colander.SchemaNode(
        colander.String(),
        widget=TextWidget()
    )

group_schema = colander.Schema()

schema = colander.Schema()
schema1 = colander.Schema()
schema2 = colander.Schema(name="foo100")
schema3 = colander.Schema()
schema4 = colander.Schema()
schema1.add(schema2)
schema2.add(schema3)
schema3.add(schema4)
schema4.add(GroupSchema())
schema.add(schema1)
group_schema.add(schema)
