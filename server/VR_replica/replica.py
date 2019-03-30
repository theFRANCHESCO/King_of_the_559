from enum import Enum
import ipaddress
import asyncio
import socket

class Mode(Enum):
    BACKUP = 0
    PRIMARY = 1

class State(Enum):
    NORMAL = 0
    VIEW_CHANGE = 1
    RECOVERING = 2

class Host():

    def __init__(self, ip_addr):
        self.address = ipaddress.ip_address(ip_addr) 

    def __lt__(self, other):
        return self.address < other.address


class replica:
    
    def __init__(self):
        self.current_mode = Mode.BACKUP
        self.current_state = State.NORMAL
        self.connected_hosts = []
        self.message_out_queue = asyncio.Queue()

        #get Ip of the local computer
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        #s.getsockname() has the local ip address at [0] and the local port at [1]
        self.local_ip = s.getsockname()[0]
        print("IP address: ", self.local_ip)
        s.close()
        self.loop = asyncio.get_event_loop()
        
        self.loop.create_task(self.read_network())
        self.loop.create_task(self.send_message())
        try:
            self.loop.run_forever()
        except:
            self.loop.close()

        #start the server
        # asyncio.run(self.read_network())

    def start_recovery(self):
        self.current_state = State.RECOVERING
        #TODO: run the recovery protocol
        self.current_state = State.NORMAL

    def start_view_change(self):
        self.current_state = State.VIEW_CHANGE
        #TODO: run the view change protocol
        self.current_state = State.NORMAL
    
    #add a new replica with the ip address in form "xxx.xxx.xxx.xxx"
    async def add_new_replica(self, ip_addr):
        self.connected_hosts.append(Host(ip_addr))

    async def add_send_message(self, ipaddr, msg):
        await self.message_out_queue.put((ipaddr, msg))
        await asyncio.sleep(0)
        

    async def send_message(self):
        while True:
            ipaddr, msg = await self.message_out_queue.get()
            reader, writer = await asyncio.open_connection(ipaddr, 9998)
            print(ipaddr)
            # print(msg)
            writer.write(msg.encode())
            writer.write_eof()
            await writer.drain()

    async def parse_message(self, reader, writer):
        msg = await reader.read()
        #parse the message (json) and call the corresponding method to deal with it.
        print(msg.decode())
        await self.message_out_queue.put(("192.168.0.10", msg.decode()))

    async def read_network(self):

        #open socket and wait for connection
        a_server = await asyncio.start_server(self.parse_message, port=9999, start_serving = True)

        

