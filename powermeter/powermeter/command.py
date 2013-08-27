# coding: utf-8

class Command(object):
    def __init__(self, option=None, valid_options=None):
        if valid_options and option is None:
            raise ValueError("Missing 'option' argument")

        if option not in valid_options:
            raise ValueError("Invalid option '%s'" % option)

        self.option = option

    @staticmethod
    def check_args(current_args, args):
        for arg in current_args:
            if arg not in args:
                raise ValueError("Missing '%s' argument" % arg)
