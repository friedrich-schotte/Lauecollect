from threading import Thread
from time import time


class Test():
    N_threads = 1
    N_repeat = 14000
    array_size = 100000

    threads = []
    start_time = 0
    finish_time = 0

    def run(self, **kwargs):
        for (key, value) in kwargs.items():
            setattr(self, key, value)
        self.start()
        self.wait()
        print(f"Run time {self.run_time} s")

    def start(self):
        self.threads = [Thread(target=self.work, daemon=True)
                        for i in range(0,self.N_threads)]
        self.start_time = self.finish_time = time()
        for thread in self.threads:
            thread.start()

    def wait(self):
        for thread in self.threads:
            thread.join()

    @property
    def run_time(self):
        return self.finish_time - self.start_time

    def work(self):
        from numpy import zeros, rint, sin
        x = zeros(self.array_size)
        N = int(rint(self.N_repeat/self.N_threads))
        for i in range(0,N):
            x = sin(x)
        self.finish_time = time()


test = Test()
