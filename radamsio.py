from pyradamsa import Radamsa
from io import BufferedIOBase
from random import choice as random_choice

class RadamsIO(BufferedIOBase):

    _buffer=None

    def __init__(self, source, seed=None, offset=0, mutations=None):
        self.source = source
        self._fuzzer = Radamsa(seed=seed, mut_offset=offset)

        self.mutations = mutations or len(source) + offset
        buf = self.fuzz(source, self.mutations)

        self._buffer = buf
        self._pos = 0

    def fuzz(self, data, size):
        return self._fuzzer.fuzz(data, max_mut=size)

    def __getstate__(self):
        if self.closed:
            raise ValueError("__getstate__ on closed stream")
        return self.__dict__.copy()

    def getvalue(self):
        if self.closed:
            raise ValueError("getvalue of closed stream")
        return bytes(self._buffer)

    def close(self):
        if self._buffer is not None:
            self._buffer.clear()
        super().close()

    def read(self, size=-1):
        if self.closed:
            raise ValueError("read from closed stream")

        if size is None:
            size=-1
        else:
            try:
                size_index = size.__index__
            except AttributeError:
                raise TypeError(f'{size!r} is an integer')
            else:
               size = size_index()

        if size < 0:
            size = len(self._buffer)

        if len(self._buffer) < self._pos + size:
            b = self._buffer[self._pos:]
            buf = self.fuzz(self.source, self.mutations)
            self._buffer = buf
            size = len(self._buffer)
            b += self._buffer[:]
            self._pos = self._pos + size
        else:
            b = self._buffer[self._pos:self._pos + size]
            newpos = min(len(self._buffer), self._pos + size)
            self._pos = self._pos + size

        return bytes(b)

    def read1(self, size=-1):
        return self.read(size)

    def write(self, b):
        raise NotImplementedError("write method not implemented")

    def seek(self, pos, whence=0):
        if self.closed:
            raise ValueError("seek on closed stream")
    
        try:
            pos_index = pos.__index__
        except AttributeError:
            raise TypeError(f'{size!r} is an integer')
        else:
           pos = pos_index()

        if whence == 0:
            if pos < 0:
                raise ValueError("seek for negative position %r" % (pos,))
            self._pos = pos
        elif whence == 1:
            self._pos = max(0, self._pos + pos)
        elif whence == 2:
            self._pos = max(0, len(self._buffer) + pos)
        else:
            raise ValueError("unsupported whence value")
        
        return self._pos

    def tell(self):
        if self.closed:
            raise ValueError("tell on closed stream")

        return self._pos

    def truncate(self, pos=None):
        raise NotImplementedError("truncate method not implemented")

    def readable(self):
        if self.closed:
            raise ValueError("IO operation on closed stream")

        return True

    def writeable(self):
        if self.closed:
            raise ValueError("IO operation on closed stream")

        return False

    def seekable(self):
        if self.closed:
            raise ValueError("IO operation on closed stream")

        return False


class RadamsUrlIO(RadamsIO):
    _ALWAYS_SAFE = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                             b'abcdefghijklmnopqrstuvwxyz'
                             b'0123456789'
                             b'_.-~')

    def sanitize(self, value):
        text = b''
        x = 0
        for i,c in enumerate(value):
            if c not in self._ALWAYS_SAFE:
                text = text+value[x:i]+chr(random_choice(list(self._ALWAYS_SAFE))).encode("utf-8")
                x=i+1

        if x<len(value):
            text=text+value[x:len(value)]

        return text

    def read(self, size=-1):
        b = super().read(size)
        return self.sanitize(b)