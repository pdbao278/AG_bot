Set WshShell = CreateObject("WScript.Shell")

' Khởi động Antigravity 2.0
WshShell.Run """C:\Users\Bao\AppData\Local\Programs\antigravity\Antigravity.exe""", 1, False

' Khởi động AG-Telebot bot ẩn (không hiện cửa sổ cmd)
WshShell.CurrentDirectory = "E:\tool\AG"
WshShell.Run """C:\Users\Bao\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"" src\main.py", 0, False
