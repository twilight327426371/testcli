import sys
import os
import collections


def lines(func):
    def expand_lines(lines):
        expanded = []
        for l in lines:
            if isinstance(l, str):
                expanded.append(l)
            else:
                expanded.extend(expand_lines(l))
        return expanded

    def __lines_1(*vargs, **kv):
        out = func(*vargs, **kv)
        return expand_lines(out)
    return __lines_1

def range_hex(h1,h2):
    co = (int(h2,16) - int(h1,16))/16 - 1 
    hex_list = [ hex(int(h1,16) + 16*i) for i in range(1,co+1) ]
    return  [ (7-len(i.split("0x")[1]))*'0' + i.split("0x")[1] for i in hex_list ]

def first(s):
    return s.split(" ")[0]

@lines
def _replace(li):
    end_profile = " 0000 0000 0000 0000 0000 0000 0000 0000"
    for idx, i in enumerate(li):
        if i.startswith("*"):
            left = li[idx - 1]
            right = li[idx + 1]
            li[idx] = [i + end_profile for i in range_hex(first(left), first(right))]
    return li

def list_data(f):
    with open(f,"r") as f:
        t = f.read().split("\n")
    return [ i for i in t if i ]

class _AttributeDict(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __str__(self):
        state = ["%s=%r" % (attribute, value)
                for (attribute, value)
                in self.items()]
        return '\n'.join(state)

n1 = _AttributeDict({
    'name':None,
    'array':None
})

n2 = _AttributeDict({
    'name':None,
    'array':None
})

#[[[[...], [...], 'b'], [...], None], [[...], [[...], [...], None], 'b'], 'a']

#def _meger(func):
#    def _meger_dict(order_dict):
#        new_dict = collections.OrderedDict()
#        
#
#
#
#    def __meger_1(*args, **kv):
#        out = func(*args, **kv)
#        return out
#    return _meger_1
#class NewOrderedDict(collections.OrderedDict):
#    def __init__(self, )
#    def __cmp__(self, arg1, arg2):

def get_different(a1, a2):
    same_map = collections.OrderedDict()
    different_map = collections.OrderedDict()
    offset, resource = 0, 0
    for a, b in zip(a1,a2):
        if a == b:
            offset += 16
            same_map["%d~%d" % (resource, offset)] = "same"
            resource = offset
        else:
            offset += 16
            different_map["%d~%d" % (resource, offset)] = "different"
            resource = offset
    return same_map, different_map


def compara_data(f1, f2):
    n1.name = os.path.split(f1)[1]
    print n1.name
    print str(n1)
    n1.array = _replace(list_data(f1))
    with open("%s_hexdump" % n1.name,"w+") as n:
        n.write("\n".join(n1.array))
    print len(n1.array)
    n2.name = os.path.split(f2)[1]
    print n2.name
    n2.array = _replace(list_data(f2))
    with open("%s_hexdump" % n2.name,"w+") as n:
        n.write("\n".join(n2.array))
    print len(n2.array)
    _, different_map = get_different(n1.array, n2.array)

    print different_map


if __name__ == "__main__":
    #print range_hex("01f820","01f890")
    if len(sys.argv) < 3:
        raise Exception("need two args!")
    else:
        compara_data(sys.argv[1],sys.argv[2])


