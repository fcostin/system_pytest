"""
example system tests for the footils.ehco module
"""

from system_test_machinery import TEST_CASE, IN_DIR, OUT_DIR, make_system_test
import footils.ehco
import os.path

EHCO_TESTS = [
    TEST_CASE(
        name="test1",
        purpose="test that ehco is able to copy a one-line quote without error",
        kwargs={
            'in_file' : IN_DIR('quote.txt'),
            'out_file' : IN_DIR('quote.txt'),
        }
    ),
]

def resolve_dir_ehco(root, kind, test_name):
    # nb kind is either 'input' or 'output_expected'
    return os.path.join(root, 'ehco_tests', kind, test_name)

@make_system_test(EHCO_TESTS, footils.ehco.main, resolve_dir_ehco)
def test_footils_rot13(output, expected):
    """run all footils.rot13 system tests"""
    assert output == expected

