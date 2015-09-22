from ziggurat_form.test_schemas import UserSchema
from ziggurat_form.form import ZigguratForm
data = {'password':'x'}

form = ZigguratForm(UserSchema)
form.set_data(data)
form.validate()

def render_field(field):
    print('--------------')
    if field.widget:
        print(field.widget.label)
        if field.widget.errors:
            print(field.widget.errors)
        print(field.widget())
    if field.children:
        print('peppercorn marker START')
        for subfield in field.children:
            render_field(subfield)
        print('peppercorn marker END')

for field in form:
    render_field(field)
