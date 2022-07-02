#!/usr/bin/env python
"""
Maniuplate Universal rResource Locators (URLs)

Author: Friedrich Schotte
Date created: 2017-12-01
Date last modified: 2019-12-02
"""
__version__ = "1.0"

def url(url,ip_address=None):
    # Disassemble URL
    url_protocol = ''
    if url.startswith("ssl:"): url_protocol = 'ssl'
    if url.startswith("tcp:"): url_protocol = 'tcp'

    if url.startswith(url_protocol+":"): url = url.replace(url_protocol+":","",1)
    if url.startswith("//"): url = url.replace("//","",1)
    if not "@" in url: url = ":@"+url
    url_username_password = url.split("@")[0]
    url_username = url_username_password.split(":")[0]
    url_password = url_username_password.split(":")[-1]
    url = url.split("@")[-1]
    url_ip_address = url.split(":")[0]
    url_port = url.split(":")[1]
   
    if ip_address is not None: url_ip_address = ip_address

    # Reassemble URL
    url = ""
    if url_protocol: url = url_protocol+"://"
    url_username_password = ""
    if url_username: url_username_password = url_username
    if url_password: url_username_password = url_username_password+":"+url_password
    if url_username_password: url += url_username_password+"@"
    url += url_ip_address
    if url_port: url += ":"+url_port

    return url

if __name__ == "__main__":
    print("url('ssl://femto10.niddk.nih.gov:2000',ip_address='pico21.niddk.nih.gov')")
    

    
