# 패치된 JAR 배치

이 폴더에 패치된 `telephony-common.jar`를 넣으세요.

공개 저장소에는 저작권(삼성 독점 프레임워크) 때문에 JAR를 포함하지 않습니다.
`adb pull /system/framework/telephony-common.jar` 후 `scripts/patch_all.py`로 패치한 결과물을 여기에 복사하세요.

예:
```
cp patched2.jar module/files/telephony-common.jar
```
