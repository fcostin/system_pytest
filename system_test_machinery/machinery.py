"""
system test machinery
"""

import functools
import os
import pytest
from system_test_machinery import file_list, expr


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

            args, kwargs = expr.extract_arguments(concrete_test_case)
            run_system_test(*args, **kwargs)

            output, expected = compare_test_output(concrete_test_case)
            system_test(output, expected)

        return system_test_wrapper
    return system_test_decorator


def default_resolve_dir(root, kind, name):
    """
    resolves abstract test data paths to concrete paths on filesystem
    
    arguments:
        root : the root path
        kind : either 'input' or 'output_expected'
        name : the name of the test
    return value:
        path to requested test resource (string)
    """
    return os.path.join(str(root), kind, name)


def make_concrete_test(test_case, test_data_dir, tmpdir, resolve_dir):
    """build a concrete system test from given test case expression"""
    test_name = expr.extract_test_case_data(test_case)['name']
    # define bindings to concrete paths obtained from pytest
    bindings = {
        'in_dir' : resolve_dir(test_data_dir, 'input', test_name),
        'expected_dir' : resolve_dir(test_data_dir, 'output_expected',
            test_name),
        'out_dir' : str(tmpdir),
    }
    # evaluate test case expr wrt bindings
    return expr.evaluate_expr(bindings, test_case)


def compare_test_output(concrete_test_case):
    """compares output files against expected files"""
    _, (resources, test_case), _ = concrete_test_case
    resources = dict(resources)
    test_case = dict(test_case)
    args = tuple(test_case.get('args', ()))
    kwargs = dict(test_case.get('kwargs', ()))

    return file_list.get_output_and_expected(
        test_case['name'],
        test_case['purpose'],
        args,
        kwargs,
        resources['out_dir'],
        resources['expected_dir'])

