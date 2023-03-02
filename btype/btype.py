# Copyright (c) 2021 by Phase Advanced Sensor Systems, Inc.
import struct
import math


class Field:
    def __init__(self, name, typ):
        self.name = name
        self.typ  = typ


class Type:
    def __init__(self):
        pass

    def __set_name__(self, owner, name):
        super().__setattr__('name', name)

    def __get__(self, obj, objtype=None):
        return obj._fields[self.name]

    def __set__(self, obj, value):
        raise NotImplementedError('Type.__set__() not implemented.')


class NumericType(Type):
    _LOWER_LIMIT = None
    _UPPER_LIMIT = None
    _TYPE        = None

    def __init__(self, default=None):
        super().__init__()
        if default is None:
            default = self._DEFAULT
        self._default = default
        self._validate(self._default)

    @classmethod
    def _validate(cls, v):
        if not isinstance(v, cls._TYPE):  # pylint: disable=W1116
            raise Exception("%s must be type %s (value '%s' is type "
                            "%s)." % (cls.__name__, cls._TYPE, v, type(v)))
        if ((not cls._LOWER_LIMIT <= v <= cls._UPPER_LIMIT) and
                v != float('inf') and v != float('-inf') and
                not math.isnan(v)):
            raise Exception("%s value '%s' is out of range." %
                            (cls.__name__, v))

    def __set__(self, obj, v):
        if isinstance(v, NumericType):
            v = v._make()
        self._validate(v)
        obj._fields[self.name] = v

    def _make(self):
        return self._default

    @classmethod
    def _make_from_array(cls, a):
        cls._validate(a[0])
        return a.pop(0)

    @classmethod
    def _flatten_r(cls, obj, a):
        a.append(obj)

    def _get_struct_format(self):
        return self._FORMAT


class int8_t(NumericType):
    _LOWER_LIMIT = -0x80
    _UPPER_LIMIT = 0x7F
    _FORMAT      = 'b'
    _DEFAULT     = 0
    _TYPE        = int


class uint8_t(NumericType):
    _LOWER_LIMIT = 0
    _UPPER_LIMIT = 0xFF
    _FORMAT      = 'B'
    _DEFAULT     = 0
    _TYPE        = int


class int16_t(NumericType):
    _LOWER_LIMIT = -0x8000
    _UPPER_LIMIT = 0x7FFF
    _FORMAT      = 'h'
    _DEFAULT     = 0
    _TYPE        = int


class uint16_t(NumericType):
    _LOWER_LIMIT = 0
    _UPPER_LIMIT = 0xFFFF
    _FORMAT      = 'H'
    _DEFAULT     = 0
    _TYPE        = int


class int32_t(NumericType):
    _LOWER_LIMIT = -0x80000000
    _UPPER_LIMIT = 0x7FFFFFFF
    _FORMAT      = 'i'
    _DEFAULT     = 0
    _TYPE        = int


class uint32_t(NumericType):
    _LOWER_LIMIT = 0
    _UPPER_LIMIT = 0xFFFFFFFF
    _FORMAT      = 'I'
    _DEFAULT     = 0
    _TYPE        = int


class int64_t(NumericType):
    _LOWER_LIMIT = -0x8000000000000000
    _UPPER_LIMIT = 0x7FFFFFFFFFFFFFFF
    _FORMAT      = 'q'
    _DEFAULT     = 0
    _TYPE        = int


class uint64_t(NumericType):
    _LOWER_LIMIT = 0
    _UPPER_LIMIT = 0xFFFFFFFFFFFFFFFF
    _FORMAT      = 'Q'
    _DEFAULT     = 0
    _TYPE        = int


class float32_t(NumericType):
    _LOWER_LIMIT = -3.40282346638528859811704183484516925e38
    _UPPER_LIMIT = +3.40282346638528859811704183484516925e38
    _FORMAT      = 'f'
    _DEFAULT     = 0.
    _TYPE        = (int, float)


class float64_t(NumericType):
    _LOWER_LIMIT = -1.79769313486231570814527423731704357e308
    _UPPER_LIMIT = +1.79769313486231570814527423731704357e308
    _FORMAT      = 'd'
    _DEFAULT     = 0.
    _TYPE        = (int, float)


