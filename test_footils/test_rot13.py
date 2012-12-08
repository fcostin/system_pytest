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

