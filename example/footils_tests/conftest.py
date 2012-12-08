"""
special py.test configuration required for system_test_machinery
"""
from system_test_machinery.file_list import FileList, file_list_diff_repr

def pytest_addoption(parser):
    """add command line options to pytest"""
    parser.addoption('--test-data-dir', dest='test_data_dir', metavar='DIR')

def pytest_generate_tests(metafunc):
    """define test_data_dir fixture from command line argument"""
    if 'test_data_dir' in metafunc.fixturenames:
        if metafunc.config.option.test_data_dir:
            metafunc.parametrize('test_data_dir',
                [metafunc.config.option.test_data_dir])

def pytest_assertrepr_compare(op, left, right):
    """define custom output for asserts between system tests FileLists"""
    if (op == '==' and isinstance(left, FileList) and
            isinstance(right, FileList)):
        return file_list_diff_repr(left, right)

