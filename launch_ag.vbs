Set WshShell = CreateObject("WScript.Shell")

' Chọn app theo tham số: "ide" → Antigravity IDE, mặc định → Antigravity 2.0
Dim appPath
If WScript.Arguments.Count > 0 And LCase(WScript.Arguments(0)) = "ide" Then
    appPath = "C:\Users\Bao\AppData\Local\Programs\Antigravity IDE\Antigravity IDE.exe"
Else
    appPath = "C:\Users\Bao\AppData\Local\Programs\antigravity\Antigravity.exe"
End If

' Khởi động Antigravity
WshShell.Run """" & appPath & """", 1, False

' Khởi động AG-Telebot bot ẩn (không hiện cửa sổ cmd)
WshShell.CurrentDirectory = "E:\tool\AG"
WshShell.Run """C:\Users\Bao\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"" src\main.py", 0, False
