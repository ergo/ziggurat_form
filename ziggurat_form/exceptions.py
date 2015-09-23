class ZigguratFormException(Exception):
    pass


class FormInvalid(ZigguratFormException):

    def __init__(self, message, *args, **kwargs):
        self.message = message
