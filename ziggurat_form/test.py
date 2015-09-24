from ziggurat_form.form import ZigguratForm
from ziggurat_form.test_schemas import UserSchema


data = {'password': 'xx', "phones": [{}], "subperson":{}}

form = ZigguratForm(UserSchema)
form.set_data(data)
form.validate()


def render_field(field):
    print(field.widget.marker_start)
    if field.widget:
        print('label:"{}", req:{}'.format(field.widget.label, field.widget.required))
        if field.widget.errors:
            print('errors:', field.widget.errors)
    if field.children:
        for subfield in field.children:
            render_field(subfield)
    else:
        print(field.widget())
    print(field.widget.marker_end)

for field in form:
    render_field(field)


print('FORM ERRORS:', form.valid)
