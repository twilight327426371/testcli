#!/usr/bin/python
import re
import shlex
from cmd import Cmd
import os
import inspect
from ctypes import *
from xml.etree.ElementTree import parse, tostring, iterparse
import json
import time
import traceback
import math
import string
import sys
sys.path.append('/odsp/scripts')
import logging


#log = open('/tmp/ntcli-log', 'a')
debug = False

def cur_time_str():
    return time.strftime('%Y-%m-%d %H:%M:%S')

def write_log(msg):
    pass
    #global log
    #log.write('%s: %s\n' % (cur_time_str(), msg))
    #log.flush()

class Unit:
    unit = ['Byte','KB','MB','GB','TB','PB','EB']
    coef = {'Byte': pow(1024,0),
        'KiB' : pow(1024,1),
        'MiB' : pow(1024,2),
        'GiB' : pow(1024,3),
        'TiB' : pow(1024,4),
        'PiB' : pow(1024,5),
        'EiB' : pow(1024,6),
        'KB'  : pow(1024,1),
        'MB'  : pow(1024,2),
        'GB'  : pow(1024,3),
        'TB'  : pow(1024,4),
        'PB'  : pow(1024,5),
        'EB'  : pow(1024,6)}

    def __init__(self, size, ceil=None):
        m = re.search('([0-9.]+)([a-zA-Z]+)', size)
        val = m.group(1)
        unit = m.group(2)

        self.byte_size = float(val) * Unit.coef[unit]
        if ceil:
           ceil_size = math.ceil(self.__convert_size(self.byte_size, ceil))
           self.byte_size = Unit('%s%s' % (ceil_size, ceil)).byte_size

    def __getattr__(self, name):
        if not name in Unit.coef: return None
        return self.__convert(self.byte_size, name)

    def __convert(self, byte_size, unit):
        size = self.__convert_size(byte_size, unit)
        if float('%.2f' % size).is_integer(): return '%d%s' % (size, unit)
        return '%.2f%s' % (size, unit)

    def __convert_size(self, byte_size, unit):
        d = Unit.coef[unit]
        size = byte_size / d
        return size

    def __str__(self):
        for u in Unit.unit:
            size = self.__convert_size(self.byte_size, u)
            if size < 1024: return getattr(self, u)


class AttrObject(dict):
    def __getattr__(self, name):
        if name in self: return self[name]
        else: return None

