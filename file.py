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
    headers = ""
    content_encoded = b""
    content = ""
    content_encoding="utf-8"
    content_length=-1

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
                    headers_complete = True

                    # read content-encoding and content-length
                    for head in headers.split("\r\n"):
                        if "Content-Encoding:" in head:
                            content_encoding = head.split("Content-Encoding: ")[1]
                        if "Content-Length:" in head:
                            content_length = int(head.split("Content-Length: ")[1])
                    
                    logging.warning(f"Content-Encoding: {content_encoding}")
                    logging.warning(f"Content-Length: {content_length}")

                # logging.warning(f"bytes_received = {bytes_received} | content_length = {content_length}")
                if bytes_received == content_length:
                    if content_encoding == "gzip":
                        content = gzip.decompress(content_encoded).decode()
                    
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

request_headers = """
GET / HTTP/1.1
Host: www.its.ac.id
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
"""

headers, content = send_command(("www.its.ac.id", 443), create_request_headers(request_headers), True)
print()
print(headers)

# SOAL 1-3
for head in headers.split("\r\n"):
    if "HTTP" in head:
        http_version = head.split(" ")[0]
        http_status_code = head.split(http_version)[1].strip()
        
    if "Content-Encoding:" in head:
        content_encoding = head.split("Content-Encoding: ")[1]

# 1. Cetaklah status code dan deskripsinya dari HTTP response header
print(f"1. Status Code\t\t| {http_status_code}")

# 2. Cetaklah versi Content-Encoding dari HTTP response header
print(f"2. Content-Encoding\t| {content_encoding}")

# 3. Cetaklah versi HTTP dari HTTP response header
print(f"3. HTTP Version\t\t| {http_version}")

print()

#
# Request ke classroom.its.ac.id
#

request_headers = """
GET / HTTP/1.1
Host: classroom.its.ac.id
Connection: keep-alive
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Referer: https://classroom.its.ac.id/my/
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
"""

headers, content = send_command(("classroom.its.ac.id", 443), create_request_headers(request_headers), True)
print()
print(headers)

# 4. Cetaklah property charset pada Content-Type dari HTTP response header pada halaman classroom.its.ac.id
for head in headers.split("\r\n"):        
    if "Content-Type:" in head:
        content_type = head.split("Content-Type: ")[1]
        charset = content_type.split("charset=")[1]

# Cetak
print(f"4. Charset\t\t| {charset}")


# 5. 

# soup = BeautifulSoup(content, "html.parser")
# html_text = soup.get_text()

print("5. Dapatkanlah daftar menu pada halaman utama classroom.its.ac.id dengan melakukan parsing HTML")
# Print biar lebih rapi

def get_all_texts(els, class_name):
    return [e.text_content() for e in els.find_class(class_name)]

root = html.fromstring(content)
mainmenu_texts = get_all_texts(root, "navbar-nav h-100 wdm-custom-menus links")

html_text = "".join(mainmenu_texts)
print(html_text)
    
# for i in range(len(html_text)):
#     if i>0:
#         if html_text[i] == "\n" and html_text[i-1] == "\n":
#             None # dont print
#         else:
#             print(html_text[i], end="")
#     else:
#         print(html_text[i], end="")

# mainmenu = root.xpath('//ul[@class="navbar-nav h-100 wdm-custom-menus links"]')
# print(etree.tostring(mainmenu))
