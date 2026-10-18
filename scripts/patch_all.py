#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
telephony-common.jar의 classes.dex를 바이너리 패치하여
ImsSmsDispatcher.isImsforNonLegacyImsSms()Z 와
ImsSmsDispatcher.isAvailable(Ljava/lang/String;)Z 를
항상 true를 반환하도록 만듭니다.

사용법:
  python3 patch_all.py [입력.jar] [출력.jar]
기본값: telephony-common.jar -> patched2.jar

개별 패치(원본 유지):
  patch.py  : telephony-common.jar -> patched.jar  (isImsforNonLegacyImsSms)
  patch2.py : patched.jar -> patched2.jar           (isAvailable)
"""
import zipfile, struct, hashlib, zlib, sys

src = sys.argv[1] if len(sys.argv) > 1 else 'telephony-common.jar'
dst = sys.argv[2] if len(sys.argv) > 2 else 'patched2.jar'

z = zipfile.ZipFile(src)
d = bytearray(z.read('classes.dex'))

def u4(o):
    return struct.unpack_from('<I', d, o)[0]

def uleb(o):
    r = 0; s = 0
    while True:
        b = d[o]; o += 1; r |= (b & 0x7f) << s; s += 7
        if b < 0x80:
            return r, o

str_ids_off = u4(0x3c)
type_ids_off = u4(0x44)
method_ids_off = u4(0x5c)
class_defs_size = u4(0x60)
class_defs_off = u4(0x64)

def string(i):
    o = u4(str_ids_off + 4 * i)
    n, o = uleb(o)
    e = o
    while d[e]:
        e += 1
    return d[o:e].decode('utf8', 'replace')

def tname(i):
    return string(u4(type_ids_off + 4 * i))

def mname(i):
    o = method_ids_off + 8 * i
    return string(u4(o + 4))

PATCH = bytes([0x12, 0x10, 0x0f, 0x00])  # const/4 v0,1 ; return v0
target = 'Lcom/android/internal/telephony/ImsSmsDispatcher;'
patched = set()

for c in range(class_defs_size):
    co = class_defs_off + 32 * c
    if tname(u4(co)) != target:
        continue
    cd = u4(co + 24)
    o = cd
    sf, o = uleb(o); if_, o = uleb(o); dm, o = uleb(o); vm, o = uleb(o)
    for _ in range(sf + if_):
        _, o = uleb(o); _, o = uleb(o)
    idx = 0
    for k in range(dm + vm):
        if k == dm:
            idx = 0
        df, o = uleb(o); idx += df; _, o = uleb(o); code, o = uleb(o)
        name = mname(idx)
        do_patch = False
        if name == 'isImsforNonLegacyImsSms':
            do_patch = True
        elif name == 'isAvailable' and struct.unpack_from('<H', d, code + 2)[0] == 2:
            do_patch = True
        if do_patch:
            insns = code + 16
            print(f'{name}: code {hex(code)} regs={struct.unpack_from("<H", d, code)[0]} first={d[insns:insns+4].hex()}')
            d[insns:insns + 4] = PATCH
            patched.add(name)

if patched != {'isImsforNonLegacyImsSms', 'isAvailable'}:
    print('패치 대상 메서드를 모두 찾지 못함:', patched)
    sys.exit(1)

d[0x0c:0x20] = hashlib.sha1(d[0x20:]).digest()
d[8:12] = struct.pack('<I', zlib.adler32(bytes(d[12:])) & 0xffffffff)

out = zipfile.ZipFile(dst, 'w')
for i in z.infolist():
    data = bytes(d) if i.filename == 'classes.dex' else z.read(i.filename)
    out.writestr(i, data, compress_type=i.compress_type)
out.close()
print(f'작성 완료: {dst} (패치: {", ".join(sorted(patched))})')
