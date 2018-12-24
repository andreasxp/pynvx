import numpy as np


class Vector:
    def __init__(self, dtype=None, adopt_data=None):
        if adopt_data is None:
            self.data = np.empty(2, dtype=dtype)
            self.size = 0
        else:
            self.data = np.asarray(adopt_data, dtype=dtype)
            self.size = len(self.data)

    @property
    def capacity(self):
        return len(self.data)

    @property
    def dtype(self):
        return self.data.dtype

    def _check_index(self, key):
        if type(key) == slice:
            if key.stop < 0 or key.stop > self.size:
                raise IndexError("vector index out of range")
            if key.start is not None and (key.start < 0 or key.start > key.stop):
                raise IndexError("vector index out of range")
        else:
            # assumed int
            if key < 0 or key >= self.size:
                raise IndexError("vector index out of range")

    def reserve(self, new_size):
        if new_size > self.capacity:
            new_data = np.empty(new_size, dtype=self.dtype)
            new_data[0:self.size] = self.data[0:self.size]
            self.data = new_data

    def shrink_to_fit(self):
        if self.size < self.capacity:
            new_data = np.empty(self.size, dtype=self.dtype)
            new_data[0:self.size] = self.data[0:self.size]
            self.data = new_data

    def append(self, value):
        if self.capacity == self.size:
            self.reserve(self.size * 2)

        self.data[self.size] = value
        self.size += 1

    def extend(self, values):
        self.reserve(self.size + len(values))

        self.data[self.size:self.size+len(values)] = values
        self.size += len(values)

    def clear(self):
        self.data[0:self.size] = np.zeros(self.size, dtype=self.dtype)
        self.size = 0

    def copy(self):
        result = Vector(dtype=self.dtype, adopt_data=np.copy(self.data))
        result.size = self.size
        return result

    def __len__(self):
        return self.size

    def __setitem__(self, key, value):
        self._check_index(key)
        self.data[key] = value

    def __getitem__(self, key):
        self._check_index(key)
        return self.data[key]

    def __delitem__(self, key):
        self._check_index(key)

        # Determine start and stop markers for deletion
        start = 0
        length = 0

        if type(key) == slice:
            # Deleting slice
            if key.start is not None:
                start = key.start

            if key.step is not None and key.step != 1:
                # If step is not one, can't delete efficiently

                # When deleting by-element, the array shifts.
                # To keep track of shifting, adjusted_index points to the actual element to delete.
                index = start
                adjusted_index = start

                while index < key.stop:
                    del self[adjusted_index]
                    adjusted_index -= 1

                    adjusted_index += key.step
                    index += key.step
                return

            length = key.stop - start
        else:
            start = key
            length = 1

        # Move elements to delete to end
        self.data[start:self.size] = np.roll(self.data[start:self.size], -length)

        # Delete elements
        self.data[self.size - length:self.size] = np.zeros(length, dtype=self.dtype)
        self.size -= length

    def __iter__(self):
        return self.data[0:self.size].flat

    def __add__(self, other):
        result = Vector(dtype=self.dtype)
        result.reserve(len(self) + len(other))
        result.extend(self)
        result.extend(other)
        return result

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __str__(self):
        return str(self.data[0:self.size])

    def __repr__(self):
        return repr(self.data[0:self.size])



