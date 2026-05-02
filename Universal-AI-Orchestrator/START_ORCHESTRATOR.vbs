Set objShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' 1. Check if Python is installed
On Error Resume Next
objShell.Run "python --version", 0, True
If Err.Number <> 0 Then
    MsgBox "ERROR: Python is not installed on this system." & vbCrLf & vbCrLf & _
           "To run the AI Orchestrator, please install Python from python.org." & vbCrLf & _
           "Make sure to check 'Add Python to PATH' during installation.", _
           16, "Universal AI Security Alert"
    WScript.Quit
End If
On Error GoTo 0

' 2. Launch the Orchestrator
' Using cmd /c ensuring the window stays open if launched directly
objShell.Run "cmd /c python orchestrator.py", 1, True
