system\_pytest
==============

grafts diff-against-expected-output style system test support onto `py.test`

purpose
-------

We want to easily write system tests that

1.  run python scripts that accept input parameters (including input files) and write output files
2.  collect the resulting output files in temporary directories
3.  diff the output against specified expected output files
4.  trigger test failures if output files differ from the expected output

We want to run our system tests using `py.test` in order to

1.  measure coverage of our system tests via the `coverage` plugin
2.  measure combined system + unit test coverage by running all our tests with a single `py.test` invocation

We want to avoid

1.  writing boilerplate when defining tests
2.  hard-coding paths to resources such as input files and expected output files
3.  needless use of the command line to pass arguments to python scripts under test
4.  dirty tricks in order to patch python import paths, working directories, etc.
5.  parsing test configurations / arguments from files

We would also like to

1.  easily swap between testing python functions, and testing command-line executables, using the same test data and parameters
2.  see human-readable messages when the tests fail

an example
----------

Suppose we've written a buggy python package named `footils`. `footils` consists of two command-line scripts, `ehco` and `rot13`.

*   `ehco` is kind of like a file-based `echo`. Unfortunately, `ehco` replaces `'ch'` with `'hc'` when writing output.
*   `rot13` is a file-based `rot13` utility which usually rot13-encodes lines of text.
    Sadly, if a line contains the substring `'13'`, the rest of the line is rotated about the `'13'`.

To test these wonderful scripts, we shall write system tests that

1.  feed the scripts input files
2.  collect the resulting output files in temporary directories
3.  diff the temporary directories against directories containing expected output
4.  trigger test failures if output files differ from the expected output

Here is an example script defining two system tests for the `rot13` script:

#### system test script `test_rot13.py`

    """
    example system tests for the footils.rot13 module
    """

    from system_test_machinery import TEST_CASE, IN_DIR, OUT_DIR, make_system_test
    import footils.rot13
    import os.path

    ROT13_TESTS = [
        TEST_CASE(
            name="test1_hello_world",
            purpose="test that rot13 correctly encodes hello world",
            args=[[IN_DIR('hello.txt'), OUT_DIR('hello.txt')]],
        ),
        TEST_CASE(
            name="test2_numbers",
            purpose="test that rot13 leaves numbers invariant",
            args=[[IN_DIR('numbers.txt'), OUT_DIR('numbers.txt')]],
        ),
    ]

    def resolve_dir_rot13(root, kind, test_name):
        # nb kind is either 'input' or 'output_expected'
        return os.path.join(root, 'rot13_tests', kind, test_name)

    @make_system_test(ROT13_TESTS, footils.rot13.main, resolve_dir_rot13)
    def test_footils_rot13(output, expected):
        """run all footils.rot13 system tests"""
        assert output == expected

#### running the system tests with `py.test`:

Provided the `system_test_machinery` package can be found by python, we can run our `footils` system tests like so:

    py.test --test-data-dir footils_test_data footils_tests/

Note that we explicitly pass the path to the test data directory via the `--test-data-dir` argument to `py.test`.
This is a custom argument to `py.test` that we have defined using a `conftest.py` file inside the `footils_tests` package, which is read by `py.test` (more on this later).

Here is an example of output from `py.test` when one of our system tests fails:

    output = <system_test_machinery.machinery.FileList object at 0x1379a10>, expected = <system_test_machinery.machinery.FileList object at 0x1379890>

        @make_system_test(ROT13_TESTS, footils.rot13.main, resolve_dir_rot13)
        def test_footils_rot13(output, expected):
            """run all footils.rot13 system tests"""
    >       assert output == expected
    E       assert <FileList of output files> == <FileList of expected files>
    E         system test: test2_numbers
    E         purpose: test that rot13 leaves numbers invariant
    E         test args:
    E           ('footils_test_data/rot13_tests/input/test2_numbers/numbers.txt', '/tmp/pytest-239/test_footils_rot13_footils_test_data_test_case1_0/numbers.txt')
    E         output dir:  "/tmp/pytest-239/test_footils_rot13_footils_test_data_test_case1_0"
    E         expected dir:  "footils_test_data/rot13_tests/output_expected/test2_numbers"
    E         FILE DIFFERS: "numbers.txt"

    footils_tests/test_rot13.py:29: AssertionError

#### example `conftest.py` configuration file

    """
    special py.test configuration required for system_test_machinery
    """
    from system_test_machinery.machinery import FileList, file_list_diff_repr

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

#### package layout used for this example

    example
    |-- footils
    |   |-- ehco.py
    |   |-- __init__.py
    |   `-- rot13.py
    |-- footils_test_data
    |   |-- ehco_tests
    |   |   |-- input
    |   |   |   `-- test1
    |   |   |       `-- quote.txt
    |   |   `-- output_expected
    |   |       `-- test1
    |   |           `-- quote.txt
    |   `-- rot13_tests
    |       |-- input
    |       |   |-- test1_hello_world
    |       |   |   `-- hello.txt
    |       |   `-- test2_numbers
    |       |       `-- numbers.txt
    |       `-- output_expected
    |           |-- test1_hello_world
    |           |   `-- hello.txt
    |           `-- test2_numbers
    |               `-- numbers.txt
    |-- footils_tests
    |   |-- conftest.py
    |   |-- __init__.py
    |   |-- test_ehco.py
    |   `-- test_rot13.py
    `-- Makefile

The `footils` package itself lives inside `footils`.
System tests have been placed in `footils_tests`.
Input and expected output files required by the system tests are arranged inside `footils_test_data`.

