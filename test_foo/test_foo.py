"""
example system tests for the foo package
"""

from system_test_machinery import TEST_CASE, IN_DIR, OUT_DIR, make_system_test
import foo.foo

FOO_TESTS = [
    TEST_CASE(
        name="test_foo",
        purpose="example of declarative test thingy",
        arguments={
            '-R' : IN_DIR('some', 'sub', 'path'),
            '-O' : OUT_DIR(),
            '-L' : OUT_DIR('log.txt'),
            '-F' : 'foo',
        },
    ),
    TEST_CASE(
        name="test_barr",
        purpose="yet another example",
        arguments={
            '-a' : IN_DIR('banana'),
            '--flip' : OUT_DIR('magic'),
            '--maybe-represent-argless-flag-like-this' : True,
        },
    ),
]


@make_system_test(FOO_TESTS, foo.foo.main)
def test_foo(output, expected):
    """perform glorious system tests upon the foo package"""
    assert output == expected

