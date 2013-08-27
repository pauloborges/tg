# coding: utf-8

class bundle(object):
    def __init__(self, **kwargs):
        self.update(kwargs)

    def update(self, kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def __unicode__(self):
        return u"<bundle: " + unicode(repr(self.__dict__)) + u">"

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __repr__(self):
        return unicode(self).encode("utf-8")


class LazyFunction(object):
    def __init__(self, module, name):
        self.module = module
        self.name = name
        self.func = None

    def __call__(self, *args, **kwargs):
        if self.func:
            return self.func(*args, **kwargs)

        self.func =  getattr(self.module, self.name)
        return self.func(*args, **kwargs)

def lazyfunc(module, function):
    return LazyFunction(module, function)


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse'] = reverse
    return type('Enum', (), enums)
