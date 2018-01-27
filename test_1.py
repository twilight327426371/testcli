#coding=utf-8
from collections import OrderedDict

class CompletionRefresher(object):
    refreshers = OrderedDict()

def refresher(name, refreshers=CompletionRefresher.refreshers):
    """Decorator to add the decorated function to the dictionary of
    refreshers. Any function decorated with a @refresher will be executed as
    part of the completion refresh routine."""
    def wrapper(wrapped):
        refreshers[name] = wrapped
        return wrapped
    return wrapper

@refresher("test")
def test(name):
    return name
@refresher("new")
def new(name):
    return name


import sys
def check_method_1():
    import select
    if select.select([sys.stdin, ], [], [], 0.0)[0]:
        print "Have data!"
        for line in sys.stdin:
            print line
        print 'end'
    else:
        print "No data"
        
def thread1():
    for x in range(4):
        yield  x
        

def thread2():
    for x in range(4,8):
        yield  x
        

threads=[]
threads.append(thread1())
threads.append(thread2())


def run(threads): #写这个函数，模拟线程并发
    pass

def mustBeKeywords(func):
    import inspect
    positions = inspect.getargspec(func).args
    args, varargs, kwargs, defaults = inspect.getargspec(func)
    def wrapper(*args, **kwargs):
        print args
        print varargs
        print kwargs
        print defaults 
        for pos in positions:
            if pos not in kwargs:
                raise Exception(pos + " must be keyword parameter")
        return func(*args, **kwargs) 
    return wrapper

@mustBeKeywords
def demo(*sss):
    print "*"*20
    print sss 

if __name__ == "__main__":
    #run(threads)
    demo(1, 2, 3, 4, 5, 6)
