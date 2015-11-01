import pytest
import colander
from ziggurat_form.form import ZigguratForm

from .schemas import group_schema, UserLoginSchema, FieldDefaultsSchema


class ValidationException(Exception):
    pass


class TestValidation(object):

    def validate(self, form):
        if not form.validate():
            raise ValidationException(
                "Not valid form: {}\n{}".format(
                    form.schema_errors, form.widget_errors)
            )

    def test_userlogin_schema(self):
        data = {"username": "admin", "password": "Abcd123!"}
        form = ZigguratForm(UserLoginSchema())
        form.set_data(data)
        self.validate(form)

    def test_bad_userlogin_schema(self):
        data = {"username": "foo", "password": "Abcd123!"}
        form = ZigguratForm(UserLoginSchema())
        form.set_data(data)
        with pytest.raises(ValidationException):
            self.validate(form)

        # widget must have error
        assert any(form.widget_errors.values()) is True

    def test_deep_group_schema(self):
        data = {'':
                {'':
                 {'foo100':
                  {'':
                   {'':
                    {'':
                     {'foo': 'sdfsdf'}
                     }
                    }
                   }
                  }
                 },
                }
        form = ZigguratForm(group_schema)
        form.set_data(data)
        self.validate(form)

    def test_bad_deep_group_schema(self):
        data = {'':
                {'':
                 {'foo100':
                  {'':
                   {'':
                    {'':
                     {'foo': ''}
                     }
                    }
                   }
                  }
                 },
                }
        form = ZigguratForm(group_schema)
        form.set_data(data)
        with pytest.raises(ValidationException):
            self.validate(form)

        # widget must have error
        assert any(form.schema_errors.values()) is True

    def test_missing_value(self):
        data = {
            'music': {
                'artist': 'Alexey Efimov',
                'album': 'Antona Valeka 15',
                'song': 'foo',
                'description': 'foo'
            }
        }
        form = ZigguratForm(FieldDefaultsSchema)
        form.set_data(data)
        assert form.non_validated_data == {
            'title': 'missing title',
            'music': {
                'title': 'missing title',
                'artist': 'Alexey Efimov',
                'album': 'Antona Valeka 15',
                'song': 'foo',
                'description': 'foo'
            }
        }
        self.validate(form)

    def test_default_value(self):
        form = ZigguratForm(FieldDefaultsSchema)
        form.set_data({})
        music = form.widget.children[1]
        assert music.children[0].data == 'Grandaddy'
        assert music.children[1].data == 'Just Like the Fambly Cat'
        assert music.children[2].data == colander.null
