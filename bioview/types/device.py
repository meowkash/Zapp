import queue

import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal

from .config import Configuration
from .datasource import DataSource
from .status import ConnectionStatus

class Device(QObject):
    connectionStateChanged = pyqtSignal(ConnectionStatus)
    logEvent = pyqtSignal(str, str)
    dataReady = pyqtSignal(np.ndarray, DataSource)

    def __init__(
        self,
        config: Configuration,
        device_name: str,
        device_type: str,
        save: bool = False,
        save_path=None,
        display=True,
    ):
        super().__init__()
        self.device_name = device_name
        self.config = config
        self.device_type = device_type

        self.state = ConnectionStatus.DISCONNECTED

        self.handler = None

        self.threads = {}

        # Configuration for saving
        self.save = save
        self.save_path = save_path
        if self.save:
            self.save_queue = queue.Queue()
        else:
            self.save_queue = None

        # Configuration for display
        self.display = display
        if self.display:
            self.display_queue = queue.Queue()
        else:
            self.display_queue = None

        # Keep track of all data sources
        self.data_sources: list[DataSource] = []
        # Make data sources available, depending on config
        self._populate_data_sources()

    def _populate_data_sources(self):
        raise NotImplementedError  # We expect subclasses to implement this

    def get_disp_freq(self):
        return self.config.get_disp_freq()

    def connect(self):
        raise NotImplementedError

    def run(self):
        for thread in self.threads.values():
            thread.logEvent.connect(self._log_message)
            thread.start()

    def stop(self):
        for thread in self.threads.values():
            thread.stop()

    def _on_connect_success(self):
        self.connectionStateChanged.emit(ConnectionStatus.CONNECTED)

    def _on_connect_failure(self, msg):
        self.logEvent.emit("error", msg)
        self.connectionStateChanged.emit(ConnectionStatus.DISCONNECTED)

    def _log_message(self, level, msg):
        self.logEvent.emit(level, msg)

    def _update_display(self, data, source):
        self.dataReady.emit(data, source)
