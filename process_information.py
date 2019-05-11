"""
How to access the PEB of another process with python ctypes

https://stackoverflow.com/questions/35106511/how-to-access-the-peb-of-another-process-with-python-ctypes
Answered Jan 31 '16 at 3:57 eryksun

The following example has the ctypes definitions that are required to query and
use ProcessBasicInformation for a given process that has the same architecture
(i.e. native 64-bit or WOW64 32-bit). It includes a class that demonstrates
usage and provides properties for the process ID, session ID, image path,
command line, and the paths for loaded modules.

The example uses a RemotePointer subclass of ctypes._Pointer, along with an
RPOINTER factory function. This class overrides __getitem__ to facilitate
dereferencing a pointer value in the address space of another process. The
index key is a tuple of the form index, handle[, size]. The optional size
parameter (in bytes) is useful for sized strings such as NTAPI UNICODE_STRING,
e.g. ustr.Buffer[0, hProcess, usrt.Length]. Null-terminated strings are not
supported, since ReadProcessMemory requires a sized buffer.

The logic for walking the loader data is in the private _modules_iter method,
which walks the loaded modules using the in-memory-order linked list. Note that
InMemoryOrderModuleList links to the InMemoryOrderLinks field of the
LDR_DATA_TABLE_ENTRY structure, and so on for each link in the list.
The module iterator has to adjust the base address for each entry by the offset
to this field. In the C API this would use the CONTAINING_RECORD macro.

The ProcessInformation constructor defaults to querying the current process if
no process ID or handle is provided. If the call status is an error or warning
(i.e. negative NTSTATUS), it calls NtError to get an instance of OSError, or
WindowsError prior to 3.3.

I have, but did not include, a more elaborate version of NtError that calls
FormatMessage to get a formatted error message, using ntdll.dll as the source
module. I can update the answer to include this version upon request.

The example was tested in Windows 7 and 10, using 32-bit and 64-bit versions
of Python 2.7 and 3.5. For the remote process test, the subprocess module is
used to start a 2nd Python instance. An event handle is passed to the child
process for synchronization. If the parent process doesn't wait for the child
process to finish loading and set the event, then the child's loader data may
not be completely initialized when read.

"""
import ctypes
from ctypes import wintypes

ntdll = ctypes.WinDLL('ntdll')
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# WINAPI Definitions

PROCESS_VM_READ           = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

ERROR_INVALID_HANDLE = 0x0006
ERROR_PARTIAL_COPY   = 0x012B

PULONG = ctypes.POINTER(wintypes.ULONG)
ULONG_PTR = wintypes.LPVOID
SIZE_T = ctypes.c_size_t

def _check_bool(result, func, args):
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return args

kernel32.ReadProcessMemory.errcheck = _check_bool
kernel32.ReadProcessMemory.argtypes = (
    wintypes.HANDLE,  # _In_  hProcess
    wintypes.LPCVOID, # _In_  lpBaseAddress
    wintypes.LPVOID,  # _Out_ lpBuffer
    SIZE_T,           # _In_  nSize
    ctypes.POINTER(SIZE_T))  # _Out_ lpNumberOfBytesRead

kernel32.CloseHandle.errcheck = _check_bool
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)

kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.GetCurrentProcess.argtypes = ()

kernel32.OpenProcess.errcheck = _check_bool
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = (
   wintypes.DWORD, # _In_ dwDesiredAccess
   wintypes.BOOL,  # _In_ bInheritHandle
   wintypes.DWORD) # _In_ dwProcessId