class XMLFormat:
    ATTR_ORDER = ('basetype', 'name', 'units', 'key', 'type', 'format')
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

    def __init__(self):
        self.xml = parse(os.path.join(os.path.split(__file__)[0], 'dothill.xml'))

    def format(self, odsptype, obj):
        self.oid = 0
        if odsptype:
            self.OBJECT = self.xml.find('OBJECT[@odsptype="%s"]' % odsptype)
            self.SUBOBJECT = self.OBJECT.find('SUBOBJECT')
            self.PROPERTY = self.OBJECT.findall('PROPERTY')
            self.SUBPROPERTY = (not self.SUBOBJECT is None) and self.SUBOBJECT.findall('PROPERTY') or []
            self.ALL_PROPERTY = self.OBJECT.findall('.//PROPERTY')

            self.odspfields = [PRO.get('odspfield') for PRO in self.ALL_PROPERTY]
            if isinstance(obj, str):
                obj = self.__mapobj(obj)
        return '\n'.join(self.__format_obj(obj))

    @lines
    def __format_obj(self, obj):
        return ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<RESPONSE VERSION="L100">',
                [self.__indent(self.__format_single_obj(so)) for so in obj],
                self.__indent(self.__status(obj)),
                '</RESPONSE>']

    def error(self, message):
        return '\n'.join(['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<RESPONSE VERSION="L100">',
                '  <COMP G="0" P="1"/>',
                '  <OBJECT basetype="status" name="status" oid="1">',
                '    <PROPERTY name="response-type" type="string">Error</PROPERTY>',
                '    <PROPERTY name="response-type-numeric" type="uint32">1</PROPERTY>',
                '    <PROPERTY name="response" type="string">%s</PROPERTY>' % message,
                '    <PROPERTY name="return-code" type="sint32">0</PROPERTY>',
                '    <PROPERTY name="component-id" type="string"></PROPERTY>',
                '    <PROPERTY name="time-stamp" type="string">%s</PROPERTY>' % cur_time_str(),
                '    <PROPERTY name="time-stamp-numeric" type="uint32">0</PROPERTY>',
                '  </OBJECT>',
                '</RESPONSE>'])

    def __status(self, obj):
        self.oid += 1
        return ['<COMP G="0" P="%s"/>' % self.oid,
                '<OBJECT basetype="status" name="status" oid="%s">' % self.oid,
                '  <PROPERTY name="response-type" type="string">Success</PROPERTY>',
                '  <PROPERTY name="response-type-numeric" type="uint32">0</PROPERTY>',
                '  <PROPERTY name="response" type="string">Command completed successfully.</PROPERTY>',
                '  <PROPERTY name="return-code" type="sint32">0</PROPERTY>',
                '  <PROPERTY name="component-id" type="string"></PROPERTY>',
                '  <PROPERTY name="time-stamp" type="string">%s</PROPERTY>' % cur_time_str(),
                '  <PROPERTY name="time-stamp-numeric" type="string">%s</PROPERTY>' % int(time.time()),
                '</OBJECT>']

    @lines
    def __format_single_obj(self, obj):
        self.oid += 1
        self.suboid = self.oid
        subfield = (not self.SUBOBJECT is None) and self.SUBOBJECT.get('odspfield') or ''
        sub_objs = subfield and obj[subfield] or [obj]

        xml = ['<COMP G="0" P="%s"/>' % self.oid,
               '<OBJECT %s oid="%s">' % (self.__get_attrib(self.OBJECT), self.oid),
               self.__indent(self.__format_prop(self.PROPERTY, obj)),
               '</OBJECT>',
               [self.__format_subobj(so) for so in sub_objs]]
        self.oid = self.suboid
        return xml

    @lines
    def __format_subobj(self, obj):
        if self.SUBOBJECT is None: return []
        self.suboid += 1
        return ['<COMP G="%s" P="%s"/>' % (self.oid, self.suboid),
                '<OBJECT %s oid="%s">' % (self.__get_attrib(self.SUBOBJECT), self.suboid),
                self.__indent(self.__format_prop(self.SUBPROPERTY, obj)),
                '</OBJECT>']

    @lines
    def __format_prop(self, PROPERTY, sobj):
        return ['<PROPERTY %s>%s</PROPERTY>' %\
            (self.__get_attrib(PRO), self.__map_single_prop(PRO, sobj)) for PRO in PROPERTY]

    def __get_attrib(self, NODE):
        items = NODE.attrib.copy()
        odspkey = [k for k in items if k.find('odsp') <> -1]
        for k in odspkey:
            del items[k]
        return ' '.join(['%s="%s"' % (k, items[k]) for k in XMLFormat.ATTR_ORDER if items.has_key(k)])

    def __has_text(self, NODE):
        return NODE.text and NODE.text.lstrip().rstrip()

    def __map_single_prop(self, S_PROPERTY, sobj):
        if self.__has_text(S_PROPERTY): return S_PROPERTY.text
        VALMAP = S_PROPERTY.findall('VALMAP')
        valmap = dict([(VM.get('odspval'), VM.get('val')) for VM in VALMAP])
        odspval = sobj[S_PROPERTY.get('odspfield')]
        return valmap.get(odspval, odspval)

    def __mapobj(self, obj):
        vals = zip(*[re.findall('%s\s*:\s*([^\n]+)' % field, obj) for field in self.odspfields])
        return [dict(zip(self.odspfields, v)) for v in vals]

    def __indent(self, lines):
        return ['  %s' % line for line in lines]


class Str2List:
    def __call__(self, s):
        return self.__colon_list(s)

    def __split2(self, s):
        m = re.search('(\d+)$', s)
        s2 = m.group(1)
        return s[0:-len(s2)], s2

    def __hyphen_list(self, s):
        m = re.search('^([^-]+)-([^-]+)$', s)
        if s.startswith('"') and s.endswith('"'): return [s[1:-1]]
        if not m: return [s.lstrip().rstrip()]
        start1,start2 = self.__split2(m.group(1))
        end1,end2 = self.__split2(m.group(2))
        return ['%s%s' % (start1.lstrip().rstrip(), i) for i in range(int(start2), int(end2)+1)]

    def __comma_list(self, s):
        l = []
        for h in s.split(','):
            l = l + self.__hyphen_list(h)
        return l

    def __colon_list(self, s):
        l = []
        for c in s.split(':'):
            l = l + self.__comma_list(c)
            l = l + [':']
        return l[:-1]

    def to_list(self, s):
        return self.__colon_list(s)

