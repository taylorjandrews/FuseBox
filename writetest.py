import tempfile
import os
import sys
import random
from encryptor import encrypt, decrypt

def test1(correct_output, offset=0):
    fd, temp_path = tempfile.mkstemp()
    os.remove(temp_path)
    fh = os.fdopen(fd, 'w+')

    uuid = 0
    server = "server"

    encrypt(correct_output, 0, fh, uuid, server)
    fh.seek(0, os.SEEK_END)
    enc_len = fh.tell()
    fh.seek(0, os.SEEK_SET)
    dec = decrypt(fh.read(enc_len), 0, True, uuid, server)

    if (dec != correct_output):
        sys.exit(1)

def test2(correct_output, offset=0):
    fd, temp_path = tempfile.mkstemp()
    os.remove(temp_path)
    fh = os.fdopen(fd, 'w+')

    uuid = 0
    server = "server"

    encrypt(correct_output, 0, fh, uuid, server)
    fh.seek(0, os.SEEK_END)
    enc_len = fh.tell()
    fh.seek(0, os.SEEK_SET)
    dec = decrypt(fh.read(enc_len), 0, True, uuid, server)

    if (dec != correct_output):
        sys.exit(1)

def main():
    correct_output = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur nec urna lacus. Maecenas venenatis est sit amet leo fringilla varius vel sed massa. Sed fermentum egestas dapibus. Fusce consequat laoreet auctor. Duis commodo arcu massa, sit amet tincidunt neque mollis vitae. Nam ut dignissim odio. In eu fringilla libero, quis dignissim neque. Nullam sagittis, augue a interdum commodo, urna mauris molestie odio, at dapibus purus sapien in risus. Fusce consequat lobortis justo eget convallis. Fusce porttitor et erat eu sollicitudin. Suspendisse ornare gravida velit. Aenean lacus tellus, pulvinar quis metus eu, molestie euismod dui. Cras consequat ullamcorper libero sed dignissim. Quisque posuere efficitur tempor. Sed non pellentesque eros, a efficitur tellus. Suspendisse sollicitudin ante ut purus pretium lobortis. Sed placerat tempus neque, eget hendrerit velit finibus et. In tristique, ligula vel commodo convallis, sapien sapien posuere enim, eget ultricies nisi felis eu neque. Phasellus id facilisis ipsum, ut dictum nulla. Curabitur ornare ultricies ultrices. Integer dignissim augue ut libero mattis consequat. Aenean elementum risus sem, sit amet pharetra nisl egestas nec. Donec eget felis sapien. Pellentesque cursus efficitur sem id auctor. In ut nisl ut nibh eleifend suscipit. Donec viverra dapibus vestibulum. Aliquam egestas nunc turpis, nec commodo diam blandit dignissim. Pellentesque ut arcu eleifend, feugiat purus id, lacinia lectus. Integer scelerisque eros in dolor ullamcorper eleifend. Aenean a elit et erat rhoncus laoreet feugiat a erat. Integer tincidunt ac purus eget accumsan. Interdum et malesuada fames ac ante ipsum primis in faucibus. Mauris imperdiet in magna eu eleifend. In ipsum quam, tempor suscipit ligula a, placerat scelerisque massa. Fusce rutrum quis orci non sodales. Aenean dapibus dolor in massa semper sodales. Curabitur a varius odio. Aenean luctus ut ante ut elementum. Nullam placerat felis at nulla blandit, ut varius magna rhoncus. Aliquam vulputate nisi vitae sem sagittis interdum. In molestie, arcu non malesuada commodo, ex mi placerat justo, eget consequat ipsum risus vel ligula. Aenean dignissim fermentum congue. Ut viverra elementum commodo. Fusce ac orci ut diam scelerisque feugiat. Pellentesque sed risus et ipsum mattis scelerisque eget vel odio. Sed porta, risus vel tincidunt semper, mauris tortor ornare nulla, nec semper tellus est ultrices erat. Integer et nibh at quam varius venenatis. Vivamus fringilla ex in est ornare consectetur. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. In eros diam, sagittis quis nisl eget, dapibus dapibus ante. Donec sit amet dolor egestas, tempus purus vitae, ultrices lectus. Nam semper, ante id dignissim facilisis, ante libero ultrices nisl, sit amet ornare neque metus non ante. Donec sodales lectus lectus, eget vulputate leo suscipit vel. Proin feugiat erat ut libero fringilla, sagittis feugiat mauris ornare. Etiam metus sem, lacinia sit amet diam sed, laoreet posuere lacus. Morbi sollicitudin congue nibh sit amet porta. Proin vehicula congue neque, a tincidunt enim. Duis auctor neque diam, eget lobortis dolor volutpat vel. Nulla tempor ipsum non neque ultricies vestibulum."
       
    test1(correct_output, 0)
    test1(correct_output, random.randint(1, len(correct_output)))

    return 0

if __name__ == '__main__':
    main()
