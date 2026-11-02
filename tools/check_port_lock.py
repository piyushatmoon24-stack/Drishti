import ctypes
from ctypes import wintypes
import sys
import psutil

ntdll = ctypes.WinDLL("ntdll.dll")
kernel32 = ctypes.WinDLL("kernel32.dll")

STATUS_INFO_LENGTH_MISMATCH = 0xC0000004
STATUS_SUCCESS = 0x00000000

SystemExtendedHandleInformation = 64

class SYSTEM_HANDLE_TABLE_ENTRY_INFO_EX(ctypes.Structure):
    _fields_ = [
        ("Object", ctypes.c_void_p),
        ("UniqueProcessId", ctypes.c_size_t),
        ("HandleValue", ctypes.c_size_t),
        ("GrantedAccess", wintypes.ULONG),
        ("CreatorBackTraceIndex", wintypes.USHORT),
        ("ObjectTypeIndex", wintypes.USHORT),
        ("HandleAttributes", wintypes.ULONG),
        ("Reserved", wintypes.ULONG),
    ]

# Try basic process inspection
print("Searching for process with handle to COM3...")
for proc in psutil.process_iter(['pid', 'name']):
    name = proc.info['name'].lower()
    if 'brave' in name or 'edge' in name or 'chrome' in name:
        print(f"Browser candidate: {proc.info['name']} (PID: {proc.info['pid']})")