class CmdError(Exception):
    def __init__(self, msg='', detail=''):
        Exception.__init__(self, msg)
        self.detail = detail

class InvalidParameters(CmdError):
    def __init__(self, name='', val=''):
        CmdError.__init__(self, 'Invalid Parameters.(%s=%s)' % (name, val))
        self.name = name
        self.val = val

class NodeNotExisted(CmdError):
    def __init__(self, name):
        CmdError.__init__(self, '%s not existed' % name)

class EnumCheck:
    def __init__(self, enum, ignorecase=True):
        self.enum = enum
        self.ignorecase = ignorecase
        if ignorecase and isinstance(self.enum[0], str):
            self.enum = [e.upper() for e in enum]

    def __call__(self, s):
        if self.ignorecase:
            s = s.upper()
        if not s in self.enum: raise CmdError('Unsurpported Value')

def args():
    _args = inspect.getargvalues(inspect.stack()[1][0]).args
    _locals = inspect.getargvalues(inspect.stack()[1][0]).locals
    return dict([(a, _locals[a]) for a in _args if a <> 'self'])

def make_opt(name, default=None, nokey=False, convertor=str, check=None):
    ao = AttrObject()
    ao.update(args())
    ao['argname'] = name.replace('-', '_')
    return ao


def options(*opt_desc):
    def get_opt_val(tokens, name):
        try:
            idx = tokens.index(name)
            eidx = idx+1
            if ' '.join(tokens[idx:eidx]) == name:
                val = tokens[eidx]
                return tokens[0:idx] + tokens[eidx+1:], val
        except:
            return tokens, None

    def get_opts(line, opt_desc, opt2val):
        opts = {}
        tokens = shlex.split(line)
        print "tokens:", tokens
        print opt_desc
        for o in opt_desc:
            if o.nokey: continue
            tokens, val = get_opt_val(tokens, o.name)
            if val: 
                opt2val[o.name] = val
                newval = o.convertor(val)
                if o.check: 
                    try:
                        o.check(newval)
                    except:
                        raise InvalidParameters(o.name, val)
                opts[o.argname] = newval
        print "get_opts: ", opts
        print "get_opts: ", tokens
        return opts, tokens

    def check_undefault_opts(opts, opt_desc):
        for desc in opt_desc:
            if desc.default is None and not desc.nokey:
                if not desc.name in opts:
                    raise CmdError('Missing Options: %s' % desc.name)

    def insert_nokey_opts(tokens, opts, opt_desc, opt2val):
        tokens.reverse()
        for desc in opt_desc:
            if desc.nokey:
                if len(tokens) == 0: 
                    if not desc.default is None:
                        opts[desc.argname] = desc.default
                    else:
                        raise CmdError('Missing: %s' % desc.name)
                else:
                    try:
                        val = tokens.pop()
                        opt2val[desc.name] = val
                        newval = desc.convertor(val)
                        if desc.check: 
                            try:
                                desc.check(newval)
                            except:
                                raise InvalidParameters(desc.name, val)
                        opts[desc.argname] = newval
                    except Exception as e:
                        raise e

    def insert_default_opts(opts, opt_desc):
        for desc in opt_desc:
            if not desc.default is None and not desc.name in opts:
                opts[desc.argname] = desc.default

    def _options1(func):
        def _options2(cmd, args):
            print "cmd:", cmd
            print "args: ", args
            opt2val = {}
            opts, tokens = get_opts(args, opt_desc, opt2val)
            check_undefault_opts(opts, opt_desc)
            insert_nokey_opts(tokens, opts, opt_desc, opt2val)
            insert_default_opts(opts, opt_desc)
            try:
                ret = func(cmd, **opts)
            except InvalidParameters as e:
                if not e.val:
                    raise InvalidParameters(e.name, opt2val[e.name])
                raise e

            if ret is None: return '', ''
            else: return ret
        return _options2
    return _options1

