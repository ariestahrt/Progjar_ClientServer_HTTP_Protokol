import socket
import logging
import os
from os.path import exists
from pathlib import Path
from datetime import datetime
import time
import platform
from _thread import *

BUFFER_SIZE=1

# Read httpserver.conf
CONFIG = {}
ALIAS = {}
MIME = {}

def creation_date(path_to_file):
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            return stat.st_mtime

def return_html(client, header, html_text=""):
    # Create Response
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")         
    
    header += f"\r\n{dt_string}"
    header += f"\r\nContent-Type: text/html; charset=utf-8"
    
    if len(html_text) > 0:
        header += f"\r\nContent-Length: {len(html_text)}"

    response = header + "\r\n\r\n" + html_text + "\r\n\r\n"
    client.sendall(response.encode())

def return_bytes(client, absolute_path):
    # Get Mime Type
    file_type = absolute_path.split(".")[-1]
    mime_type = f"application/{file_type}"
    if file_type in MIME:
        mime_type = MIME[file_type]

    # Create Response
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")         
    
    header = "HTTP/1.1 200 OK"
    header += f"\r\n{dt_string}"
    header += f"\r\nContent-Type: {mime_type}"
    header += f"\r\naccept-ranges: bytes"

    filesize = os.path.getsize(absolute_path)
    header += f"\r\nContent-Length: {filesize}"
    header += "\r\n\r\n"

    client.send(header.encode())
    
    with open(absolute_path, "rb") as f:
        while True:
            # read the bytes from the file
            bytes_read = f.read()
            if not bytes_read:
                break

            # send to client
            client.send(bytes_read)

print("[!] READING HTTPSERVER.CONF")

f = open("httpserver.conf", "r")
for line in f:
    line = line.rstrip()
    if "Listen" in line:
        CONFIG["LISTEN_PORT"] = int(line.split(" ")[1])
    if "ServerRoot" in line:
        CONFIG["SERVER_ROOT"] = line.split(" ")[1].replace('"', '')
    if "ServerName" in line:
        CONFIG["SERVER_NAME"] = line.split(" ")[1]
    if "ServerAdmin" in line:
        CONFIG["SERVER_ADMIN"] = line.split(" ")[1]
    if "ErrorDocument" in line:
        CONFIG["404"] = line.split(" ")[2].replace('"', '')
    if "Alias" in line:
        a_from = line.split(" ")[1].replace('"', '')
        a_to   = line.split(" ")[2].replace('"', '')
        ALIAS[a_from] = a_to
f.close()

print("[!] READING MIME")

f = open("mime.csv", "r")
for line in f:
    line = line.rstrip()
    ext=line.split(";")[0]
    mime_type=line.split(";")[1]
    MIME[ext] = mime_type
f.close()

# print(ALIAS)

# Define socket host and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = CONFIG["LISTEN_PORT"]
ThreadCount = 0

# Create socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)
print('[!] Listening on port %s ...' % SERVER_PORT)

def threaded_socket(client_connection):
    while True:
        # Get the client request
        client_request=""

        while True:
            try:
                request = client_connection.recv(BUFFER_SIZE).decode()
                client_request += request
                if "\r\n\r\n" in client_request:
                    # Done reading client request
                    break
            except Exception as ex:
                None
        print(client_request)

        # Get Request Path
        first_head=client_request.split("\r\n")[0].split(" ")
        request_method, request_path, http_version = first_head[0], first_head[1], first_head[2]
        
        # Check Path Alias
        if request_path in ALIAS:
            request_path = ALIAS[request_path]

        absolute_path = CONFIG["SERVER_ROOT"] + request_path
        print("Absolute path:", absolute_path)

        # Check is path exist?
        if exists(absolute_path):
            if Path(absolute_path).is_file():
                if absolute_path.split(".")[-1] == "html":
                    # return html
                    # read file content

                    f = open(absolute_path, "r")
                    html_text = f.read()
                    f.close()
                    
                    # Return HTML
                    return_html(client_connection, "HTTP/1.1 200 OK", html_text)
                else:
                    # return file bytes
                    return_bytes(client_connection, absolute_path)
                    None
            else:
                # return directory listing as HTML file
                # Get File List in Path
                dir_list = os.listdir(absolute_path)
                
                # Generate HTML Element to Append @ Template
                directory_dom = ""
                for file in dir_list:
                    # check file size and last modified
                    last_modified = time.ctime(creation_date(f"{absolute_path}{file}"))
                    
                    if Path(f"{absolute_path}{file}").is_file():
                        filesize = os.path.getsize(f"{absolute_path}{file}")
                        directory_dom += f"""
                        <tr>
                            <td valign="top"><img src="/icons/text.gif" alt="[TXT]"></td>
                            <td><a href="{file}">{file}</a>   </td>
                            <td align="right">{last_modified}  </td>
                            <td align="right">{filesize} B</td><td>&nbsp;</td>
                        </tr>
                        """
                        None
                    else:
                        directory_dom += f"""
                        <tr>
                            <td valign="top"><img src="/icons/folder.gif" alt="[DIR]"></td>
                            <td><a href="{file}/">{file}/</a>                </td>
                            <td align="right">{last_modified}  </td>
                            <td align="right">  - </td><td>&nbsp;</td>
                        </tr>
                        """

                f = open("template_directory.html", "r")
                html_text = f.read()
                f.close()

                html_text=html_text.replace("==DIRECTORY_NAME==", request_path)
                html_text=html_text.replace("==DIRECTORY_LIST==", directory_dom)
                return_html(client_connection, "HTTP/1.1 200 OK", html_text)
                None
        else:
            # Return 404
            f = open(CONFIG["SERVER_ROOT"] + CONFIG["404"], "r")
            html_text = f.read()
            f.close()
            
            # Return HTML
            return_html(client_connection, "HTTP/1.1 404 Not Found", html_text)
            None

        # Close connection
        client_connection.close()

    # Close socket
    server_socket.close()

try:
    while True:
        # Wait for client connections
        client_connection, client_address = server_socket.accept()
        print(f"[+] New client {client_address} is connected.")
        start_new_thread(threaded_socket, (client_connection, ))
        ThreadCount += 1
        print('[!] Thread Number: ' + str(ThreadCount))
        
except KeyboardInterrupt:
    server_socket.close()
    sys.exit(0)