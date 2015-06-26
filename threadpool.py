import threading, queue



class Threadpool(object):
    def __init__(self,size):
        self.size = size
        self.input = queue.Queue()
        self.output = queue.Queue()
    def map(self,func,*args):
        tuples = zip(*args)
        for t in tuples:
            self.input.put(t)
        def worker(func):
            while True:
                try:
                    myargs = self.input.get(t,False)
                    self.output.put(func(*myargs))
                    self.input.task_done()
                except:
                    return
        threads = map(lambda x: threading.Thread(target=lambda: worker(func)), range(self.size))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        while not self.output.empty():
            yield self.output.get()
            self.output.task_done()

if __name__ == "__main__":
    t = Threadpool(5)
    for x in t.map(print,range(20)):
        pass