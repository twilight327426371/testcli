import inspect
import shlex
import logging
from .colors import blue 

_logger = logging.getLogger(__name__)

__all__ = ("options", "make_opt")
class AttrObject(dict):
    def __getattr__(self, attr):
        if attr in self: return self[attr]
        else: return None

class CmdError(Exception):
    def __init__(self, msg=''):
        Exception.__init__(self, msg)

class InvalidParameters(Exception):
    def __init__(self, name, value):
        Exception.__init__(self, 'Invalid parameters.(%s=%s)' % (name, value))
        self.name = name
        self.value = value

def args():
    _args = inspect.getargvalues(inspect.stack()[1][0]).args
    _locals = inspect.getargvalues(inspect.stack()[1][0]).locals
    return dict([(a, _locals[a]) for a in _args if a <> 'self'])

def make_opt(name, default=None, nokey=False, convertor=str, check=None, suggest=None):
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
        _logger.info(tokens)
        _logger.info(opt_desc)
        for o in opt_desc:
            if o.nokey: continue
            tokens, val = get_opt_val(tokens, o.name)
            _logger.info(tokens)
            _logger.info(val)
            if val: 
                opt2val[o.name] = val
                newval = o.convertor(val)
                if o.check: 
                    try:
                        o.check(newval)
                    except:
                        raise InvalidParameters(o.name, val)
                opts[o.argname] = newval
        _logger.info(opts)
        _logger.info(tokens)
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
                            _logger.info("check")
                            try:
                                desc.check(newval)
                            except:
                                raise InvalidParameters(desc.name, val)
                        opts[desc.argname] = newval
                    except Exception as e:
                        if desc.suggest:
                            e.message = e.message + "\n" + blue("\n".join(desc.suggest()))
                        raise e

    def insert_default_opts(opts, opt_desc):
        for desc in opt_desc:
            if not desc.default is None and not desc.name in opts:
                opts[desc.argname] = desc.default

    def _options1(func):
        def _options2(cmd, args):
            _logger.info(cmd)
            _logger.info(type(args))
            _logger.info(args)
            opt2val = {}
            opts, tokens = get_opts(args, opt_desc, opt2val)
            check_undefault_opts(opts, opt_desc)
            insert_nokey_opts(tokens, opts, opt_desc, opt2val)
            insert_default_opts(opts, opt_desc)
            try:
                _logger.info(opts)
                ret = func(cmd, **opts)
            except InvalidParameters as e:
                if not e.value:
                    raise InvalidParameters(e.name, opt2val[e.name])
                raise e

            if ret is None: return '', ''
            else: return ret
        return _options2
    return _options1
