
SYMBOL_FILE = 'mks937bHcg-symbol.edl'
NEW_SYMBOL_FILE = 'mks937bHcg-symbol2.edl'

GROUP_HEADER = 'object activeGroupClass'
GROUP_START = 'beginGroup'
GROUP_END = 'endGroup'

groups = []
current_group = []

def detect_group(group):
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
                print "xline:", line
                val = line.split()[1]
                new_val = int(val) + x_move
                new_group.append(line.replace(val, str(new_val)))
                print "new xline:", line.replace(val, str(new_val))
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

with open(SYMBOL_FILE) as f:

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



print len(groups)
x, y, width, height = detect_group(groups[0])

start_x = 0

moved_groups = []

for group in groups:
    x, y, h, w = detect_group(group)
    assert w == width
    assert h == height
    moved_groups.append(move_group(group, start_x - x, 0 - y))
    start_x += width

print len(moved_groups)
for line in moved_groups[0]:
    print line

i = 0
new_file = []

with open(SYMBOL_FILE) as f:

    in_group = False
    new_file = []

    for line in f:
        if line.strip() == GROUP_HEADER:
            in_group = True
            new_file.extend(moved_groups[i])
            i += 1
        elif line.strip() == GROUP_END:
            in_group = False
            groups.append(current_group)
            current_group = []

        if not in_group:
            new_file.append(line)

print len(new_file)

with open(NEW_SYMBOL_FILE, 'w') as f:
    for line in new_file:
        f.write(line)


