"""
Platform-independent pathnames
F. Schotte, 28 Mar 2014 - 14 Feb 2017
"""
__version__ = "1.1.6" # "darwin" platform (MacOS)

def normpath(pathname):
    """Translate between UNIX-style to Windows-style pathnames, following
    Universal Naming Convention.
    E.g. "/net/mx340hs/data" to "//mx340hs/data"""
    if pathname == "": return pathname

    from os.path import exists
    pathname = str(pathname)

    # Try to expand a Windows drive letter to a UNC name.
    # E.g. "J:/anfinrud_1106" to "//mx340hs/data/anfinrud_1106"
    try:
        import win32wnet # http://sourceforge.net/projects/pywin32
        pathname = win32wnet.WNetGetUniversalName(pathname)
    except: pass

    # Resolve symbolic links. E.g. "/data" to "/net/mx340hs/data"
    # E.g. "G:/anfinrud_1403/Logfiles" or "\\mx340hs\data\anfinrud_1403\Logfiles"
    import os
    if not pathname[1:2] == ":" and not "\\" in pathname \
       and not pathname.startswith("//") and not os.name == "nt": 
       from os.path import realpath
       pathname = realpath(pathname)

    # Convert separators from Window style to UNIX style.
    # E.g. "\\mx340hs\data\anfinrud_1106" to "//mx340hs/data/anfinrud_1106"  
    pathname = pathname.replace("\\","/")

    # Mac OS X: mount point "/Volumes/share" does not reveal server name. 
    if pathname.startswith("/Volumes/data"):
        pathname = pathname.replace("/Volumes/data","/net/mx340hs/data")
    if pathname.startswith("/Volumes/Femto"):
        pathname = pathname.replace("/Volumes/Femto","/net/femto/C")
    if pathname.startswith("/Volumes/C"):
        pathname = pathname.replace("/Volumes/C","/net/femto/C")

    # Convert from Windows to UNIX style.
    # E.g. "//mx340hs/data/anfinrud_1106" to "/net/mx340hs/data/anfinrud_1106"
    if pathname.startswith("//"): # //server/share/directory/file
        parts = pathname.split("/")
        if len(parts) >= 4:
            server = parts[2] ; share = parts[3]
            path = "/".join(parts[4:])
            if not exists("//"+server+"/"+share):
                if exists("/net/"+server+"/"+share):
                    pathname = "/net/"+server+"/"+share+"/"+path
                if exists("/net/"+server+"/home/"+share):
                    pathname = "/net/"+server+"/home/"+share+"/"+path

    # Convert from UNIX to Windows style.
    # E.g. "/net/mx340hs/data/anfinrud_1106" to "//mx340hs/data/anfinrud_1106"
    from sys import platform
    if pathname.startswith("/net/") and platform in ("win32","darwin"):
        parts = pathname.split("/")
        if len(parts) >= 4:
            server = parts[2] ; share = parts[3]
            path = "/".join(parts[4:])
            # E.g. /net/id14b4/home/useridb/NIH/Software
            if share == "home" and len(parts)>4:
                share = parts[4]
                path = "/".join(parts[5:])
            pathname = "//"+server+"/"+share+"/"+path

    # E.g. "/home/useridb/NIH/Software"
    if not pathname.startswith("//") and pathname.startswith("/") and \
        platform != "win32" and not pathname.startswith("/net/") and \
        not pathname.startswith("/Volumes/"):
        from platform import node
        hostname = node()
        parts = pathname.strip("/").split("/")
        dir = "/".join(parts[0:2])
        path = "/".join(parts)
        if exists("/net/"+hostname+"/"+dir):
            pathname = "/net/"+hostname+"/"+path

    return pathname

if __name__ == "__main__":
    print(normpath("/net/mx340hs/data/anfinrud_1403/Logfiles"))
    print(normpath("/data/anfinrud_1403/Logfiles"))
    print(normpath("//mx340hs/data/anfinrud_1403/Logfiles"))
    print(normpath(r"\\mx340hs\data\anfinrud_1403\Logfiles"))
    print(normpath(r"G:\anfinrud_1403\Logfiles"))
    print(normpath("/net/id14b4/home/useridb/NIH/Software"))
    print(normpath("//id14b4/useridb/NIH/Software"))
    print(normpath("/home/useridb/NIH/Software"))