def errmatch(*match):
    def _errmatch1(func):
        def _errmatch2(self, *vargs, **kv):
            try:
                all_args = inspect.getcallargs(func, self, *vargs[:], **kv.copy())
                return func(self, *vargs, **kv)
            except CmdError as e:
                all_args['time'] = cur_time_str()
                for m in match:
                    if m[0] and e.detail.find(m[0]) <> -1:
                        raise CmdError(m[1] % all_args)
                raise e
        return _errmatch2
    return _errmatch1

class NTCli(Cmd):
    cmd_map = {}
    prompt = '#'
    def __init__(self):
        Cmd.__init__(self)

    @classmethod
    def register(cls, cmd_class):
        cmd = cmd_class()
        for attr in dir(cmd):
            m = getattr(cmd, attr)
            if callable(m) and attr.endswith('_cmd'):
                cls.__create_cmd(cls.cmd_map, cmd_class, attr, m)
    
    @classmethod
    def __create_cmd(cls, cmd_map, cmd_class, cmdname, method):
        keys = []
        if hasattr(cmd_class, 'cmd_map'):
            try:
                keys = getattr(cmd_class, 'cmd_map')[cmdname]
            except:
                pass
        keys = keys and keys or cmdname.replace('_cmd', '').split('_')
        cls.__register_cmd(cmd_map, keys, (cmd_class, cmdname))
        setattr(cls, 'complete_%s' % keys[0], NTCli.__complete)
        setattr(cls, 'do_%s' % keys[0], NTCli.__do)

    @classmethod
    def __register_cmd(cls, map, keys, cmd):
        if len(keys) == 1: map[keys[0]] = cmd
        else: cls.__register_cmd(map.setdefault(keys[0], {}), keys[1:], cmd)

    def __do(self, args):
        keys = self.lastcmd.split()
        cmd_class, cmdname = self.__get_method(keys)
        if cmd_class and len(keys) >= 2:
            try:
                cmd = cmd_class()
                odsptype, out = getattr(cmd, cmdname)(args.replace(keys[1], '', 1))
                print XMLFormat().format(odsptype, out)
            except Exception as e:
                if debug: print traceback.print_exc()
                #else: print XMLFormat().error(e.message)
                else: print e.message

    def do_enable_debug(self, args):
        global debug
        debug = True

    def do_disable_debug(self, args):
        global debug
        debug = False

    def __complete(self, text, line, begidx, endidx):
        keys = line.split()
        map = NTCli.cmd_map[keys[0]]
        if len(keys) == 1: return map.keys()
        elif len(keys) == 2: 
            completion = [c for c in map if c.startswith(keys[1])]
            idx = keys[1].rfind('-')
            if completion and idx <> -1:
                completion = [completion[0].replace(keys[1][0:idx+1], '')]
            return completion

    def __get_method(self, keys):
        try:
            method = NTCli.cmd_map[keys[0]][keys[1]]
            return method
        except:
            return None, None

    def do_EOF(self, line):
        return True

    def emptyline(self):
        return False

    do_q = do_exit = do_EOF

def shortcut_opts(kv, **remap):
    opts = []
    for k in kv:
        if not k in remap and kv[k]:
            opts.append('-%s %s' % (k[0], kv[k]))
        elif kv[k]:
            opts.append('-%s %s' % (remap[k], kv[k]))
    return ' '.join(opts)


def rollback(rb_func, *params):
    def _rollback1(func):
        def _rollback2(self, *vargs, **kv):
            if not self.rb_enabled:
                return func(self, *vargs, **kv)

            try:
                rb_stack = getattr(self, 'rb_stack')
            except:
                rb_stack = []
                setattr(self, 'rb_stack', rb_stack)

            try:
                all_args = inspect.getcallargs(func, self, *vargs[:], **kv.copy())
                rb_args = dict([(p, all_args[p]) for p in params])
                if not 'self' in rb_args:
                    rb_args['self'] = all_args['self']
                rb_stack.append((rb_func, rb_args))
                return func(self, *vargs, **kv)
            except Exception as e:
                rb_stack.reverse()
                for rb, kv in rb_stack[1:]:
                    rb(**kv)
                raise e

        return _rollback2
    return _rollback1


