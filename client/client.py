import sys
import socket
import json
import logging
import ssl
import os
from bs4 import BeautifulSoup
from lxml import html, etree

import gzip

BUFFER_SIZE=1

def make_socket(destination_address='localhost',port=12000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")

def make_secure_socket(destination_address='localhost',port=10000):
    try:
        #get it from https://curl.se/docs/caextract.html
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        secure_socket = ssl.wrap_socket(sock, keyfile=None, certfile=None, server_side=False, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")


def send_command(server, command_str, is_secure=False):
    global BUFFER_SIZE
    BUFFER_SIZE=1
    # Get Request Path
    request_path=command_str.split("\r\n")[0].split("GET")[1].split("HTTP")[0].strip()
    print("request_path", request_path)

    headers = ""
    content_encoded = b""
    content = ""
    content_encoding="utf-8"
    content_length=-1
    content_type="text/html"

    bytes_received=0
    headers_complete=False

    alamat_server = server[0]
    port_server = server[1]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # gunakan fungsi diatas
    if is_secure == True:
        sock = make_secure_socket(alamat_server,port_server)
    else:
        sock = make_socket(alamat_server,port_server)

    try:
        logging.warning(f"sending data ")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received="" #empty string
        while True:
            #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(BUFFER_SIZE)
            if data:
                # Special handling for Downloadable Content
                if "html" not in content_type:
                    bytes_received += len(data)
                    print(f"[!] Bytes Received {bytes_received}/{content_length}")

                    save_file_name = request_path.split("/")[-1]
                    f = open(save_file_name, "ab")
                    f.write(data)
                    f.close()

                    if bytes_received == content_length:
                        content = f""
                        break
                    continue

                #data is not empty, concat with previous content
                # print(data)
                
                if not headers_complete: # alias headers belum selesai dibaca
                    headers += data.decode()
                else: # encode datanya pakai encoding dari headers
                    bytes_received += 1

                    if content_encoding == "utf-8":
                        content += data.decode()
                    else:
                        content_encoded = b"%b%b" % (content_encoded, data)

                if "\r\n\r\n" in headers and not headers_complete:
                    logging.warning("HEADER COMPLETED")
                    print(headers)
                    headers_complete = True

                    # read content-encoding and content-length
                    for head in headers.split("\r\n"):
                        if "Content-Encoding:" in head:
                            content_encoding = head.split("Content-Encoding: ")[1]
                        if "Content-Length:" in head:
                            content_length = int(head.split("Content-Length: ")[1])
                        if "Content-Type:" in head:
                            content_type = head.split("Content-Type: ")[1].strip()
                    
                    logging.warning(f"Content-Encoding: {content_encoding}")
                    logging.warning(f"Content-Length: {content_length}")
                    logging.warning(f"Content-Type: {content_type}")
                    
                    if "html" not in content_type:
                        print("It is downloadable file")
                        # It is downloadable file, delete the file first,
                        BUFFER_SIZE=1024*10
                        print("OK")
                        try:
                            save_file_name = request_path.split("/")[-1]
                            os.remove(save_file_name)
                        except:
                            None

                # logging.warning(f"bytes_received = {bytes_received} | content_length = {content_length}")
                if bytes_received == content_length:
                    if content_encoding == "gzip":
                        content = gzip.decompress(content_encoded).decode()
                    elif content_encoding == "utf-8":
                        None
                    else:
                        content = "[Downloadable Content!]"
                    break
            else:
                print("No More Data Received")
                # no more data, stop the process by break
                break
        
        logging.warning("data receive is done~")
        # print(content)
        return headers, content
    except Exception as ee:
        logging.warning(f"error during data receiving {str(ee)}")
        return False

def create_request_headers(req_str):
    # Generate request based on HTTP protocol
    data = ""
    for head in request_headers.split("\n"):
        if head != "":
            data += f"{head}\r\n"

    data += "\r\n"
    return data

#
# START
#

try:
    while True:
        print("[!] Where to?: http://192.168.167.6/", end="")
        dest = input()
        request_headers = f"""
GET /{dest} HTTP/1.1
Host: 192.168.167.6
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36
"""
        # BUFFER_SIZE=1
        headers, content = send_command(("192.168.167.6", 8000), create_request_headers(request_headers), False)
        print()
        print(headers)
        soup = BeautifulSoup(content, "html.parser")
        html_text = soup.get_text()
        print(html_text)
        
except KeyboardInterrupt:
    server_socket.close()
    sys.exit(0)