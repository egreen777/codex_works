import json
import os
import re
import shutil
import subprocess


def cpu_percent():
    result = subprocess.run(
        ["top", "-bn", "1"],
        capture_output=True,
        text=True,
        check=True,
    )

    cpu_line = next(
        (line for line in result.stdout.splitlines() if "%cpu" in line.lower()),
        None,
    )
    if cpu_line is None:
        raise RuntimeError("CPU summary not found in top output")

    matches = re.findall(r"(\d+)%([a-z]+)", cpu_line.lower())
    if not matches:
        raise RuntimeError("CPU summary could not be parsed")

    values = {label: int(value) for value, label in matches}
    idle = values.get("idle", 0)
    cores = max(os.cpu_count() or 1, 1)
    return round(max(0.0, min(100.0, 100.0 - (idle / cores))), 1)


def memory_percent():
    fields = {}
    with open("/proc/meminfo", encoding="utf-8") as meminfo:
        for line in meminfo:
            name, value = line.split(":", 1)
            fields[name] = int(value.strip().split()[0])

    total = fields["MemTotal"]
    available = fields["MemAvailable"]
    used = total - available
    return round((used / total) * 100, 1)


def storage_percent():
    usage = shutil.disk_usage("/")
    return round((usage.used / usage.total) * 100, 1)

def run():
    status = {
        "cpu": cpu_percent(),
        "memory": memory_percent(),
        "storage": storage_percent(),
    }
    print(json.dumps(status))  # CLI는 JSON 출력을 선호합니다.

if __name__ == "__main__":
    run()
