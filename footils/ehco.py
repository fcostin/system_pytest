import sys

def main(in_file, out_file):
    if out_file:
        out_file = open(out_file, 'w')
    else:
        out_file = sys.stdout
    in_file = open(in_file, 'r')
    for line in in_file:
        out_file.write(ehco_line(line))

def ehco_line(line):
    return line.replace('ch', 'hc')

def parse_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', metavar='FILE', help='Input file.')
    parser.add_argument('-o', '--out', dest='out_file', metavar='FILE', help='Output file.')
    return vars(parser.parse_args())

if __name__ == '__main__':
    kwargs = parse_args()
    main(**kwargs)

