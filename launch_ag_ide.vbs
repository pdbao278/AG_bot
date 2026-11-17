Set WshShell = CreateObject("WScript.Shell")

' Khởi động Antigravity IDE
WshShell.Run """C:\Users\Bao\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe""", 1, False

' Khởi động AG-Telebot bot ẩn (không hiện cửa sổ cmd)
WshShell.CurrentDirectory = "E:\tool\AG"
WshShell.Run """C:\Users\Bao\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"" src\main.py", 0, False
