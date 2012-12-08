"""
system test machinery
"""

import functools
import os
import pytest
import itertools
import filecmp


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


def is_handled_expr(known_tags, x):
    """is this an expression we know how to handle?"""
    return isinstance(x, tuple) and len(x) == 3 and x[0] in known_tags


def vmap(f, d):
    """maps over dict values, returning dict"""
    return {k:f(v) for k, v in d.iteritems()}


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

    def expand_dir(dir_name, args, kwargs):
        """expand args as sub-path of bound path for dir_name"""
        return os.path.join(bindings[dir_name], *args)

    eval_in_dir = functools.partial(expand_dir, 'in_dir')
    eval_out_dir = functools.partial(expand_dir, 'out_dir')

    handler = {
        'test_case' : eval_test_case,
        'in_dir' : eval_in_dir,
        'out_dir' : eval_out_dir,
    }

    def _eval(x):
        """evaluate expression or literal"""
        if is_handled_expr(handler, x):
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


def default_resolve_dir(root, name, kind):
    """
    resolves abstract test data paths to concrete paths on filesystem
    
    arguments:
        root : the root path
        name : the name of the test
        kind : either 'input' or 'output_expected'
    return value:
        path to requested test resource (string)
    """
    return os.path.join(str(root), name, kind)

def is_ignored_file(name):
    """ignore this file, even if it is in expected dir?"""
    return name.startswith('.') or name.endswith('~')

def gen_files_inside(root_path):
    """yields relative paths to all files inside root_path"""
    def handle_error(error):
        """raises any filesystem errors when walking over expected files"""
        raise error
    for (dirpath, _, file_names) in os.walk(root_path, onerror=handle_error):
        for name in file_names:
            if is_ignored_file(name):
                continue
            yield os.path.relpath(os.path.join(dirpath, name), root_path)

class FileList(object):
    def __init__(self, test_name, test_purpose, test_args, test_kwargs, dir, files):
        super(FileList, self).__init__()
        self.test_name = test_name
        self.test_purpose = test_purpose
        self.test_args = test_args
        self.test_kwargs = test_kwargs
        self.dir = dir
        self.files = files

    def __eq__(self, right):
        if len(self.files) != len(right.files):
            return False
        else:
            return all(a == b for (a, b) in itertools.izip(self.files, right.files))

def file_list_diff_repr(left, right):
    """custom assert FileList == FileList hook for py.test"""
    lines = [
        '<FileList of output files> == <FileList of expected files>',
        ('system test: %s' % left.test_name),
        ('purpose: %s' % left.test_purpose),
    ]
    if left.test_args:
        lines += ['test args:']
        for arg in left.test_args:
            lines += ['\t%s' % str(arg)]
    if left.test_kwargs:
        lines += ['test kwargs:']
        for (k, v) in sorted(left.test_kwargs.items()):
            lines += ['\t%s = %s' % (str(k), str(v))]

    lines += [
        ('output dir:  "%s"' % left.dir),
        ('expected dir:  "%s"' % right.dir),
    ]
    for left_status, right_status in itertools.izip(left.files, right.files):
        if left_status != right_status:
            lines.append('FILE %s: "%s"' % (left_status[0].upper(),
                left_status[1]))
    return lines

def get_output_and_expected(name, purpose, test_args, test_kwargs, out_dir, expected_dir):
    """compares files, returning output and expected FileList objects"""
    left = []
    right = []
    for rel_file in gen_files_inside(expected_dir):
        out = os.path.join(out_dir, rel_file)
        expected = os.path.join(expected_dir, rel_file)
        assert os.path.exists(expected)
        if os.path.exists(out):
            if filecmp.cmp(out, expected, True):
                left.append(('matches', rel_file))
                right.append(('matches', rel_file))
            else:
                left.append(('differs', rel_file))
                right.append(('expected', rel_file))
        else:
            left.append(('missing', rel_file))
            right.append(('exists', rel_file))

    left_files = FileList(name, purpose, test_args, test_kwargs, out_dir, left)
    right_files = FileList(name, purpose, test_args, test_kwargs, expected_dir, right)
    return left_files, right_files


def compare_test_output(concrete_test_case):
    """compares output files against expected files"""
    _, (resources, test_case), _ = concrete_test_case
    resources = dict(resources)
    test_case = dict(test_case)
    args = tuple(test_case.get('args', ()))
    kwargs = dict(test_case.get('kwargs', ()))

    return get_output_and_expected(
        test_case['name'],
        test_case['purpose'],
        args,
        kwargs,
        resources['out_dir'],
        resources['expected_dir'])


def extract_arguments(concrete_test_case):
    """extract system test arguments from a concrete test case"""
    _, (_, test_case), _ = concrete_test_case
    test_case = dict(test_case)
    args = tuple(test_case.get('args', ()))
    kwargs = dict(test_case.get('kwargs', ()))
    return args, kwargs


def make_concrete_test(test_case, test_data_dir, tmpdir, resolve_dir):
    """build a concrete system test from given test case expression"""
    # unfreeze/unpack test case expr
    _, _, kwargs = test_case
    kwargs = dict(kwargs)
    test_name = kwargs['name']
    # define bindings to concrete paths obtained from pytest
    bindings = {
        'in_dir' : resolve_dir(test_data_dir, 'input', test_name),
        'expected_dir' : resolve_dir(test_data_dir, 'output_expected',
            test_name),
        'out_dir' : str(tmpdir),
    }
    # evaluate test case expr wrt bindings
    return evaluate_expr(bindings, test_case)


def make_system_test(test_cases, run_system_test, resolve_dir=None):
    """
    Builds system tests that interface with py.test

    arguments:
        test_cases: [TEST_CASE(...), ...]
        resolve_dir : optional function used to obtain input / output_expected dirs
    required pytest fixtures:
        test_data_dir: root directory containing data for system tests
    returns:
        decorator used to decorate system tests

    Example of usage:

    MY_TEST_CASES = [
        TEST_CASE(...),
        ...
    ]

    import foo
    @system_test(MY_TEST_CASES, foo.main)
    def test_foo(output, expected):
        assert output == expected
    """

    #pytest demands tuple'd parameters when using mark.parametrize
    test_cases = [(x, ) for x in test_cases]

    if resolve_dir is None:
        resolve_dir = default_resolve_dir

    def system_test_decorator(system_test):
        """transforms given system test py.test parametrised with test cases"""
        #pylint gets confused and complains that pytest has no mark member
        #pylint: disable=E1101
        @pytest.mark.parametrize(('test_case', ), test_cases)
        @functools.wraps(system_test)
        def system_test_wrapper(test_data_dir, tmpdir, test_case):
            """boilerplate to construct and run system tests"""

            concrete_test_case = make_concrete_test(test_case, test_data_dir,
                tmpdir, resolve_dir)

            args, kwargs = extract_arguments(concrete_test_case)
            run_system_test(*args, **kwargs)

            output, expected = compare_test_output(concrete_test_case)
            system_test(output, expected)

        return system_test_wrapper
    return system_test_decorator


