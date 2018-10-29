from time import process_time


class Timer():

    """Context manager that measures the time of a process, usage:

    with Timer():
        # the code that you want to meassure
        # and it will output the processing time
    
    Attributes:
        t1 (flost): initial time
    """
    
    def __enter__(self):
        self.t1 = process_time()

    def __exit__(self, *a):
        t2 = process_time()
        print(t2 - self.t1)