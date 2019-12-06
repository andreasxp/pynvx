"""`ctypes`-compatible enumeration class.
Adapted from https://code.activestate.com/recipes/576415/
"""
from ctypes import c_int


class EnumerationType(type(c_int)):
    """Metatype for all ctype enumerations.

    See also
    --------
    CEnum : actual ctypes enum
    """
    def __new__(metacls, name, bases, dict):
        if not "_members_" in dict:
            _members_ = {}
            for key, value in dict.items():
                if not key.startswith("_"):
                    _members_[key] = value

            dict["_members_"] = _members_
        else:
            _members_ = dict["_members_"]

        dict["_reverse_map_"] = { v: k for k, v in _members_.items() }
        cls = type(c_int).__new__(metacls, name, bases, dict)
        for key, value in cls._members_.items():
            globals()[key] = value
        return cls

    def __repr__(self):
        return "<Enumeration %s>" % self.__name__


class CEnum(c_int, metaclass=EnumerationType):
    """A ctypes enumeration type.
    This enumeration is less customizable compared to its C equivalent: it always uses c_int as its underlying type.
    """
    _members_ = {}

    def __repr__(self):
        value = self.value
        return "<%s.%s: %d>" % (
            self.__class__.__name__,
            self._reverse_map_.get(value, '(unknown)'),
            value
        )

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other

        return type(self) == type(other) and self.value == other.value
