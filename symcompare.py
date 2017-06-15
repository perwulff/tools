#!/usr/bin/env python

import subprocess
import pprint
import sys
import os
import re

# read file
def parse_elf(inp):

    #print "Parsing file: %s" % (inp)

    data = {}
    udata = 0
    idata = 0
    code = 0

    tmp = subprocess.check_output(['avr-nm','-a','-S','--size-sort',inp])
    lines = tmp.split(b'\n')
    for l in lines:
        try:
            params = l.split(b' ')
            if len(params) >= 4:
                elm = {}
                elm['addr'] = params[0]
                sym = elm['sym'] = params[2]
                size = elm['size'] = int(params[1], 16)
                if sym in "bBCsS":
                    # un-initialized data
                    udata += size
                elif sym in "dDgG":
                    # initialized data
                    idata += size
                else:
                    # code
                    code += size
                file = elm['file'] = params[3]
                data[file] = elm
            else:
                #print "not parsed: " + l
                pass
        except:
            print "Failed to pass line [%s] in file [%s]" % (str(l), inp)
            raise

    return (data, udata, idata, code)


# read file
def parse_obj(inp):

    #print "Parsing dir: %s" % (inp)

    data = {}
    udata = 0
    idata = 0
    code = 0

    for root, subFolders, files in os.walk(inp):
        for f in files:
            if f.endswith(".o"):
                objfile = os.path.join(root, f)
                tmp = subprocess.check_output(['avr-nm','-S',objfile])
                lines = tmp.split(b'\n')
                for l in lines:
                    try:
                        params = l.split(b' ')
                        if (len(params) >= 4) and params[0] and params[1] and params[2]:
                            common_name = re.sub(inp, '', objfile)
                            cnames = common_name.split('/')
                            if len(cnames) > 2:
                                common_name = '/'.join(cnames[0:3])
                            file = os.path.dirname(common_name)
                            if not file in data:
                                data[file] = {}
                            elm = data[file]
                            elm['file'] = file

                            #elm['addr'] = params[0]
                            sym = params[2]
                            size = int(params[1], 16)
                            if sym in "bBCsS":
                                # un-initialized data
                                udata += size
                            elif sym in "dDgG":
                                # initialized data
                                idata += size
                            else:
                                # code
                                code += size
                            if not 'size' in elm:
                                elm['size'] = 0
                            elm['size'] += size
                        else:
                            #print "not parsed: " + l
                            pass
                    except:
                        print "Failed to pass line [%s] in file [%s]" % (str(l), objfile)
                        raise

    return (data, udata, idata, code)


# main
if (len(sys.argv) == 4) and (sys.argv[1] == 'elf'):
    inp_1 = sys.argv[2]
    (data_1, udata_1, idata_1, code_1) = parse_elf(inp_1)
    print "reference: %s, uninitialized data: %d, initialized data: %d, code: %d" % (inp_1, udata_1, idata_1, code_1)

    inp_2 = sys.argv[3]
    (data_2, udata_2, idata_2, code_2) = parse_elf(inp_2)
    print "input: %s, uninitialized data: %d, initialized data: %d, code: %d" % (inp_2, udata_2, idata_2, code_2)
elif (len(sys.argv) == 4) and (sys.argv[1] == 'obj'):
    inp_1 = sys.argv[2]
    (data_1, udata_1, idata_1, code_1) = parse_obj(inp_1)
    print "reference: %s, uninitialized data: %d, initialized data: %d, code: %d" % (inp_1, udata_1, idata_1, code_1)

    inp_2 = sys.argv[3]
    (data_2, udata_2, idata_2, code_2) = parse_obj(inp_2)
    print "input: %s, uninitialized data: %d, initialized data: %d, code: %d" % (inp_2, udata_2, idata_2, code_2)
else:
    print "usage: <type> <file1> <file2>"
    exit(1)


# compare
for k2, v2 in data_2.iteritems():
    if k2 in data_1:
        v1 = data_1[k2]
        #pprint.pprint(v1)
        #pprint.pprint(v2)
        # compare against ref
        if v2['size'] < v1['size']:
            print "- %5d : %s" % (v1['size'] - v2['size'], str(v2))
        elif int(v2['size']) > int(v1['size']):
            print "+ %5d : %s" % (v2['size'] - v1['size'], str(v2))
        del data_1[k2]
    else:
        print "+ %5d : %s (new)" % (v2['size'], str(v2))

for k1, v1 in data_1.iteritems():
    print "- %5d : %s (del)" % (v1['size'], str(v1))
