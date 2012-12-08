"""
system test case expression machinery
"""

import functools
import os

def make_expr(tag, *args, **kwargs):
    """build expression of form (tag, args, kwargs)"""
    # We want to be able to use EXPRs as parameters to pytest test cases.
    # For some pytest internal reason this means we need to be able to hash
    # them. So, we turn all collections into frozen representations.
    return (tag, deep_freeze(args), deep_freeze(kwargs))


TEST_CASE = functools.partial(make_expr, 'test_case')
IN_DIR = functools.partial(make_expr, 'in_dir')
OUT_DIR = functools.partial(make_expr, 'out_dir')
CONCRETE_TEST_CASE = functools.partial(make_expr, 'concrete_test_case')


def evaluate_expr(bindings, root_expr):
    """evaluate TEST_CASE wrt given bindings, returning a CONCRETE_TEST_CASE"""

    def eval_test_case(_, test_case):
        """evaluate args of test case and return concrete test case"""
        test_case = dict(test_case)
        args = tuple(test_case.get('args', ()))
        kwargs = dict(test_case.get('kwargs', {}))
        test_case['args'] = map(_eval, args)
        test_case['kwargs'] = vmap(_eval, kwargs)

        test_resources = {
            'in_dir' : bindings['in_dir'],
            'out_dir' : bindings['out_dir'],
            'expected_dir' : bindings['expected_dir'],
        }
        return CONCRETE_TEST_CASE(test_resources, test_case)

    def expand_dir(dir_name, args, _):
        """expand args as sub-path of bound path for dir_name"""
        return os.path.join(bindings[dir_name], *args)

    eval_in_dir = functools.partial(expand_dir, 'in_dir')
    eval_out_dir = functools.partial(expand_dir, 'out_dir')

    handler = {
        'test_case' : eval_test_case,
        'in_dir' : eval_in_dir,
        'out_dir' : eval_out_dir,
    }

    def is_handled_expr(x):
        """is this an expression we know how to handle?"""
        return isinstance(x, tuple) and len(x) == 3 and x[0] in handler

    def _eval(x):
        """evaluate expression or literal"""
        if is_handled_expr(x):
            tag, args, kwargs = x
            return handler[tag](args, kwargs)
        else:
            if isinstance(x, tuple):
                return tuple(_eval(y) for y in x)
            elif isinstance(x, list):
                # nb intentionally freeze lists as tuples
                return tuple(_eval(y) for y in x)
            else:
                return x

    return _eval(root_expr)


def extract_arguments(concrete_test_case):
    """extract system test arguments from a concrete test case"""
    _, (_, test_case), _ = concrete_test_case
    test_case = dict(test_case)
    args = tuple(test_case.get('args', ()))
    kwargs = dict(test_case.get('kwargs', ()))
    return args, kwargs


def extract_test_case_data(test_case):
    """extract data from a test case"""
    _, _, kwargs = test_case
    kwargs = dict(kwargs)
    return kwargs


def deep_freeze(x):
    """return frozen deep copy of x"""
    if isinstance(x, dict):
        return tuple((deep_freeze(k), deep_freeze(v)) for (k, v) in
            x.iteritems())
    elif isinstance(x, list):
        return tuple(deep_freeze(v) for v in x)
    elif isinstance(x, set):
        return frozenset(deep_freeze(v) for v in x)
    else:
        return x


def vmap(f, d):
    """maps over dict values, returning dict"""
    return {k:f(v) for k, v in d.iteritems()}

