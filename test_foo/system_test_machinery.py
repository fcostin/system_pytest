"""
system test machinery
"""

import functools
import os
import pytest
import collections
import itertools
import filecmp

def deep_freeze(x):
    if isinstance(x, dict):
        return tuple((deep_freeze(k), deep_freeze(v)) for (k, v) in x.iteritems())
    elif isinstance(x, list):
        return tuple(deep_freeze(v) for v in x)
    elif isinstance(x, set):
        return frozenset(deep_freeze(v) for v in x)
    else:
        return x

def EXPR(_expr_tag, *args, **kwargs):
    # we wanna be able to use EXPRs as parameters to pytest test cases
    # for some pytest internal reason this means we need to be able to hash them
    # so, we turn all collections into frozen representations
    return (_expr_tag, deep_freeze(args), deep_freeze(kwargs))

TEST_CASE = functools.partial(EXPR, 'test_case')
IN_DIR = functools.partial(EXPR, 'in_dir')
OUT_DIR = functools.partial(EXPR, 'out_dir')
CONCRETE_TEST_CASE = functools.partial(EXPR, 'concrete_test_case')

def is_handled_expr(known_tags, x):
    return isinstance(x, tuple) and len(x) == 3 and x[0] in known_tags

def vmap(f, d):
    return {k:f(v) for k, v in d.iteritems()}

def eval_in_context(bindings, root_expr):

    def eval_test_case(args, kwargs):
        test_case = dict(kwargs)
        arguments = dict(test_case.get('arguments', {}))
        test_case['arguments'] = vmap(_eval, arguments)

        test_resources = {
            'in_dir' : bindings['in_dir'],
            'out_dir' : bindings['out_dir'],
            'expected_dir' : bindings['expected_dir'],
        }
        return CONCRETE_TEST_CASE(test_resources, test_case)

    def expand_dir(dir_name, args, kwargs):
        return os.path.join(bindings[dir_name], *args)

    eval_in_dir = functools.partial(expand_dir, 'in_dir')
    eval_out_dir = functools.partial(expand_dir, 'out_dir')

    handler = {
        'test_case' : eval_test_case,
        'in_dir' : eval_in_dir,
        'out_dir' : eval_out_dir,
    }

    def _eval(x):
        if is_handled_expr(handler, x):
            tag, args, kwargs = x
            return handler[tag](args, kwargs)
        else:
            return x

    return _eval(root_expr)


def default_resolve_dir(root, name, kind):
    return os.path.join(str(root), name, kind)

def gen_files_inside(root_path):
    def handle_error(error):
        raise error
    for (dirpath, _, file_names) in os.walk(root_path, onerror=handle_error):
        for name in file_names:
            yield os.path.relpath(os.path.join(dirpath, name), root_path)

FileList = collections.namedtuple('FileList', ['test_name', 'test_purpose',
    'test_arguments', 'dir', 'files'])

def file_list_diff_repr(left, right):
    """custom assert FileList == FileList hook for py.test"""
    lines = [
        '<output files> == <expected files>',
        ('system test: %s' % left.test_name),
        ('purpose: %s' % left.test_purpose),
        'arguments:',
    ]
    for (k, v) in sorted(left.test_arguments.items()):
        lines += ['\t%s = %s' % (str(k), str(v))]

    lines += [
        ('output dir:  "%s"' % left.dir),
        ('expected dir:  "%s"' % right.dir),
    ]
    for left_status, right_status in itertools.izip(left.files, right.files):
        if left_status != right_status:
            lines.append('FILE %s: "%s"' % (left_status[0].upper(), left_status[1]))
    return lines

def get_output_and_expected(name, purpose, test_args, out_dir, expected_dir):
    left = []
    right = []
    for rel_file in gen_files_inside(expected_dir):
        out = os.path.join(out_dir, rel_file)
        expected = os.path.join(expected_dir, rel_file)
        assert os.path.exists(expected)
        if os.path.exists(out):
            if filecmp.cmp(left, right, True):
                left.append(('matches', rel_file))
                right.append(('matches', rel_file))
            else:
                left.append(('differs', rel_file))
                right.append(('expected', rel_file))
        else:
            left.append(('missing', rel_file))
            right.append(('exists', rel_file))

    left_files = FileList(name, purpose, test_args, out_dir, left)
    right_files = FileList(name, purpose, test_args, expected_dir, right)
    return left_files, right_files

def compare_test_output(concrete_test_case):
    _, (resources, test_case), _ = concrete_test_case
    resources = dict(resources)
    test_case = dict(test_case)
    arguments = dict(test_case.get('arguments', ()))

    return get_output_and_expected(
        test_case['name'],
        test_case['purpose'],
        arguments,
        resources['out_dir'],
        resources['expected_dir'])

def extract_arguments(concrete_test_case):
    _, (resources, test_case), _ = concrete_test_case
    resources = dict(resources)
    test_case = dict(test_case)
    return dict(test_case.get('arguments', ()))


def make_concrete_test(test_data_dir, tmpdir, test_case_expr, resolve_dir):
    # -- unfreeze/unpack test case expr
    _, _, kwargs = test_case_expr
    kwargs = dict(kwargs)
    test_name = kwargs['name']
    # -- define bindings to concrete paths obtained from pytest
    bindings = {
        'in_dir' : resolve_dir(test_data_dir, 'input', test_name),
        'expected_dir' : resolve_dir(test_data_dir, 'output_expected', test_name),
        'out_dir' : str(tmpdir),
    }
    # -- evaluate test case expr wrt bindings
    return eval_in_context(bindings, test_case_expr)


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

    test_cases = [(x, ) for x in test_cases]

    if resolve_dir is None:
        resolve_dir = default_resolve_dir

    def system_test_decorator(system_test):
        #pylint gets confused and complains that pytest has no mark member
        #pylint: disable=E1101
        @pytest.mark.parametrize(('test_case_expr', ), test_cases)
        @functools.wraps(system_test)
        def system_test_wrapper(test_data_dir, tmpdir, test_case_expr):

            concrete_test_case = make_concrete_test(test_data_dir, tmpdir,
                test_case_expr, resolve_dir)

            run_system_test(extract_arguments(concrete_test_case))

            output_files, expected_files = compare_test_output(concrete_test_case)
            system_test(output_files, expected_files)

        return system_test_wrapper
    return system_test_decorator


