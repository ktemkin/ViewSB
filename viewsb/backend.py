"""
ViewSB backend class defintions -- defines the abstract base for things that capture USB data.
"""

import io

from .ipc import ProcessManager


class ViewSBBackendProcess(ProcessManager):
    """ Class that controls and communicates with a VSB backend running in another process. """
    pass



class ViewSBBackend:
    """ Generic parent class for sources that capture USB data. """


    def __init__(self):
        """
        Function that initializes the relevant backend. In most cases, this objects won't be instantiated
        directly -- but instead instantiated by the `run_asynchronously` / 'run_backend_asynchronously` helpers.
        """
        pass


    def set_up_ipc(self, output_queue, termination_event, stdin=None):
        """
        Function that accepts the synchronization objects we'll use for output. Must be called prior to
        calling run().

        Args:
            output_queue -- The Queue object that will be fed any USB data generated.
            termination_event -- A synchronization event that is set when a capture is terminated.
        """

        # Store our IPC primitives, ready for future use.
        self.output_queue      = output_queue
        self.termination_event = termination_event


    def run_capture(self):
        """ Runs a single iteration of our backend capture. """
        raise NotImplementedError("backends must implement run_capture(), or override run()")


    def emit_packet(self, packet):
        """ Emits a given ViewSBPacket-derivative to the main decoder thread for analysis. """
        self.output_queue.put(packet)


    def run(self):
        """ Runs the given backend until the provided termination event is set. """

        # Capture infinitely until our termination signal is set.
        while not self.termination_event.is_set():
            self.run_capture()

        # Allow the backend to handle any data still pending on termination.
        self.handle_termination()


    def handle_termination(self):
        """ Called once the capture is terminated; gives the backend the ability to capture any remaining data. """
        pass



class FileBackend(ViewSBBackend):
    """ Generic class for mass parsing packets from files. """

    # Provided for the default implementation of run_capture.
    # Specifies the amount of data that should be read from the file at once.
    # If none, we'll try to read all of the data available at once. :)
    # Defaults to a sane value for reading regular files, per python.
    # Not (directly) used if `next_read_size()` is overridden.
    READ_CHUNK_SIZE = io.DEFAULT_BUFFER_SIZE

    def __init__(self, target_filename):

        # Open the relevant file for reading. 
        self.target_file = open(target_filename, 'rb', buffering=0)


    def next_read_size(self):
        """ Returns the amount of data that should be read in the next read. """
        return self.READ_CHUNK_SIZE


    def read(self, length):
        """
        Read handler that the subclass can call to perform a manual read.
        Useful for grabbing data payloads following a header captured by `capture_data`.
        """
        return self.target_file.read(length)


    def run_capture(self):
        """
        Primary capture function: reads a single chunk from the file, and passes
        it to `handle_data` for conversion into ViewSB packets.
        """

        # Attempt to read a chunk from the given file.
        data = self.target_file.read(self.READ_CHUNK_SIZE)

        # If we have data, handle it.
        if data:
            self.handle_data(data)

        #TODO: handle EOF


    def handle_data(self, data):
        """ Handle chunks of data read from the relevant file. """
        raise NotImplementedError("subclass must implement handle_data()")






