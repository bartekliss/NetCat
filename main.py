import argparse
import socket
import subprocess
import sys
import textwrap
import threading

class NetCat:
    def __init__(self, args):
        self.args = args
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        self.socket.connect((self.args.target, self.args.port))
        if self.args.buffer:
            self.socket.sendall(self.args.buffer)

        try:
            while True:
                response = self.socket.recv(4096)
                if not response:
                    break
                print(response.decode(), end='')
                cmd = input('> ')
                self.socket.sendall(cmd.encode())
        except KeyboardInterrupt:
            print("Operacja przerwana przez użytkownika")
        finally:
            self.socket.close()

    def listen(self):
        print("Nasłuchiwanie")
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)

        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()

    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.sendall(output.encode())

        elif self.args.upload:
            with open(self.args.upload, 'rb') as f:
                file_data = f.read()
            client_socket.sendall(file_data)

        elif self.args.command:
            while True:
                client_socket.send(b' #> ')
                cmd_buffer = b''
                while True:
                    data = client_socket.recv(64)
                    if not data:
                        break
                    cmd_buffer += data
                response = execute(cmd_buffer.decode())
                client_socket.sendall(response.encode())

def execute(cmd):
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return output
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Narzędzie BHP')
    parser.add_argument('-c', '--command', action='store_true', help='otwarcie powłoki')
    parser.add_argument('-e', '--execute', help='wykonanie polecenia')
    parser.add_argument('-l', '--listen', action='store_true', help='nasłuchiwanie')
    parser.add_argument('-p', '--port', type=int, default=5555, help='docelowy port')
    parser.add_argument('-t', '--target', default='192.168.1.203', help='docelowy adres IP')
    parser.add_argument('-u', '--upload', help='załadowanie pliku')
    parser.add_argument('-b', '--buffer', help='dane do wysłania', default=None)
    
    args = parser.parse_args()

    if not (args.listen or args.buffer):
        print("Proszę podać dane do wysłania lub uruchomić w trybie nasłuchiwania.")
        sys.exit(1)

    nc = NetCat(args)
    nc.run()
