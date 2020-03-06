import time

# decorator for debugging execution times

def timeit(method):
    def timed(*args,**kw):
        ts=time.time()
        result=method(*args,**kw)
        te=time.time()
        print("%r %2.2f ms"%(method.__name__,(te-ts)*1000))
        return result
    return timed

def FPS(method):
    def timed(*args,**kw):
        ts=time.time()
        result=method(*args,**kw)
        te=time.time()
        print("FPS %2.2f "%(1/(te-ts)))
        return result
    return timed

def traceit(method):
    def tracer(*args,**kw):
        print(method.__name__,"called")
        result=method(*args,**kw)
        return result
    return tracer

def tracebot(method):
    def tracer(*args,**kw):
        print("robot:", method.__name__, "called")
        result=method(*args,**kw)
        return result
    return tracer

def tracecam(method):
    def tracer(*args,**kw):
        print("cam:",method.__name__,"called")
        result=method(*args,**kw)
        return result
    return tracer