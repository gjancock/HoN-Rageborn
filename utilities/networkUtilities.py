import subprocess

import time

def get_active_adapter():
    ps_cmd = r'''
    Get-NetRoute -DestinationPrefix "0.0.0.0/0" |
    Sort-Object RouteMetric |
    Select-Object -First 1 |
    ForEach-Object {
        (Get-NetAdapter -InterfaceIndex $_.InterfaceIndex).Name
    }
    '''
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    adapter = result.stdout.strip()
    return adapter if adapter else None


def testPing(host="8.8.8.8", timeout_ms=1000):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception:
        return False


def wait_for_ping(host="8.8.8.8", timeout=30, interval=1):
    start = time.time()
    while time.time() - start < timeout:
        if testPing(host=host, timeout_ms=1000):
            return True
        time.sleep(interval)
    return False


def getDisconnected():
    adapter = get_active_adapter()
    if not adapter:
        raise RuntimeError("No active internet adapter found")

    print(f"[INFO] Disabling adapter: {adapter}")
    subprocess.run(
        f'powershell -NoProfile -Command "Disable-NetAdapter -Name \'{adapter}\' -Confirm:$false"',
        shell=True,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return adapter


def reconnect(adapter):
    print(f"[INFO] Enabling adapter: {adapter}")
    subprocess.run(
        f'powershell -NoProfile -Command "Enable-NetAdapter -Name \'{adapter}\' -Confirm:$false"',
        shell=True,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
