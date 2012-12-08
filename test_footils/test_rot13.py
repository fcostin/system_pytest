"""
example system tests for the footils.rot13 module
"""

from system_test_machinery import TEST_CASE, IN_DIR, OUT_DIR, make_system_test
import footils.rot13

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


@make_system_test(ROT13_TESTS, footils.rot13.main)
def test_footils_rot13(output, expected):
    """run all footils.rot13 system tests"""
    assert output == expected

