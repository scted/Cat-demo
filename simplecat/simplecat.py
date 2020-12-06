from migen import *
from migen.fhdl import verilog
from migen.build.platforms import arty_a7

def create_platform():
    while True:
        yield arty_a7.Platform(toolchain="symbiflow")

platform_factory = create_platform()

class CatDemo4(Module):
    def __init__(self, permutation):
        '''
        Different ways to implement ins(2) => cat_bus(=Cat(s0, s1)) => outs(2)
        sim the same in all cases: ins == outs
        
        "no_slicing" :: verilog == sim
        "lhs" : assign the lhs of bus from ins via slicing: verilog <> sim
        "rhs" : assign the rhs of bus to outs via slicing: verilog <> sim
        "use_signals" : assign ins/out directly to/from cat_bus: verilog == sim
        '''
        
        
        self.ins = ins = Signal(2)
        self.outs = outs = Signal(2)

        self.s0 = s0 = Signal()                                 
        self.s1 = s1 = Signal()
        
        #object of interest
        self.cat_bus = cat_bus = Cat(s0, s1)

        if permutation == "no_slicing":         #sim == verilog
            self.comb += cat_bus.eq(ins)
            
            self.comb += outs.eq(cat_bus)

        elif permutation == "lhs":              #sim <> verilog
            self.comb += cat_bus[0].eq(ins[0])
            self.comb += cat_bus[1].eq(ins[1])
            
            self.comb += outs.eq(cat_bus)

        elif permutation == "rhs":              #sim <> verilog
            self.comb += cat_bus.eq(ins)

            self.comb += outs[0].eq(cat_bus[0])
            self.comb += outs[1].eq(cat_bus[1])

        elif permutation == "use_signals":      #sim == verilog
            self.comb += s0.eq(ins[0])
            self.comb += s1.eq(ins[1])
            
            self.comb += outs[0].eq(s0)
            self.comb += outs[1].eq(s1)
        


class CatDemo4Arty(CatDemo4):
    def __init__(self, *args):
        self.platform = platform = next(platform_factory)
        self.btns = btns = Cat(*[platform.request("user_btn") for n in range(2)])
        self.leds = leds = Cat(*[platform.request("user_led") for n in range(2)])
        CatDemo4.__init__(self, *args)

        self.comb += self.ins.eq(btns)
        self.comb += leds.eq(self.outs)



#all permutations simulate as expected       
def cat4_test(dut):
    for i in range(8):
        yield dut.ins.eq(i)
        yield
        print("ins: {} outs: {}".format(i, (yield dut.outs)))

def run_cat4_sim(permutation):
    print()
    print('Running simulation for "{}" ... appears to work'.format(permutation))
    print()
    dut = CatDemo4(permutation)
    run_simulation(dut, cat4_test(dut))

#but the verilog is not what i was expecting for the assignment to/from a slice ('lhs' and 'rhs' permutions) 
def write_cat4_verilog(permutation):
    top = CatDemo4(permutation)
    print()
    if permutation in ["lhs", "rhs"]:
        print('Writing verilog for "{}" ... something gets mangled and only the MSB is connected'.format(permutation))
    else:
        print('Writing verilog for "{}" ... matches simulation'.format(permutation))
    print()
    print(verilog.convert(top))
    
#will build files that can be consumed by Vivado or Symbiflow to target ArtyA7
def build(demo, *args):
    demo = demo(*args)
    demo.platform.build(demo, run=False)

if __name__ == "__main__":
    for perm in ['no_slicing', 'lhs', 'rhs', 'use_signals']:
        run_cat4_sim(perm)
    for perm in ['no_slicing', 'lhs', 'rhs', 'use_signals']:
        write_cat4_verilog(perm)