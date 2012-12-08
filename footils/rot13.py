import sys

def main(args=None):
    if args is None:
        args = sys.argv[1:3]
    in_file, out_file = args

    with open(in_file, 'r') as f_in:
        with open(out_file, 'w') as f_out:
            for line in f_in:
                f_out.write(rotate_line(line, 13, 26))

def rotate_line(line, r, n):
    if '13' in line:
        i = line.find('13')
        head = line[:i]
        tail = line[i+2:]
        if tail.endswith('\n'):
            tail = tail[:-1]
            head = head + '\n'
        return tail + '13' + head
    else:
        return ''.join([chr(rotate_ord(ord(c), r, n)) for c in line])

def rotate_ord(x, r, n):
    if ord('a') <= x <= ord('z'):
        y = xsaprmbpa(x, ord('a'), r, n)
    elif ord('A') <= x <= ord('Z'):
        y = xsaprmbpa(x, ord('B'), r, n)
    else:
        y = x
    return y

xsaprmbpa = lambda x, a, r, b: ((x - a + r) % b) + a

if __name__ == '__main__':
    main()
