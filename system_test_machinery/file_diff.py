"""briefly explain differences between files"""


import difflib

def is_probably_binary(file_name):
    """ref: http://stackoverflow.com/questions/898669/ """
    block_size = 1024
    with open(file_name, 'rb') as f:
        block = f.read(block_size)
        while block == block_size:
            if '\0' in block:
                return True
            block = f.read(block_size)
    return False


def explain_difference(left, right):
    """return a few lines giving a short explaination of difference"""
    bin_left = is_probably_binary(left)
    bin_right = is_probably_binary(right)
    if bin_left and bin_right:
        return ['binary files differ']
    elif bin_left:
        return ['left file is binary, right file is text']
    elif bin_right:
        return ['left file is text, right file is binary']
    else:
        return list(gen_unified_diff_snippet(left, right, 1, 10))


def gen_unified_diff_snippet(left_name, right_name, context_lines, max_lines):
    """yields truncated headerless unified diff of given files"""
    with open(left_name, 'r') as f:
        left = f.readlines()
    with open(right_name, 'r') as f:
        right = f.readlines()

    unified_diff_lines = difflib.unified_diff(left, right, left_name,
        right_name, n=context_lines)
    for i, line in enumerate(unified_diff_lines):
        if i < 2:
            continue # skip header
        if i > max_lines + 2:
            break
        yield line

