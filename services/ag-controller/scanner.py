"""
ARP scanner for device discovery on local network.
Uses scapy for ARP scan + manuf for MAC vendor lookup.
"""
import asyncio
import logging
import subprocess
import re
from dataclasses import dataclass
from datetime import datetime, timezone

log = logging.getLogger("ag-controller.scanner")


@dataclass
class DiscoveredDevice:
    ip: str
    mac: str
    hostname: str | None
    manufacturer: str | None


def _normalize_mac(mac: str) -> str:
    return mac.lower().replace("-", ":").strip()


def _arp_scan(subnet: str, interface: str) -> list[DiscoveredDevice]:
    """Run arp-scan and parse output."""
    try:
        result = subprocess.run(
            ["arp-scan", "--interface", interface, subnet],
            capture_output=True,
            text=True,
            timeout=30,
        )
        devices = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                ip = parts[0].strip()
                mac = _normalize_mac(parts[1].strip())
                vendor = parts[2].strip() if len(parts) > 2 else None
                if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                    devices.append(DiscoveredDevice(ip=ip, mac=mac, hostname=None, manufacturer=vendor))
        return devices
    except FileNotFoundError:
        # Fallback to /proc/net/arp when arp-scan is not available
        return _read_arp_table()
    except Exception as e:
        log.warning("arp-scan failed: %s", e)
        return _read_arp_table()


def _read_arp_table() -> list[DiscoveredDevice]:
    """Read kernel ARP cache as fallback."""
    devices = []
    try:
        with open("/proc/net/arp") as f:
            next(f)  # skip header
            for line in f:
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "0x2":
                    ip = parts[0]
                    mac = _normalize_mac(parts[3])
                    if mac != "00:00:00:00:00:00":
                        devices.append(DiscoveredDevice(ip=ip, mac=mac, hostname=None, manufacturer=None))
    except Exception as e:
        log.warning("ARP table read failed: %s", e)
    return devices


async def scan(subnet: str, interface: str) -> list[DiscoveredDevice]:
    loop = asyncio.get_event_loop()
    devices = await loop.run_in_executor(None, _arp_scan, subnet, interface)
    # Resolve hostnames
    for dev in devices:
        try:
            result = subprocess.run(
                ["nslookup", dev.ip],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.splitlines():
                if "name =" in line.lower():
                    dev.hostname = line.split("=")[-1].strip().rstrip(".")
                    break
        except Exception:
            pass
    return devices
