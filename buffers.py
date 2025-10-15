#! /usr/bin/env python3


import os

class BufferedWriter:
    def __init__(self, fd, buffer_size=4096):
        self.fd = fd
        self.buffer = bytearray()
        self.buffer_size = buffer_size

    def write(self, data):
        self.buffer.extend(data)
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        if self.buffer:
            # Use a loop for a "reliable write"
            data_to_write = self.buffer
            while data_to_write:
                bytes_written = os.write(self.fd, data_to_write)
                data_to_write = data_to_write[bytes_written:]
            self.buffer.clear()

    def close(self):
        self.flush()
        # Only close the file descriptor if it's not a standard one (0, 1, or 2).
        if self.fd > 2:
            os.close(self.fd)

class BufferedReader:
    def __init__(self, fd, buffer_size=4096):
        self.fd = fd
        self.buffer = b""
        self.buffer_size = buffer_size

    def read(self, bytes_to_read):
        """Reads a specific number of bytes."""
        result = bytearray()
        while len(result) < bytes_to_read:
            if not self.buffer:
                self.buffer = os.read(self.fd, self.buffer_size)
                if not self.buffer: # End of file
                    break
            
            chunk_size = min(bytes_to_read - len(result), len(self.buffer))
            result.extend(self.buffer[:chunk_size])
            self.buffer = self.buffer[chunk_size:]
        return bytes(result)

    def close(self):
        os.close(self.fd)