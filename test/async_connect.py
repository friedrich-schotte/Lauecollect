from socket import socket
from select import select
from time import sleep

def test():
    global s
    s=socket()
    s.setblocking(False)
    errno = s.connect_ex(("127.0.0.1",5064))
    sel = select([s],[s],[s],0)
    print errno,sel
    sleep(1)
    print select([s],[s],[s],0)

##>>> test()
##10035 ([], [], [])
##([], [], [<socket._socketobject object at 0x00CCEA08>])
##>>> test()
##10035 ([], [<socket._socketobject object at 0x00CCE9D0>], [])
##([], [<socket._socketobject object at 0x00CCE9D0>], [])
##>>> test()
##10035 ([], [], [])
##([], [], [<socket._socketobject object at 0x00CCEA08>])

if __name__ == "__main__":
    print("test()")