class ArrayElems(list):
    def __init__(self, atype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._atype = atype

    def decode(self):
        return self._atype._elems_decode(self)

    def __repr__(self):
        return self._atype._elems_repr(self)

    def __eq__(self, other):
        return self._atype._elems_equal(self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __setitem__(self, k, v):
        if not isinstance(k, (int, slice)):
            raise Exception('Arrays only support integer or slice indices '
                            '(got %s)' % v)
        if isinstance(k, slice):
            slen = len(v)
            rlen = len(range(*k.indices(len(self))))
            if rlen != slen:
                raise Exception('Array bounds or length mismatch error '
                                '(got %s expected %s).' % (rlen, slen))
            for e in v:
                self._atype._type._validate(e)
        else:
            self._atype._type._validate(v)
        super().__setitem__(k, v)


class Array(Type):
    def __init__(self, typ, N):
        super().__init__()
        self._type    = typ
        self._N       = N

    def __set__(self, obj, v):
        if isinstance(v, Array):
            v = v._make()
        if isinstance(v, bytes):
            v = list(v) + [0]*(self._N - len(v))
        self._validate(v)
        obj._fields[self.name] = ArrayElems(self, v)

    def _elems_equal(self, ae, v):
        if isinstance(v, bytes):
            v = list(v) + [0]*(self._N - len(v))
        return all(v_elem == ae_elem for v_elem, ae_elem in zip(v, ae))

    def _elems_repr(self, obj):
        return 'Array(%s, %s)' % (type(self._type).__name__, list.__repr__(obj))

    def _validate(self, v):
        if not isinstance(v, (list, tuple)):
            raise Exception("Array(%s) cannot be assigned a %s." %
                            (type(self._type).__name__, type(v).__name__))
        if len(v) != self._N:
            raise Exception("Array(%s) assigned list of incorrect length %s "
                            "(expected %s)." % (type(self._type).__name__,
                                                len(v), self._N))
        for elem in v:
            self._type._validate(elem)

    def _make(self):
        return ArrayElems(self, (self._type._make() for _ in range(self._N)))

    def _make_from_array(self, a):
        return ArrayElems(self, (self._type._make_from_array(a)
                                 for _ in range(self._N)))

    @classmethod
    def _flatten_r(cls, obj, a):
        if isinstance(obj._atype._type, NumericType):
            for e in obj:
                a.append(e)
        else:
            for e in obj:
                e._flatten_r(e, a)

    def _get_struct_format(self):
        if isinstance(self._type, NumericType):
            return '%u%s' % (self._N, self._type._get_struct_format())
        return self._type._get_struct_format() * self._N


class CString(Array):
    def __init__(self, N):
        super().__init__(uint8_t(), N)

    def _elems_decode(self, obj):
        return bytes(obj).rstrip(b'\x00').decode()

    def _elems_repr(self, obj):
        return repr(bytes(obj).rstrip(b'\x00'))


class Struct(Type):
    def __init__(self, **kwargs):
        super().__init__()
        super().__setattr__('_fields', {})
        for f in self._FIELDS:
            if f.name in kwargs:
                setattr(self, f.name, kwargs[f.name])
                del kwargs[f.name]
            else:
                setattr(self, f.name, f.typ)

        if kwargs:
            raise Exception('Unexpected kwargs: %s' % kwargs)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        fields = []
        for k, v in vars(cls).items():
            if isinstance(v, Type):
                fields.append(Field(k, v))

        cls._FIELDS   = tuple(fields)
        cls._TYPE_MAP = {f.name : f.typ for f in fields}
        cls._STRUCT   = struct.Struct(cls._get_struct_format())

        if hasattr(cls, '_EXPECTED_SIZE'):
            if cls._STRUCT.size != cls._EXPECTED_SIZE:
                raise Exception('Class %s has size %s, expected %s' %
                                (cls, cls._STRUCT.size, cls._EXPECTED_SIZE))

    def __repr__(self):
        attrs = []
        for f in self._FIELDS:
            attrs.append('%s=%s' % (f.name, repr(getattr(self, f.name))))

        return '%s(%s)' % (type(self).__name__, ', '.join(attrs))

    def __setattr__(self, name, v):
        if name not in self._TYPE_MAP:
            raise Exception("Field '%s' is not a member of struct '%s'." %
                            (name, type(self).__name__))
        super().__setattr__(name, v)

    def _validate(self, v):
        if type(v) is not type(self):
            raise Exception("Cannot assign struct %s to %s." %
                            (type(v).__name__, type(self).__name__))

    def __set__(self, obj, v):
        self._validate(v)
        n = self._make()
        for f in self._FIELDS:
            setattr(n, f.name, getattr(v, f.name))
        obj._fields[self.name] = n

    @classmethod
    def _make(cls):
        return cls()

    @classmethod
    def _make_from_array(cls, a):
        n = cls._make()
        for f in cls._FIELDS:
            setattr(n, f.name, f.typ._make_from_array(a))
        return n

    def _flatten(self):
        a = []
        self._flatten_r(self, a)
        return a

    @classmethod
    def _flatten_r(cls, obj, a):
        for f in cls._FIELDS:
            f.typ._flatten_r(getattr(obj, f.name), a)

    @classmethod
    def _get_struct_format(cls):
        fmt = ''
        for f in cls._FIELDS:
            fmt += f.typ._get_struct_format()
        return fmt

    def pack(self):
        return self._STRUCT.pack(*self._flatten())

    @classmethod
    def unpack(cls, data):
        a = list(cls._STRUCT.unpack(data))
        return cls._make_from_array(a)

    @classmethod
    def unpack_from(cls, data, offset=0):
        a = list(cls._STRUCT.unpack_from(data, offset=offset))
        return cls._make_from_array(a)
