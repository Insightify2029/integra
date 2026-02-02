Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Projects\Integra"
WshShell.Run Chr(34) & "C:\Program Files\Python311\pythonw.exe" & Chr(34) & " " & Chr(34) & "D:\Projects\Integra\main.py" & Chr(34), 0, False
