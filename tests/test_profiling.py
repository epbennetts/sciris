'''
Test profiling functions.
'''

import sciris as sc
import numpy as np
import pytest


def test_loadbalancer():
    sc.heading('Testing loadbalancer')
    o = sc.objdict()

    # Test basic functions
    o.ncpus = sc.cpu_count()
    o.cpu = sc.cpuload()
    o.mem = sc.memload()

    # Test loadbalancer
    o.load = sc.loadbalancer(interval=0.1)
    return o


def test_memchecks():
    sc.heading('Testing memory checks')

    o = sc.objdict()
    
    complexobj = sc.prettyobj(
        a = sc.objdict(
            a_dict = {'foo':'bar'},
            a_arr = np.random.rand(243,589),
            ),
        b = [0,1,2,[3,4,'foo']]
    )

    print('\nTesting checkmem')
    o.mem = sc.checkmem(complexobj, descend=2)

    print('\nTesting checkram')
    o.ram = sc.checkram()
    print(o.ram)

    return o


def test_profile():
    sc.heading('Test profiling functions (profile/mprofile)')
    
    print('Benchmarking:')
    bm = sc.benchmark()
    print(bm)
    assert bm['numpy'] > bm['python']
    
    print('Profiling:')

    def slow_fn():
        n = 2000
        int_list = []
        int_dict = {}
        for i in range(n):
            int_list.append(i)
            int_dict[i] = i
        return

    def big_fn():
        n = 1000
        int_list = []
        int_dict = {}
        for i in range(n):
            int_list.append([i]*n)
            int_dict[i] = [i]*n
        return

    class Foo:
        def __init__(self):
            self.a = 0
            return

        def outer(self):
            for i in range(100):
                self.inner()
            return

        def inner(self):
            for i in range(1000):
                self.a += 1
            return

    foo = Foo()
    try:
        sc.mprofile(big_fn) # NB, cannot re-profile the same function at the same time
    except TypeError as E: # This happens when re-running this script
        print(f'Unable to re-profile memory function; this is usually not cause for concern ({E})')
        
    # Run profiling test, checking versions first
    valid_python = '<3.12'
    if sc.compareversions(sc.metadata().versions.python, valid_python):
        sc.profile(run=foo.outer, follow=[foo.outer, foo.inner])
        lp = sc.profile(slow_fn)
    else:
        print(f'Warning: skipping sc.profile() test Python must be {valid_python}')
        lp = None
    
    return lp


def test_cprofile():
    sc.heading('Testing function profiler (cprofile)')
    
    class Slow:
        
        def math(self):
            n = 1_000_000
            self.a = np.arange(n)
            self.b = sum(self.a)
            
        def plain(self):
            n = 100_000
            self.int_list = []
            self.int_dict = {}
            for i in range(n):
                self.int_list.append(i)
                for j in range(10):
                    self.int_dict[i+j] = i+j
        
        def run(self):
            self.math()
            self.plain()
    
    # Option 1: as a context block
    with sc.cprofile() as cpr:
        slow = Slow()
        slow.run()
        
    # Option 2: with start and stop
    cpr = sc.cprofile()
    cpr.start()
    slow = Slow()
    slow.run()
    cpr.stop()
    
    # Tests
    df = cpr.df
    assert len(df) >= 4 # Should be at least this many profiled functions
    assert df[0].cumpct > df[-1].cumpct # Should be in descending order
    
    return cpr


def test_resourcemonitor():
    sc.heading('Testing resource monitor')

    o = sc.objdict()
    o.callback = []

    def callback(checkdata, checkstr):
        ''' Small function to test that callbacks work '''
        print('Callback works as intended')
        o.callback.append(checkdata)
        return

    with pytest.raises(sc.LimitExceeded):
        with sc.resourcemonitor(mem=0.001, interval=0.1, die=False) as resmon:
            print('Effectively zero memory limit')
            sc.timedsleep(0.3)
        raise resmon.exception
    o.resmon_died = resmon

    # As a standalone (don't forget to call stop!)
    resmon = sc.resourcemonitor(mem=0.95, cpu=0.99, time=0.1, interval=0.1, label='Load checker', die=False, callback=callback, verbose=True)
    sc.timedsleep(0.2)
    resmon.stop()
    print(resmon.to_df())

    o.resmon = resmon

    return o


#%% Run as a script
if __name__ == '__main__':
    sc.tic()

    lb  = test_loadbalancer()
    mc  = test_memchecks()
    lp  = test_profile()
    cpr = test_cprofile()
    rm  = test_resourcemonitor()

    sc.toc()
    print('Done.')