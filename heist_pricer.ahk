#Requires AutoHotkey >=2.0
JEE_RunGetStdOut(vTarget, vSize:="")
{
    DetectHiddenWindows(true)
    vPID := ""
    Run(A_ComSpec,, "Hide", &vPID)
    WinWait("ahk_pid " vPID)
    DllCall("kernel32\AttachConsole", "UInt", vPID)
    oShell := ComObject("WScript.Shell")
    oExec := oShell.Exec(vTarget)
    vStdOut := ""
    if !(vSize = "")
        VarSetStrCapacity(&vStdOut, vSize)
    while !oExec.StdOut.AtEndOfStream
        vStdOut := oExec.StdOut.ReadAll()
    DllCall("kernel32\FreeConsole")
    ProcessClose(vPID)
    return vStdOut
}

Alt & F3::
F3::
{
    result := JEE_RunGetStdOut(a_scriptdir "\dist\heist_ocr\heist_ocr.exe")
    MsgBox(result)
}