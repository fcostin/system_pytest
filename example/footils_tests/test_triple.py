"""
example system tests for the footils.triple module
"""

from system_test_machinery import TEST_CASE, IN_DIR, OUT_DIR, make_system_test
import footils.triple
import os.path

TRIPLE_TESTS = [
    TEST_CASE(
        name="test1_hello_this_is_dog",
        purpose="test that triple writes three exact copies of its input",
        kwargs={
            'in_file' : IN_DIR('hello.txt'),
            'out_dir' : OUT_DIR(),
        }
    ),
]

def resolve_dir_triple(root, kind, test_name):
    # nb kind is either 'input' or 'output_expected'
    return os.path.join(root, 'triple_tests', kind, test_name)

@make_system_test(TRIPLE_TESTS, footils.triple.main, resolve_dir_triple)
def test_footils_triple(output, expected):
    """run all triple system tests"""
    assert output == expected

