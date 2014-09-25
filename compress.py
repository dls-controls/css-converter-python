import sys

GROUP_HEADER = 'object activeGroupClass'
GROUP_START = 'beginGroup'
GROUP_END = 'endGroup'


def find_groups(filename):
    groups = []
    current_group = []
    with open(filename) as f:

        in_group = False

        for line in f:
            if line.strip() == GROUP_HEADER:
                in_group = True
            elif line.strip() == GROUP_END:
                in_group = False
                groups.append(current_group)
                current_group = []

            if in_group:
                current_group.append(line)

    return groups


def locate_group(group):
    for line in group:
        if line.startswith('x'):
            x = int(line.split()[1])
        elif line.startswith('y'):
            y = int(line.split()[1])
        elif line.startswith('w'):
            w = int(line.split()[1])
        elif line.startswith('h'):
            h = int(line.split()[1])
        elif line.strip() == GROUP_START:
            break
    for line in group:
        if line.startswith('y'):
            y = int(line.split()[1])
            break

    return x, y, w, h
    return x, y, w+1, h+1  # Account for border width

def move_group(group, x_move, y_move):
    new_group = []
    in_x = False
    in_y = False
    for line in group:
        if line.startswith('x '):
            new_val = int(line.split()[1]) + x_move
            new_group.append('x %s\n' % new_val)
        elif line.startswith('y '):
            new_val = int(line.split()[1]) + y_move
            new_group.append('y %s\n' % new_val)
        elif line.startswith('xPoints'):
            in_x = True
            new_group.append(line)
        elif in_x:
            if line.strip().endswith('}'):
                in_x = False
                new_group.append(line)
            else:
                val = line.split()[1]
                new_val = int(val) + x_move
                new_group.append(line.replace(val, str(new_val)))
        elif line.startswith('yPoints'):
            in_y = True
            new_group.append(line)
        elif in_y:
            if line.strip().endswith('}'):
                in_y = False
                new_group.append(line)
            else:
                val = line.split()[1]
                new_val = int(val) + y_move
                new_group.append(line.replace(val, str(new_val)))
        else:
            new_group.append(line)
    return new_group


def new_name(filename, width):
    '''
    Just append the pixel width of each symbol.
    '''
    parts = filename.split('.')
    return '.'.join(parts[:-1]) + '-' + str(width) + '.' + parts[-1]


def find_groups(filename):
    groups = []
    current_group = []
    with open(filename) as f:

        in_group = False

        for line in f:
            if line.strip() == GROUP_HEADER:
                in_group = True
            elif line.strip() == GROUP_END:
                in_group = False
                groups.append(current_group)
                current_group = []

            if in_group:
                current_group.append(line)

    return groups


if __name__ == '__main__':
    if not len(sys.argv) == 2:
        print "Usage: %s <symbol-file>" % sys.argv[0]
        sys.exit()

    filename = sys.argv[1]
    groups = find_groups(filename)

    print 'Found %s symbols.' % len(groups)
    x, y, width, height = locate_group(groups[0])

    # We'll later resize to the exact size
    total_height = height
    total_width = width * len(groups)

    # Move each group's top left to width*i, 0
    start_x = 0
    moved_groups = []

    for group in groups:
        x, y, w, h = locate_group(group)
        assert w == width
        assert h == height
        moved_groups.append(move_group(group, start_x - x, 0 - y))
        start_x += width

    # Create new file by passing through every line
    i = 0
    new_file = []
    changed_height = False
    changed_width = False

    with open(filename) as f:
        in_group = False
        new_file = []

        for line in f:
            # Replace first instance of height with revised version
            if not changed_height and line.split()[0] == 'h':
                new_file.append('h %s\n' % total_height)
                changed_height = True
                continue
            # Replace first instance of width with revised version
            if not changed_width and line.split()[0] == 'w':
                new_file.append('w %s\n' % total_width)
                changed_width = True
                continue
            # if in a group, replace it with the moved group
            if line.strip() == GROUP_HEADER:
                in_group = True
                new_file.extend(moved_groups[i])
                i += 1
            elif line.strip() == GROUP_END:
                in_group = False

            if not in_group:
                new_file.append(line)

    print 'New file length: %s' % len(new_file)

    new_filename = new_name(filename, width)
    # Write out the new file
    with open(new_filename, 'w') as f:
        for line in new_file:
            f.write(line)

    print 'Wrote new EDM symbol to %s' % new_filename

