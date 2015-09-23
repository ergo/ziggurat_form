from ziggurat_form.form import ZigguratForm
from ziggurat_form.test_schemas import UserSchema


data = {'password': 'x'}

form = ZigguratForm(UserSchema)
form.set_data(data)
form.validate()


def render_field(field):
    print('--------------')
    if field.widget:
        print(
            'label:"{}", req:{}'.format(
                field.widget.label, field.widget.required))
        if field.widget.errors:
            print('errors:', field.widget.errors)
        print(field.widget())
    if field.children:
        print('peppercorn marker START')
        for subfield in field.children:
            render_field(subfield)
        print('peppercorn marker END')

for field in form:
    render_field(field)


print('FORM ERRORS:', form.errors)
