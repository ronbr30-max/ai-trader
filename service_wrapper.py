import sys
import os
import time
import subprocess
import win32serviceutil
import win32service
import win32event
import servicemanager


class AITraderService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AITrader"
    _svc_display_name_ = "AI Trader - Paper Trading Bot"
    _svc_description_ = "Automated AI paper-trading bot with Streamlit dashboard on port 8501"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.run_loop()

    def run_loop(self):
        work_dir = os.path.dirname(os.path.abspath(__file__))
        python_exe = sys.executable

        while win32event.WaitForSingleObject(self.stop_event, 0) == win32event.WAIT_TIMEOUT:
            try:
                self.process = subprocess.Popen(
                    [
                        python_exe, "-m", "streamlit", "run", "app.py",
                        "--server.headless", "true",
                        "--server.address", "0.0.0.0",
                        "--server.port", "8501"
                    ],
                    cwd=work_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.process.wait()
            except Exception:
                pass

            if win32event.WaitForSingleObject(self.stop_event, 10000) != win32event.WAIT_TIMEOUT:
                break


if __name__ == "__main__":
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AITraderService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AITraderService)
