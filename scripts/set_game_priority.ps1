# =========================================
# HoN Priority Enforcer
# Process : hon.exe
# Priority: High
# =========================================

$processName = "juvio"

Write-Host "[HoN Priority Enforcer] Running..."

while ($true)
{
    try
    {
        $procs = Get-Process -Name $processName -ErrorAction SilentlyContinue

        foreach ($p in $procs)
        {
            if ($p.PriorityClass -ne "High")
            {
                $p.PriorityClass = "High"
                Write-Host "[OK] Set hon.exe PID $($p.Id) to HIGH"
                break
            }
        }
    }
    catch
    {
        Write-Host "[ERROR] Failed to set priority: $_"
    }

    Start-Sleep -Milliseconds 800
}
