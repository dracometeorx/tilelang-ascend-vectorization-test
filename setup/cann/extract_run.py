"""Extract verified Makeself archives without executing installer scripts.

RPM signatures must be verified separately before using this helper.
Every inner archive's embedded SHA256 and size are checked before extraction.
"""
import hashlib
import gzip
import re
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

archive, destination = map(Path, sys.argv[1:])
with archive.open("rb") as stream:
    header = stream.read(65536)
    skip = int(re.search(rb'^skip="(\d+)"', header, re.M)[1])
    expected = re.search(rb'^SHA="([a-f0-9]{64})"', header, re.M)[1].decode()
    expected_size = int(re.search(rb'^totalsize="(\d+)"', header, re.M)[1])
    stream.seek(0)
    for _ in range(skip):
        stream.readline()
    offset = stream.tell()
    assert archive.stat().st_size - offset == expected_size, "Archive size mismatch"
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
    assert digest == expected, f"SHA256 mismatch: {archive}"
    print(f"SHA256 verified: {archive.name}: {digest}", flush=True)
    stream.seek(offset)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir="/workspace/setup/cann") as unpacked:
        with gzip.GzipFile(fileobj=stream) as compressed:
            shutil.copyfileobj(compressed, unpacked)
        unpacked.seek(0)
        with tarfile.open(fileobj=unpacked, mode="r:") as payload:
            payload.extractall(destination, filter="data")
print(f"Extracted to {destination}")
