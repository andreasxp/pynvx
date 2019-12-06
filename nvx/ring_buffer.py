"""Numpy-based ringbuffer."""
import numpy as np


class RingBuffer:
    def __init__(self, capacity: int, dtype=np.int32):
        """A linear ringbuffer array based on numpy.ndarray.

        Ring buffer is not an array. Not all elements observable through self.data are valid. Instead, ring buffer
        reserves its maximum capacity in the `data` member. After construction, the buffer will be empty - you will need
        to `append()` new values into it.

        In pynvx the buffer is used to temporarily hold samples before they are pulled by the user.

        Parameters
        ----------
        capacity : int
            The maximum amount of elements this ringbuffer can hold, before it starts overwriting old elements.
        dtype
            Type of elements stored in the buffer.
        """
        self.data = np.empty(capacity, dtype=dtype)
        self._begin = 0
        self._size = 0

        self.clear()

    def as_array(self):
        """Convert data to a numpy array.

        Warnings
        --------
        Since numpy arrays must store contiguous data only, this function will always perform a copy of the data. If you
        are sure your data can be represented as a view (self.is_contiguous() returns True) use as_array_view instead.

        Returns
        -------
        numpy.ndarray
            A copy of the data in a flat numpy array. Array's size will not be larger than ringbuf's size.
        """
        if self.is_contiguous():
            # Return a copy via copy
            return np.copy(self.data[self._begin:(self._begin + self.size)])
        else:
            # Return a copy via numpy.concatenate
            return np.concatenate((
                self.data[self._begin:self.capacity],
                self.data[0:((self._begin + self.size) % self.capacity)]
            ))

    def as_array_view(self):
        """Convert data to a numpy array view.

        Warnings
        --------
        Since numpy arrays must store contiguous data only, this function will fail if self.is_contiguous() returns
        False. If you would like the function to copy if the data is bifurcated, use as_array instead.

        Raises
        ------
        BufferError
            if the internal buffer is bifurcated.

        Returns
        -------
        numpy.ndarray
            A view of the data in a flat numpy array. Array's size will not be larger than ringbuf's size.
        """
        if self.is_contiguous():
            # Return a view
            return self.data[self._begin:(self._begin + self.size)]
        else:
            raise BufferError("ring buffer array is bifurcated")

    def is_contiguous(self):
        """Check if the data in the ring buffer has been bifurcated.

        Returns
        -------
        bool
            True if all data is in a contiguous chunk of memory, False otherwise.
        """
        return self._begin + self.size <= self.capacity

    def __len__(self):
        """Return the amount of elements the ringbuffer holds.
        Equivalent to calling buffer.size().
        """
        return self._size
    
    @property
    def size(self):
        """Return the amount of elements the ringbuffer holds.
        Equivalent to calling len(buffer).
        """
        return self._size
    
    @property
    def capacity(self):
        """Return current maximum capacity of the ring buffer."""
        return self.data.shape[0]

    def __getitem__(self, index: int):
        """Retrieve an element from the buffer.

        Parameters
        ----------
        index : int
            An index in range [0, size()) for elements counting from the start, or an index in range [-size(), 0) for
            elements from the end. This function does not accept slices.

        Raises
        ------
        IndexError
            If the index is out of bounds [0, size()).

        Returns
        -------
        value
            Retrieved value.
        """
        if 0 <= index < self.size:
            return self.data[(self._begin + index) % self.capacity]
        elif -self.size <= index < 0:
            return self.data[(self._begin + self.size + index) % self.capacity]
        else:
            raise IndexError("index " + str(index) + " is out of bounds for size " + str(self.size))

    def __setitem__(self, index: int, value):
        """Retrieve an element from the buffer.

        Parameters
        ----------
        index : int
            An index in range [0, size()) for elements counting from the start, or an index in range [-size(), 0) for
            elements from the end. This function does not accept slices.
        value
            A value to set.

        Raises
        ------
        IndexError
            If the index is out of bounds [0, size()).
        """
        if 0 <= index < self.size:
            self.data[(self._begin + index) % self.capacity] = value
        elif -self.size <= index < 0:
            self.data[(self._begin + self.size + index) % self.capacity] = value
        else:
            raise IndexError("index " + str(index) + " is out of bounds for size " + str(self.size))

    def append(self, value):
        """Append an item to the ring buffer.
        Appending elements does not increase the buffer's capacity. If the ring buffer is full, newest element will
        overwrite the oldest.

        Parameters
        ----------
        value
            A value to append.
        """
        self.data[(self._begin + self.size) % self.capacity] = value
        if self.size == self.capacity:
            self._begin = (self._begin + 1) % self.capacity
        else:
            self._size += 1

    def extend(self, iterable):
        """Extend the ring buffer with new items.
        Appending elements does not increase the buffer's capacity. If the ring buffer is full, newest element will
        overwrite the oldest.

        Parameters
        ----------
        iterable
            An iterable to traverse and read values from.
        """
        for value in iterable:
            self.append(value)

    def clear(self):
        """Clear all data from the buffer.
        If dtype of underlying array is object, fills the capacity with None. Otherwise fills it with zeros.
        """
        if self.data.dtype is object:
            self.data.fill(None)
        else:
            self.data.fill(0)
        self._begin = 0
        self._size = 0

    @property
    def dtype(self):
        """Internal objects' dtype."""
        return self.data.dtype

    def __repr__(self):
        return repr(self.data)
