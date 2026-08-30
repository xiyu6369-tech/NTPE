#!/usr/bin/env python3
"""
File Creation Trace Tool
Traces the creator process of a file using Windows APIs and Event Logs.
"""

import subprocess
import json
import sys
import os
from datetime import datetime
from pathlib import Path


def run_powershell(script):
    """Run a PowerShell script and return stdout."""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def get_file_metadata(filepath):
    """Get file creation time and basic metadata using PowerShell."""
    script = f"""
    $file = Get-Item -LiteralPath '{filepath}'
    $result = @{{
        FullName = $file.FullName
        CreationTime = $file.CreationTime.ToString('o')
        LastWriteTime = $file.LastWriteTime.ToString('o')
        LastAccessTime = $file.LastAccessTime.ToString('o')
        Length = $file.Length
        Directory = $file.DirectoryName
    }}
    $result | ConvertTo-Json -Compress
    """
    stdout, stderr, code = run_powershell(script)
    if code != 0:
        return {"error": stderr}
    return json.loads(stdout)


def get_process_info(pid):
    """Get process information including command line and parent process."""
    script = f"""
    $proc = Get-WmiObject Win32_Process -Filter "ProcessId = {pid}"
    if ($proc) {{
        $parent = Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.ParentProcessId)"
        $result = @{{
            ProcessId = $proc.ProcessId
            Name = $proc.Name
            CommandLine = $proc.CommandLine
            ExecutablePath = $proc.ExecutablePath
            ParentProcessId = $proc.ParentProcessId
            ParentName = if ($parent) {{ $parent.Name }} else {{ $null }}
            ParentCommandLine = if ($parent) {{ $parent.CommandLine }} else {{ $null }}
            CreationDate = $proc.CreationDate
        }}
        $result | ConvertTo-Json -Compress
    }}
    """
    stdout, stderr, code = run_powershell(script)
    if code != 0 or not stdout:
        return {"error": f"Process {pid} not found or access denied"}
    return json.loads(stdout)


def trace_process_chain(pid, max_depth=10):
    """Trace the parent process chain up to max_depth."""
    chain = []
    current_pid = pid
    for _ in range(max_depth):
        info = get_process_info(current_pid)
        if "error" in info:
            chain.append(info)
            break
        chain.append(info)
        if info.get("ParentProcessId") and info["ParentProcessId"] != 0:
            current_pid = info["ParentProcessId"]
        else:
            break
    return chain


def check_ntpe_process(process_info):
    """Check if a process is related to NTPE."""
    ntpe_indicators = [
        "ntpe",
        "NTPE",
        "python",
        "pwsh",
        "powershell",
        "kilo",
        "agent",
    ]
    name = (process_info.get("Name") or "").lower()
    cmdline = (process_info.get("CommandLine") or "").lower()
    exe_path = (process_info.get("ExecutablePath") or "").lower()

    for indicator in ntpe_indicators:
        if indicator in name or indicator in cmdline or indicator in exe_path:
            return True, indicator
    return False, None


def query_file_creation_events(filepath, hours_back=24):
    """Query Windows Security/Event logs for file creation events."""
    filename = Path(filepath).name
    directory = str(Path(filepath).parent).replace("\\", "\\\\")
    
    script = f"""
    $startTime = (Get-Date).AddHours(-{hours_back})
    $events = Get-WinEvent -FilterHashtable @{{
        LogName = 'Security'
        Id = 4663
        StartTime = $startTime
    }} -ErrorAction SilentlyContinue | Where-Object {{
        $_.Properties[6].Value -like '*{filename}*' -and
        $_.Properties[5].Value -like '*{directory}*'
    }} | Select-Object TimeCreated, Id, @{{Name='ProcessId';Expression={{$_.Properties[4].Value}}}}, @{{Name='ProcessName';Expression={{$_.Properties[5].Value}}}}, @{{Name='ObjectName';Expression={{$_.Properties[6].Value}}}}, @{{Name='AccessMask';Expression={{$_.Properties[7].Value}}}}
    $events | ConvertTo-Json -Compress -Depth 3
    """
    stdout, stderr, code = run_powershell(script)
    if code != 0:
        return {"error": stderr, "events": []}
    if not stdout:
        return {"events": []}
    try:
        events = json.loads(stdout)
        if not isinstance(events, list):
            events = [events]
        return {"events": events}
    except json.JSONDecodeError:
        return {"error": "Failed to parse events", "events": []}


def main():
    if len(sys.argv) < 2:
        print("Usage: file_creation_trace.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        sys.exit(1)

    filepath = os.path.abspath(filepath)
    print(f"Tracing creation of: {filepath}")

    # Get file metadata
    print("\n=== File Metadata ===")
    metadata = get_file_metadata(filepath)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    # Query file creation events from Security log
    print("\n=== File Creation Events (Security Log) ===")
    events = query_file_creation_events(filepath)
    print(json.dumps(events, indent=2, ensure_ascii=False))

    # If we have events with process IDs, trace them
    process_chains = []
    if events.get("events"):
        for event in events["events"]:
            pid = event.get("ProcessId")
            if pid:
                print(f"\n=== Process Chain for PID {pid} ===")
                chain = trace_process_chain(pid)
                print(json.dumps(chain, indent=2, ensure_ascii=False))
                
                # Check for NTPE relation
                for proc in chain:
                    is_ntpe, indicator = check_ntpe_process(proc)
                    proc["is_ntpe_related"] = is_ntpe
                    proc["ntpe_indicator"] = indicator
                
                process_chains.append({
                    "event": event,
                    "process_chain": chain
                })

    # Also check current processes that might have the file open
    print("\n=== Current Processes with File Open (if any) ===")
    script = f"""
    $handles = Get-Process | Where-Object {{ $_.Id -ne $PID }} | ForEach-Object {{
        try {{
            $handles = (Get-Process -Id $_.Id).Handles
        }} catch {{ $handles = @() }}
        $_ | Add-Member -MemberType NoteProperty -Name 'HandleCount' -Value $handles.Count -Force
        $_
    }} | Where-Object {{ $_.HandleCount -gt 0 }}
    $handles | Select-Object Id, ProcessName, HandleCount | ConvertTo-Json -Compress
    """
    stdout, stderr, code = run_powershell(script)
    if code == 0 and stdout:
        print(stdout)

    # Compile final report
    report = {
        "trace_timestamp": datetime.now().isoformat(),
        "target_file": filepath,
        "file_metadata": metadata,
        "file_creation_events": events,
        "process_chains": process_chains,
        "working_directory": os.getcwd(),
    }

    # Write to artifacts
    artifacts_dir = Path("D:/Python/NTPE/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = artifacts_dir / f"DUMMY-TXT-02_trace_{timestamp}.json"
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Report saved to: {report_file} ===")
    
    # Summary
    print("\n=== SUMMARY ===")
    print(f"File: {filepath}")
    print(f"Creation Time: {metadata.get('CreationTime', 'Unknown')}")
    print(f"Events Found: {len(events.get('events', []))}")
    print(f"Process Chains Traced: {len(process_chains)}")
    
    ntpe_found = False
    for chain_data in process_chains:
        for proc in chain_data["process_chain"]:
            if proc.get("is_ntpe_related"):
                print(f"NTPE-related process found: PID={proc.get('ProcessId')}, Name={proc.get('Name')}, Indicator={proc.get('ntpe_indicator')}")
                ntpe_found = True
    
    if not ntpe_found:
        print("No NTPE-related process found in traced chains.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())