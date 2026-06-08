from __future__ import annotations

import ipaddress
import socket
import subprocess
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def build_certificate(cert_dir: Path) -> None:
    cert_dir.mkdir(parents=True, exist_ok=True)

    ipv4_addresses = _detect_local_ipv4_addresses()
    san_entries = [
        x509.DNSName("localhost"),
        x509.DNSName(socket.gethostname()),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        x509.IPAddress(ipaddress.IPv6Address("::1")),
    ]

    for address in ipv4_addresses:
        if address != "127.0.0.1":
            san_entries.append(x509.IPAddress(ipaddress.IPv4Address(address)))

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "RU"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "PawCare Local Dev"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    san = x509.SubjectAlternativeName(san_entries)

    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=825))
        .add_extension(san, critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=True,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ), critical=True)
        .sign(private_key=key, algorithm=hashes.SHA256())
    )

    key_path = cert_dir / "localhost.key.pem"
    cert_path = cert_dir / "localhost.cert.pem"
    trust_path = cert_dir / "localhost.cer"

    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    trust_path.write_bytes(cert.public_bytes(serialization.Encoding.DER))

    print(f"Generated certificate files in: {cert_dir}")
    if ipv4_addresses:
        print(f"Detected IPv4 addresses: {', '.join(ipv4_addresses)}")
    print(f"  {trust_path.name}  (import this into Windows Trusted Root)")
    print(f"  {cert_path.name}")
    print(f"  {key_path.name}")


def _detect_local_ipv4_addresses() -> list[str]:
    candidates: set[str] = set()

    powershell_addresses = _detect_ipv4_with_powershell()
    candidates.update(powershell_addresses)

    try:
        output = subprocess.check_output(["ipconfig"], text=True, encoding="utf-8", errors="ignore")
    except Exception:
        output = ""

    for line in output.splitlines():
        line = line.strip()
        if "IPv4 Address" in line or "IPv4-адрес" in line:
            if ":" in line:
                value = line.split(":", 1)[1].strip()
                value = value.rstrip("(Preferred)").strip()
                try:
                    ipaddress.IPv4Address(value)
                except ValueError:
                    continue
                if not value.startswith("169.254."):
                    candidates.add(value)

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            candidates.add(sock.getsockname()[0])
    except OSError:
        pass

    return sorted(candidates)


def _detect_ipv4_with_powershell() -> list[str]:
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254*' } | Select-Object -ExpandProperty IPAddress | ConvertTo-Json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True,
        )
    except Exception:
        return []

    output = completed.stdout.strip()
    if not output:
        return []

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, str):
        parsed = [parsed]

    addresses: list[str] = []
    for value in parsed:
        try:
            ipaddress.IPv4Address(value)
        except ValueError:
            continue
        addresses.append(value)

    return addresses


if __name__ == "__main__":
    build_certificate(Path(__file__).resolve().parent.parent / "caddy" / "ssl")
