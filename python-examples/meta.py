import json

f = open("t.txt", 'rb+')

decoder = json.JSONDecoder()

def get_decoded_and_remainder(input_data):
    obj, end = decoder.raw_decode(input_data)
    remaining = input_data[end:]
    return (obj, end, remaining)

encoded_object = '[{"padding_size": 13, "uuid": 10000, "server": 4}]'
extra_text = "This text is not JSON."

f.seek(0)

print 'JSON first:'
metadata, metasize, dataobj = get_decoded_and_remainder(f.read())
filedata = repr(dataobj)
print 'Object              :', metadata
print 'End of parsed input :', metasize
print 'Remaining text      :', filedata

m = json.loads(json.dumps(metadata[0]))
m["padding_size"] = 10

metadata[0] = m

f.seek(0)
f.write(json.dumps(metadata))
f.write(filedata[1:-1])

f.close()