class SeriesFile:
    def __init__(self, name):
        self.name = name
        self.path = os.path.join('/odsp/config/local', 'series_%s.xml' % name)
        self.mtime = -1

    def content(self):
        mtime = os.path.getmtime(self.path)
        if self.mtime <> mtime:
            self.list = []
            self.mtime = mtime
            node = {}
            for event, elem in iterparse(self.path):
                if '%s_0x' % self.name in elem.tag:
                    node['uuid'] = elem.attrib['uuid']
                    self.list.append(node)
                    node = {}
                else:
                    node[elem.tag] = elem.attrib.copy()
                    if 'name' in elem.attrib:
                        node['name'] = elem.attrib['name']
                elem.clear()
        return self.list

    def getnode(self, name):
        for node in self.content():
            if node.get('name','') == name:
                return node
        raise NodeNotExisted(name)
    
    def getnode_by_uuid(self, uuid):
        for node in self.content():
            if node.get('uuid','') == uuid:
                return node
        raise NodeNotExisted(uuid)

class Port:
    @options()
    def show_ports_cmd(self):
        print "hello"

    @options()
    def show_masks_cmd(self):
        pass

class Host:
    def convert_nickname(self,nickname):
        return '\\"%s\\"'%nickname

    def convert_id(self,id):
        return '\\"%s\\"'%id

    @options(make_opt('nickname',nokey=True),
             make_opt('id'))
    @errmatch(('Initiator name duplicated.', 'Bad parameter(s) were specified. - The host identifier or nickname is already in use, or the host identifier is invalid'))
    def create_host_cmd(self,id,nickname):
        print id
    
    @options(make_opt('id',nokey=True))
    @errmatch(('The client is not existed.', 'The specified host was not found. (%(id)s) - The host was not found.'))
    def delete_host_cmd(self,id):
        pass

    def __mapped(self, op, host):
        init = op.query_initiator(host)
        if not init['clients']: return 'No'
        targets = op.query_target_list(init['clients'][0])
        for target in targets:
            if target['luns']: return 'Yes'
        return 'No'


    @options()
    def show_hosts_cmd(self):
        pass
        

class Disk:
        
    @options()
    def show_disks_cmd(self, name, disks, vdisk):
        pass
        

class Vdisk:
    def mk_attr(**kv):
        return kv

    disk_cnt_limit = mk_attr(
            RAID0  = (2, 16),
            RAID1  = (2, 2),
            RAID5  = (3, 16),
            RAID10 = (4, 16))
    support_raid_lvl = 'RAID0|RAID1|RAID5|RAID10'.split('|')
    support_chunk_size = '16KB|32KB|64KB'.split('|')

    def convert_lvl(lvl):
        if len(lvl) > 6: raise CmdError()
        lvl = re.sub('(r)(\d+)', 'raid\\2', lvl).upper()
        return lvl

    def convert_chunk_size(size):
        return re.sub('k|K', 'KB', size)

    def convert_location(loc):
        return [l.replace('.', ':') for l in loc.split(',')]

    def check_location(loc):
        for l in loc:
            m = re.search('^\d+:\d+:\d+:\d+$', l)
            if not m: raise CmdError()

    @options()
    @errmatch(('The RAID has been existed', 'A duplicate name was specified. (%(name)s) -  Failed to create the vdisk(%(time)s).'))
    def create_vdisk_cmd(self, name, level, disks, chunk_size, spare):
        pass

    @options(make_opt('name', nokey=True))
    @errmatch(('the raid is not existed.', 'The vdisk was not found on this system. (%(name)s) - %(name)s NOT deleted.(%(time)s)'))
    def delete_vdisks_cmd(self, name):
        pass

    @options(make_opt('name', nokey=True, default=''))
    def show_vdisks_cmd(self, name):
        pass


class Sds:
    def osd_df_cmd(self):
        print "osd df"
    def new_tree_cmd(self, a):
        print a
    def test_a_b_cmd(self,b):
        print b

NTCli.register(Port)
NTCli.register(Disk)
NTCli.register(Host)
NTCli.register(Vdisk)
NTCli.register(Sds)


if __name__ == '__main__':

    try:
        write_log('===== ntcli run =====')
        cli = NTCli()
        cli.cmdloop()
    finally:
        write_log('===== ntcli exit =====')
        #log.close()