class RemotePointer(ctypes._Pointer):
    def __getitem__(self, key):
        # TODO: slicing
        size = None
        if not isinstance(key, tuple):
            raise KeyError('must be (index, handle[, size])')
        if len(key) > 2:
            index, handle, size = key
        else:
            index, handle = key
        if isinstance(index, slice):
            raise TypeError('slicing is not supported')
        dtype = self._type_
        offset = ctypes.sizeof(dtype) * index
        address = PVOID.from_buffer(self).value + offset
        simple = issubclass(dtype, ctypes._SimpleCData)
        if simple and size is not None:
            if dtype._type_ == wintypes.WCHAR._type_:
                buf = (wintypes.WCHAR * (size // 2))()
            else:
                buf = (ctypes.c_char * size)()
        else:
            buf = dtype()
        nread = SIZE_T()
        kernel32.ReadProcessMemory(handle,
                                   address,
                                   ctypes.byref(buf),
                                   ctypes.sizeof(buf),
                                   ctypes.byref(nread))
        if simple:
            return buf.value
        return buf

    def __setitem__(self, key, value):
        # TODO: kernel32.WriteProcessMemory
        raise TypeError('remote pointers are read only')

    @property
    def contents(self):
        # a handle is required
        raise NotImplementedError

_remote_pointer_cache = {}
def RPOINTER(dtype):
    if dtype in _remote_pointer_cache:
        return _remote_pointer_cache[dtype]
    name = 'RP_%s' % dtype.__name__
    ptype = type(name, (RemotePointer,), {'_type_': dtype})
    _remote_pointer_cache[dtype] = ptype
    return ptype

# NTAPI Definitions

NTSTATUS = wintypes.LONG
PVOID = wintypes.LPVOID
RPWSTR = RPOINTER(wintypes.WCHAR)
PROCESSINFOCLASS = wintypes.ULONG

ProcessBasicInformation   = 0
ProcessDebugPort          = 7
ProcessWow64Information   = 26
ProcessImageFileName      = 27
ProcessBreakOnTermination = 29

STATUS_UNSUCCESSFUL         = NTSTATUS(0xC0000001)
STATUS_INFO_LENGTH_MISMATCH = NTSTATUS(0xC0000004).value
STATUS_INVALID_HANDLE       = NTSTATUS(0xC0000008).value
STATUS_OBJECT_TYPE_MISMATCH = NTSTATUS(0xC0000024).value

class UNICODE_STRING(ctypes.Structure):
    _fields_ = (('Length',        wintypes.USHORT),
                ('MaximumLength', wintypes.USHORT),
                ('Buffer',        RPWSTR))

class LIST_ENTRY(ctypes.Structure):
    pass

RPLIST_ENTRY = RPOINTER(LIST_ENTRY)

LIST_ENTRY._fields_ = (('Flink', RPLIST_ENTRY),
                       ('Blink', RPLIST_ENTRY))

class LDR_DATA_TABLE_ENTRY(ctypes.Structure):
    _fields_ = (('Reserved1',          PVOID * 2),
                ('InMemoryOrderLinks', LIST_ENTRY),
                ('Reserved2',          PVOID * 2),
                ('DllBase',            PVOID),
                ('EntryPoint',         PVOID),
                ('Reserved3',          PVOID),
                ('FullDllName',        UNICODE_STRING),
                ('Reserved4',          wintypes.BYTE * 8),
                ('Reserved5',          PVOID * 3),
                ('CheckSum',           PVOID),
                ('TimeDateStamp',      wintypes.ULONG))

RPLDR_DATA_TABLE_ENTRY = RPOINTER(LDR_DATA_TABLE_ENTRY)

class PEB_LDR_DATA(ctypes.Structure):
    _fields_ = (('Reserved1',               wintypes.BYTE * 8),
                ('Reserved2',               PVOID * 3),
                ('InMemoryOrderModuleList', LIST_ENTRY))

RPPEB_LDR_DATA = RPOINTER(PEB_LDR_DATA)

class RTL_USER_PROCESS_PARAMETERS(ctypes.Structure):
    _fields_ = (('Reserved1',     wintypes.BYTE * 16),
                ('Reserved2',     PVOID * 10),
                ('ImagePathName', UNICODE_STRING),
                ('CommandLine',   UNICODE_STRING))

RPRTL_USER_PROCESS_PARAMETERS = RPOINTER(RTL_USER_PROCESS_PARAMETERS)
PPS_POST_PROCESS_INIT_ROUTINE = PVOID

class PEB(ctypes.Structure):
    _fields_ = (('Reserved1',              wintypes.BYTE * 2),
                ('BeingDebugged',          wintypes.BYTE),
                ('Reserved2',              wintypes.BYTE * 1),
                ('Reserved3',              PVOID * 2),
                ('Ldr',                    RPPEB_LDR_DATA),
                ('ProcessParameters',      RPRTL_USER_PROCESS_PARAMETERS),
                ('Reserved4',              wintypes.BYTE * 104),
                ('Reserved5',              PVOID * 52),
                ('PostProcessInitRoutine', PPS_POST_PROCESS_INIT_ROUTINE),
                ('Reserved6',              wintypes.BYTE * 128),
                ('Reserved7',              PVOID * 1),
                ('SessionId',              wintypes.ULONG))

RPPEB = RPOINTER(PEB)

class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = (('Reserved1',       PVOID),
                ('PebBaseAddress',  RPPEB),
                ('Reserved2',       PVOID * 2),
                ('UniqueProcessId', ULONG_PTR),
                ('Reserved3',       PVOID))

def NtError(status):
    import sys
    descr = 'NTSTATUS(%#08x) ' % (status % 2**32,)
    if status & 0xC0000000 == 0xC0000000:
        descr += '[Error]'
    elif status & 0x80000000 == 0x80000000:
        descr += '[Warning]'
    elif status & 0x40000000 == 0x40000000:
        descr += '[Information]'
    else:
        descr += '[Success]'
    if sys.version_info[:2] < (3, 3):
        return WindowsError(status, descr)
    return OSError(None, descr, None, status)

NtQueryInformationProcess = ntdll.NtQueryInformationProcess
NtQueryInformationProcess.restype = NTSTATUS
NtQueryInformationProcess.argtypes = (
    wintypes.HANDLE,  # _In_      ProcessHandle
    PROCESSINFOCLASS, # _In_      ProcessInformationClass
    PVOID,            # _Out_     ProcessInformation
    wintypes.ULONG,   # _In_      ProcessInformationLength
    PULONG)           # _Out_opt_ ReturnLength

class ProcessInformation(object):
    _close_handle = False
    _closed = False
    _module_names = None

    def __init__(self, process_id=None, handle=None):
        if process_id is None and handle is None:
            handle = kernel32.GetCurrentProcess()
        elif handle is None:
            handle = kernel32.OpenProcess(PROCESS_VM_READ |
                                          PROCESS_QUERY_INFORMATION,
                                          False, process_id)
            self._close_handle = True
        self._handle = handle
        self._query_info()
        if process_id is not None and self._process_id != process_id:
            raise NtError(STATUS_UNSUCCESSFUL)

    def __del__(self, CloseHandle=kernel32.CloseHandle):
        if self._close_handle and not self._closed:
            try:
                CloseHandle(self._handle)
            except WindowsError as e:
                if e.winerror != ERROR_INVALID_HANDLE:
                    raise
            self._closed = True

    def _query_info(self):
        info = PROCESS_BASIC_INFORMATION()
        handle = self._handle
        status = NtQueryInformationProcess(handle,
                                           ProcessBasicInformation,
                                           ctypes.byref(info),
                                           ctypes.sizeof(info),
                                           None)
        if status < 0:
            raise NtError(status)
        self._process_id = info.UniqueProcessId
        self._peb = peb = info.PebBaseAddress[0, handle]
        self._params = peb.ProcessParameters[0, handle]
        self._ldr = peb.Ldr[0, handle]

    def _modules_iter(self):
        headaddr = (PVOID.from_buffer(self._peb.Ldr).value +
                    PEB_LDR_DATA.InMemoryOrderModuleList.offset)
        offset = LDR_DATA_TABLE_ENTRY.InMemoryOrderLinks.offset
        pentry = self._ldr.InMemoryOrderModuleList.Flink
        while pentry:
            pentry_void = PVOID.from_buffer_copy(pentry)
            if pentry_void.value == headaddr:
                break
            pentry_void.value -= offset
            pmod = RPLDR_DATA_TABLE_ENTRY.from_buffer(pentry_void)
            mod = pmod[0, self._handle]
            yield mod
            pentry = LIST_ENTRY.from_buffer(mod, offset).Flink

    def update_module_names(self):
        names = []
        for m in self._modules_iter():
            ustr = m.FullDllName
            name = ustr.Buffer[0, self._handle, ustr.Length]
            names.append(name)
        self._module_names = names

    @property
    def module_names(self):
        if self._module_names is None:
            self.update_module_names()
        return self._module_names

    @property
    def process_id(self):
        return self._process_id

    @property
    def session_id(self):
        return self._peb.SessionId

    @property
    def image_path(self):
        ustr = self._params.ImagePathName
        return ustr.Buffer[0, self._handle, ustr.Length]

    @property
    def command_line(self):
        ustr = self._params.CommandLine
        buf = ustr.Buffer[0, self._handle, ustr.Length]
        return buf

if __name__ == '__main__':
    import os
    import sys
    import subprocess
    import textwrap

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = (('nLength',              wintypes.DWORD),
                    ('lpSecurityDescriptor', wintypes.LPVOID),
                    ('bInheritHandle',       wintypes.BOOL))
        def __init__(self, *args, **kwds):
            super(SECURITY_ATTRIBUTES, self).__init__(*args, **kwds)
            self.nLength = ctypes.sizeof(self)

    def test_remote(use_pid=True, show_modules=False):
        sa = SECURITY_ATTRIBUTES(bInheritHandle=True)
        hEvent = kernel32.CreateEventW(ctypes.byref(sa), 0, 0, None)
        try:
            script = textwrap.dedent(r"""
            import sys
            import ctypes
            kernel32 = ctypes.WinDLL('kernel32')
            kernel32.SetEvent(%d)
            sys.stdin.read()""").strip() % hEvent
            cmd = '"%s" -c "%s"' % (sys.executable, script)
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                    close_fds=False)
            try:
                kernel32.WaitForSingleObject(hEvent, 5000)
                if use_pid:
                    pi = ProcessInformation(proc.pid)
                else:
                    pi = ProcessInformation(handle=int(proc._handle))
                assert pi.process_id == proc.pid
                assert pi.image_path == sys.executable
                assert pi.command_line == cmd
                assert pi.module_names[0] == sys.executable
                if show_modules:
                    print('\n'.join(pi.module_names))
            finally:
                proc.terminate()
        finally:
            kernel32.CloseHandle(hEvent)

    print('Test 1: current process')
    pi = ProcessInformation()
    assert os.getpid() == pi.process_id
    assert pi.image_path == pi.module_names[0]
    print('Test 2: remote process (Handle)')
    test_remote(use_pid=False)
    print('Test 3: remote process (PID)')
    test_remote(show_modules=True)
