import numpy as np

block_rgb_lookup = {
    "grass" : (35, 217, 72, 255),
    "dirt" : (136, 40, 84, 255),
}

block_id_lookup = {
    35 : ("m.Grass.ID", None, 2),
    136 : ("m.Dirt.ID", 1, 1),
}

pixel = (35, 217, 72, 255)
print("original pixel:", pixel)

# get available rgb values
values = block_rgb_lookup.values()

if pixel not in values:
    print("ist nicht drin")

# calculate the difference of the pixel to each key
diff = []
for i in range(0, len(values)):
    d = np.subtract(values[i],pixel)
    sum = abs(np.sum(d[0:]))
    diff.append(sum)

# determine the lowest residual value
minval = min(diff)

# get index of the diff array and set new pixel value
for index in range(0, len(diff)):
    if diff[index] == minval:
        pixel = values[index][0]
        break

print("new pixel:", pixel)

block = block_id_lookup[pixel]

print("Following block has been determined the most probable", block)