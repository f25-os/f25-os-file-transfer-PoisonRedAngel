#! /usr/bin/env python3


import os
from buffers import BufferedWriter, BufferedReader

class FramedWriter:
    def __init__(self):
        # Create an instance of our BufferedWriter to handle efficient writing.
        self.writer = BufferedWriter(1)#self is the instance of the class FramedWriter

    #Finds a file's size, creates a header, and writes the header and data
    def write_file(self, filename_to_add):

        os.write(2, f"Archiving: {filename_to_add}\n".encode())

        fd = os.open(filename_to_add, os.O_RDONLY)# Open the input file for reading

        file_size = os.lseek(fd, 0, os.SEEK_END)# this sets the file offset to the end of the file and returns the file size
        os.lseek(fd, 0, os.SEEK_SET)# this returns the file offset to the beginning of the file
        # --- ----the Header ----------
        # 1. Convert filename string to bytes.
        filename_bytes = filename_to_add.encode()
        # 2. Pad the filename with null bytes until it is exactly 100 bytes long.
        padded_filename = filename_bytes.ljust(100, b'\0')#adds null bytes to the right until it is 100 bytes long
        # 3. Convert the integer file_size into an 8-byte sequence.
        length_bytes = file_size.to_bytes(8, 'big')#convert the integer file_size into an 8-byte sequence using big-endian byte order
        # 4. Combine them to create the 108-byte header.
        header = padded_filename + length_bytes
        
        # --- ---- Write the header and file data to the buffered writer -----
        self.writer.write(header)

        # Read the input file's data in chunks and write each chunk to the buffer.
        while True:
            chunk = os.read(fd, 4096)#os.read reads up to 4096 bytes from the file descriptor fd
            if not chunk:
                break
            self.writer.write(chunk)
            
        # Close the input file we were reading from.
        os.close(fd)

    def close(self):
        """Closes the underlying buffered writer, flushing any remaining data."""
        self.writer.close()#close the underlying buffered writer, flushing any remaining data

class FramedReader:
    def __init__(self):
        # Create an instance of our BufferedReader to handle efficient reading.
        self.reader = BufferedReader(0)

    def read_next_file(self):
        """Reads the next header and data chunk from the archive, saving it to a file."""
        
        # --- Read the Header ---
        # Read the fixed-size 108-byte header from the archive.
        header = self.reader.read(108)
        
        # If the header is empty, we've reached the end of the archive.
        if not header:
            return False # Signal that we are done.

        # --- Unpack the Header ---
        # 1. The first 100 bytes are the padded filename.
        padded_filename = header[:100]
        # 2. The last 8 bytes are the data length.
        length_bytes = header[100:]
        
        # 3. Remove the null-byte padding and decode to get the original filename string.
        filename = padded_filename.strip(b'\0').decode()
        # 4. Convert the 8 bytes for the length back into an integer.
        data_length = int.from_bytes(length_bytes, 'big')

        os.write(2, f"Extracting: {filename} ({data_length} bytes)\n".encode())
        # --- Read the Data and Write to New File ---
        # Create and open the new file for writing.
        output_fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        #writer = BufferedWriter(output_fd)
        # Keep reading from the archive until we've read the full data_length.
        bytes_remaining = data_length
        while bytes_remaining > 0:
            # Read a chunk from the archive.
            chunk = self.reader.read(min(bytes_remaining, 4096))
            if not chunk: # Should not happen if archive is not corrupt
                break
            # Write the chunk to the new file.
            os.write(output_fd, chunk)
            #writer.write(chunk)
            bytes_remaining -= len(chunk)
            
        # Close the new file that we just created.
        os.close(output_fd)
        return True # Signal success.

    def close(self):
        """Closes the underlying buffered reader."""
        self.reader.close()
