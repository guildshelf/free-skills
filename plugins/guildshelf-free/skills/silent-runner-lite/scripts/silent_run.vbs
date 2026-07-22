' silent_run.vbs — run any command with a fully hidden window (window style 0).
' Typical use: wrap a .bat (or any command) so that launching it never flashes
' a black console window or steals foreground focus.
' Usage: wscript.exe silent_run.vbs <program> [args...]
Option Explicit
Dim sh, cmd, i, a
Set sh = CreateObject("WScript.Shell")
cmd = ""
For i = 0 To WScript.Arguments.Count - 1
  a = WScript.Arguments(i)
  If InStr(a, " ") > 0 Then a = """" & a & """"
  If i > 0 Then cmd = cmd & " "
  cmd = cmd & a
Next
If Len(cmd) > 0 Then sh.Run cmd, 0, False   ' second argument 0 = hidden window
