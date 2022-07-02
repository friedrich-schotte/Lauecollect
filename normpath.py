"""
Platform-independent pathnames
Author: Friedrich Schotte
Date created: 2014-03-28
Date last modified: 2021-06-20
Revision comment: Cleanup: pylint
"""
__version__ = "1.3.3"


def normpath(pathname):
    """Translate between UNIX-style to Windows-style pathnames, following
    Universal Naming Convention.
    E.g. "/net/mx340hs/data" to "//mx340hs/data"""
    if pathname == "":
        return pathname

    end = "/" if pathname.endswith("/") else ""

    from os.path import exists
    pathname = str(pathname)

    # Try to expand a Windows drive letter to a UNC name.
    # E.g. "J:/anfinrud_1106" to "//mx340hs/data/anfinrud_1106"
    try:
        from win32wnet import WNetGetUniversalName, error as win32wnet_error
    except ImportError:
        def WNetGetUniversalName(pathname):
            return pathname

        win32wnet_error = OSError
    try:
        pathname = WNetGetUniversalName(pathname)
    except win32wnet_error:
        pass

    # Resolve symbolic links. E.g. "/data" to "/net/mx340hs/data"
    # E.g. "G:/anfinrud_1403/Logfiles" or "\\mx340hs\data\anfinrud_1403\Logfiles"
    from os import name as os_name
    if not pathname[1:2] == ":" and "\\" not in pathname \
            and not pathname.startswith("//") and not os_name == "nt":
        from os.path import realpath
        pathname = realpath(pathname)
        if pathname.startswith("/System/Volumes/Data/"):
            short_pathname = pathname.replace("/System/Volumes/Data/", "/")
            if exists(toplevel_directory(short_pathname)):
                pathname = short_pathname

    # Convert separators from Window style to UNIX style.
    # E.g. "\\mx340hs\data\anfinrud_1106" to "//mx340hs/data/anfinrud_1106"
    pathname = pathname.replace("\\", "/")

    # Mac OS X: mount point "/Volumes/share" does not reveal server name.
    if pathname.startswith("/Volumes/data"):
        pathname = pathname.replace("/Volumes/data", "/net/mx340hs/data")
    if pathname.startswith("/Volumes/Femto/"):
        pathname = pathname.replace("/Volumes/Femto/", "/net/femto/C/")
    if pathname.startswith("/Volumes/C/"):
        pathname = pathname.replace("/Volumes/C/", "/net/femto/C/")
    if pathname.startswith("/Volumes/C-1/"):
        pathname = pathname.replace("/Volumes/C-1/", "/net/femto/C/")
    if pathname.startswith("/Volumes/C-2/"):
        pathname = pathname.replace("/Volumes/C-2/", "/net/femto/C/")

    # Convert from Windows to UNIX style.
    # E.g. "//mx340hs/data/anfinrud_1106" to "/net/mx340hs/data/anfinrud_1106"
    if pathname.startswith("//"):  # //server/share/directory/file
        parts = pathname.split("/")
        if len(parts) >= 4:
            server = parts[2]
            share = parts[3]
            path = "/".join(parts[4:])
            if not exists("//" + server + "/" + share):
                for prefix in "/net", "/Mirror":
                    if exists(prefix + "/" + server + "/" + share):
                        pathname = prefix + "/" + server + "/" + share + "/" + path
                    if exists(prefix + "/" + server + "/home/" + share):
                        pathname = prefix + "/" + server + "/home/" + share + "/" + path

    # Convert from UNIX to Windows style.
    # E.g. "/net/mx340hs/data/anfinrud_1106" to "//mx340hs/data/anfinrud_1106"
    from sys import platform
    if pathname.startswith("/net/") and platform == "win32":
        parts = pathname.split("/")
        if len(parts) >= 4:
            server = parts[2]
            share = parts[3]
            path = "/".join(parts[4:])
            # E.g. /net/id14b4/home/useridb/NIH/Software
            if share == "home" and len(parts) > 4:
                share = parts[4]
                path = "/".join(parts[5:])
            pathname = "//" + server + "/" + share + "/" + path

    # E.g. "/home/useridb/NIH/Software"
    if not pathname.startswith("//") and \
            pathname.startswith("/") and \
            platform != "win32" and \
            not pathname.startswith("/net/") and \
            not pathname.startswith("/Volumes/") and \
            not pathname.startswith("/Mirror/"):
        from platform import node
        hostname = node()
        parts = pathname.strip("/").split("/")
        directory = "/".join(parts[0:2])
        path = "/".join(parts)
        if exists("/net/" + hostname + "/" + directory):
            pathname = "/net/" + hostname + "/" + path

    # E.g. "/Mirror/Femto/C/All Projects/APS/Instrumentation/Software"
    if pathname.startswith("/Mirror/"):
        if not exists("/Mirror"):
            pathname = pathname.replace("/Mirror/", "//", 1)

    if not pathname.endswith(end):
        pathname += end

    return pathname


def toplevel_directory(pathname):
    if pathname.startswith("/"):
        pathname = pathname.strip("/")
        root = "/"
    else:
        root = ""
    toplevel_directory = root + pathname.split("/")[0]
    return toplevel_directory


if __name__ == "__main__":
    print(normpath("/net/mx340hs/data/anfinrud_1403/Logfiles"))
    print(normpath("/data/anfinrud_1403/Logfiles"))
    print(normpath("//mx340hs/data/anfinrud_1403/Logfiles"))
    print(normpath("/mx340hs/data/anfinrud_1403/Logfiles"))
    print(normpath(r"\\mx340hs\data\anfinrud_1403\Logfiles"))
    print(normpath(r"G:\anfinrud_1403\Logfiles"))
    print(normpath("/net/id14b4/home/useridb/NIH/Software"))
    print(normpath("//id14b4/useridb/NIH/Software"))
    print(normpath("/home/useridb/NIH/Software"))
    print(normpath("//mx340hs/data/anfinrud_1807/Archive"))
    print(normpath("/Volumes/C-1/All Projects/APS/Instrumentation/Software/Lauecollect"))
    print(normpath("/System/Volumes/Data/Mirror/femto/C/All Projects/APS/Instrumentation/Software/Lauecollect/module_dir.py"))
