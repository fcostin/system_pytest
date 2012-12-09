import sys
import os.path

def main(in_file, out_dir):
    with open(in_file, 'r') as f:
        lines = list(f)

    name = os.path.basename(in_file)
    for i in xrange(3):
        out_file = os.path.join(out_dir, '%s.%d' % (name, i))
        with open(out_file, 'w') as f:
            for line in lines:
                f.write(triple_line(line, i))

def triple_line(line, i):
    return ''.join(c*i for c in line)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', metavar='FILE', help='Input file.')
    parser.add_argument('-o', '--out', dest='out_dir', metavar='DIR',
        help='Output dir.', required=True)
    return vars(parser.parse_args())

if __name__ == '__main__':
    kwargs = parse_args()
    main(**kwargs)

