from system_test_machinery import FileList, file_list_diff_repr

def pytest_addoption(parser):
    parser.addoption('--test-data-dir', dest='test_data_dir', metavar='DIR')

def pytest_generate_tests(metafunc):
    if 'test_data_dir' in metafunc.fixturenames:
        if metafunc.config.option.test_data_dir:
            metafunc.parametrize('test_data_dir', [metafunc.config.option.test_data_dir])

def pytest_assertrepr_compare(op, left, right):
    if op == '==' and isinstance(left, FileList) and isinstance(right, FileList):
        return file_list_diff_repr(left, right)

