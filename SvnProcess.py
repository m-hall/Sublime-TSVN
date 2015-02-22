import sublime
from subprocess import Popen, PIPE
from threading import Thread, Timer
from queue import Queue, Empty
from . import SvnOutput

TIME_INTERVAL = 0.05
LOADING_SIZE = 7

class Process:
    def __init__(self, name, cmd, log=True, thread=False):
        self.name = name
        self.done = False
        self.log = log
        self.outputText = None
        self.errorText = None
        self.loading = 0
        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        if thread:
            self.check_status()
        else:
            self.finish()
            if log:
                self.log_result()

    def log_result(self):
        SvnOutput.add_command(self.name)
        SvnOutput.add_result(self.output())
        SvnOutput.add_error(self.error())
        SvnOutput.end_command()

    def finish(self):
        output, error = self.process.communicate()
        self.outputText = output.decode('UTF-8')
        self.errorText = error.decode('UTF-8')
        self.done = True

    def check_status(self):
        if self.is_done():
            sublime.status_message("Complete: " + self.name)
            if self.log:
                self.log_result()
        else:
            if LOADING_SIZE > 0:
                n = abs(self.loading - LOADING_SIZE)
                sublime.status_message("Running: " + self.name + "[" + " " * (LOADING_SIZE - n) + "=" + " " * n + "]")
                self.loading = (self.loading + 1) % (LOADING_SIZE * 2)

            self.timer = Timer(TIME_INTERVAL, self.check_status)
            self.timer.start()

    def output(self):
        if self.outputText is not None:
            return self.outputText
        if not self.is_done():
            return ''
        output = self.process.stdout.read()
        if output is not None:
            self.outputText = output.decode('UTF-8')
            return self.outputText
        return None

    def error(self):
        if self.errorText is not None:
            return self.errorText
        if not self.is_done():
            return ''
        error = self.process.stdout.read()
        if error is not None:
            self.errorText = error.decode('UTF-8')
            return self.errorText
        return None

    def is_done(self):
        if not self.done:
            self.done = self.process.poll() is not None
        return self.done