import queue

from PyQt6.QtCore import QThread

from bioview.types import BiopacConfiguration, ExperimentConfiguration
from bioview.utils import init_save_file, update_save_file


class ProcessWorker(QThread):
    def __init__(
        self,
        exp_config: ExperimentConfiguration,
        bio_config: BiopacConfiguration,
        rx_queue: queue.Queue,
        disp_queue: queue.Queue,
        running: bool = False,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.exp_config = exp_config

        self.rx_queue = rx_queue
        self.disp_queue = disp_queue
        self.running = running

        self.out_file = exp_config.get_save_path("biopac")
        if self.saving:
            init_save_file(
                file_path=self.out_file, num_channels=len(bio_config.channels)
            )

    def run(self):
        while self.running:
            # Get latest sample
            try:
                samples = self.rx_queue.get()

                # Add to display queue
                try:
                    self.disp_queue.put(samples)
                except queue.Empty:
                    self.logEvent.emit("debug", "[BIOPAC] Display Queue Empty")
                except queue.Full:
                    self.logEvent.emit("debug", "[BIOPAC] Display Queue Full")

                # Save to file
                if self.saving:
                    update_save_file(self.out_file, samples)

            except queue.Empty:
                self.logEvent.emit("debug", "[BIOPAC] Rx Queue Empty")
                continue
            except queue.Full:
                self.logEvent.emit("debug", "[BIOPAC] Rx Queue Full")
                continue
            except Exception as e:
                self.logEvent.emit("error", f"[BIOPAC] Saving error: {e}")
                continue

    def stop(self):
        self.running = False
