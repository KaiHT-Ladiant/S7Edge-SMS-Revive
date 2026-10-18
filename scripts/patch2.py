import zipfile,struct,hashlib,zlib,sys
src='patched.jar'
z=zipfile.ZipFile(src); d=bytearray(z.read('classes.dex'))
def u4(o): return struct.unpack_from('<I',d,o)[0]
def uleb(o):
    r=0;s=0
    while True:
        b=d[o];o+=1;r|=(b&0x7f)<<s;s+=7
        if b<0x80: return r,o
str_ids_off=u4(0x3c); type_ids_off=u4(0x44); method_ids_off=u4(0x5c); class_defs_size=u4(0x60); class_defs_off=u4(0x64)
def string(i):
    o=u4(str_ids_off+4*i); n,o=uleb(o); e=o
    while d[e]: e+=1
    return d[o:e].decode('utf8','replace')
def tname(i): return string(u4(type_ids_off+4*i))
def mname(i):
    o=method_ids_off+8*i; return string(u4(o+4))
target='Lcom/android/internal/telephony/ImsSmsDispatcher;'
for c in range(class_defs_size):
    co=class_defs_off+32*c
    if tname(u4(co))!=target: continue
    cd=u4(co+24); o=cd
    sf,o=uleb(o);if_,o=uleb(o);dm,o=uleb(o);vm,o=uleb(o)
    for _ in range(sf+if_): _,o=uleb(o);_,o=uleb(o)
    idx=0
    for k in range(dm+vm):
        if k==dm: idx=0
        df,o=uleb(o);idx+=df;_,o=uleb(o);code,o=uleb(o)
        if mname(idx)=='isAvailable' and struct.unpack_from('<H',d,code+2)[0]==2:
            insns=code+16
            print('code',hex(code),'regs',struct.unpack_from('<H',d,code)[0],'first',d[insns:insns+4].hex())
            d[insns:insns+4]=bytes([0x12,0x10,0x0f,0x00])
            d[0x0c:0x20]=hashlib.sha1(d[0x20:]).digest()
            d[8:12]=struct.pack('<I',zlib.adler32(bytes(d[12:]))&0xffffffff)
            out=zipfile.ZipFile('patched2.jar','w')
            for i in z.infolist():
                data=bytes(d) if i.filename=='classes.dex' else z.read(i.filename)
                out.writestr(i,data,compress_type=i.compress_type)
            out.close(); print('written'); sys.exit()
print('not found')

