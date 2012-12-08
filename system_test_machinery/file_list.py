"""
compare and pretty-print file differences in py.test failures
"""

import os
import filecmp
import itertools

from system_test_machinery import file_diff


class FileList(object):
    """
    Represents a list of diff'd files from system test, along with system test data.

    Exists purely to obtain custom human-readable py.test output for failed system tests.
    """
    def __init__(self, test_name, test_purpose, test_args, test_kwargs,
            root_dir, files):
        super(FileList, self).__init__()
        self.test_name = test_name
        self.test_purpose = test_purpose
        self.test_args = test_args
        self.test_kwargs = test_kwargs
        self.root_dir = root_dir
        self.files = files

    def __eq__(self, right):
        if len(self.files) != len(right.files):
            return False
        else:
            return all(a == b for (a, b) in itertools.izip(self.files,
                right.files))


def get_output_and_expected(name, purpose, test_args, test_kwargs, out_dir,
        expected_dir):
    """compares files, returning output and expected FileList objects"""
    left = []
    right = []
    for rel_file in gen_files_inside(expected_dir):
        out = os.path.join(out_dir, rel_file)
        expected = os.path.join(expected_dir, rel_file)
        assert os.path.exists(expected)
        if os.path.exists(out):
            if filecmp.cmp(out, expected, True):
                left.append(('matches', rel_file))
                right.append(('matches', rel_file))
            else:
                diff = file_diff.explain_difference(out, expected)
                left.append(('differs', rel_file, diff))
                right.append(('expected', rel_file))
        else:
            left.append(('missing', rel_file))
            right.append(('exists', rel_file))

    if not right:
        raise RuntimeError('found no files in expected_dir: %s' % expected_dir)

    left_files = FileList(name, purpose, test_args, test_kwargs,
        out_dir, left)
    right_files = FileList(name, purpose, test_args, test_kwargs,
        expected_dir, right)
    return left_files, right_files


def file_list_diff_repr(left, right):
    """custom assert FileList == FileList pretty-printing hook for py.test"""
    lines = [
        '<FileList of output files> == <FileList of expected files>',
        ('system test: %s' % left.test_name),
        ('purpose: %s' % left.test_purpose),
    ]
    if left.test_args:
        lines += ['test args:']
        for arg in left.test_args:
            lines += ['\t%s' % str(arg)]
    if left.test_kwargs:
        lines += ['test kwargs:']
        for (k, v) in sorted(left.test_kwargs.items()):
            lines += ['\t%s = %s' % (str(k), str(v))]

    lines += [
        ('output dir:  "%s"' % left.root_dir),
        ('expected dir:  "%s"' % right.root_dir),
    ]
    for left_status, right_status in itertools.izip(left.files, right.files):
        if left_status != right_status:
            lines.append('FILE %s: "%s"' % (left_status[0].upper(),
                left_status[1]))
            if len(left_status) == 3:
                lines += left_status[2]
    return lines


def is_ignored_file(name):
    """ignore this file, even if it is in expected dir?"""
    return name.startswith('.') or name.endswith('~')


def gen_files_inside(root_path):
    """yields relative paths to all files inside root_path"""
    def handle_error(error):
        """raises any filesystem errors when walking over expected files"""
        raise error
    for (dirpath, _, file_names) in os.walk(root_path, onerror=handle_error):
        for name in file_names:
            if is_ignored_file(name):
                continue
            yield os.path.relpath(os.path.join(dirpath, name), root_path)

