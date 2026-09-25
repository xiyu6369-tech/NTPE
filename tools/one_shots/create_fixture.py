import struct
import zlib
import hashlib
from pathlib import Path

# Create a minimal valid PNG (1x1 pixel)
png_data = bytes.fromhex('89504E470D0A1A0A')  # PNG signature
# IHDR chunk
ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
png_data += struct.pack('>I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
# IDAT chunk (empty compressed data)
idat_data = b'\x00'
idat_crc = zlib.crc32(b'IDAT' + idat_data) & 0xffffffff
png_data += struct.pack('>I', len(idat_data)) + b'IDAT' + idat_data + struct.pack('>I', idat_crc)
# IEND chunk
iend_crc = zlib.crc32(b'IEND') & 0xffffffff
png_data += struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)

fixture_dir = Path('tests/contract/fixtures')
fixture_dir.mkdir(parents=True, exist_ok=True)
with open(fixture_dir / 'test_image.png', 'wb') as f:
    f.write(png_data)
print(f'Created test PNG: {len(png_data)} bytes')
print(f'SHA256: {hashlib.sha256(png_data).hexdigest()}')