# Galaxy S7 edge — Eylem ROM LG U+ SMS over IMS 수정

Galaxy S7 edge (SM-G935S, Exynos 8890)에서 **Eylem ROM**(Note20 Ultra N985F 포트, Android 13, CSC DBT) + **LG U+ SIM** 환경에서 통화는 되지만 SMS가 실패하는 문제를 고치는 KernelSU 모듈과 바이너리 패치 스크립트입니다.

> **저작권 안내:** 패치된 `telephony-common.jar`는 삼성 독점 프레임워크이므로 **이 공개 저장소에는 포함하지 않습니다.** 직접 `adb pull` 후 패치 스크립트로 생성하세요. 비공개 미러에는 개인 백업용으로 JAR가 있을 수 있습니다.

## 환경

| 항목 | 값 |
|------|-----|
| 기기 | Galaxy S7 edge SM-G935S (Exynos 8890) |
| ROM | Eylem ROM (N985F 포트), Android 13, CSC DBT |
| 통신사 | LG U+ |
| 루트 | KernelSU (`ksud` 3.1.0) |
| 증상 | 통화 OK, SMS/LMS/MMS 실패 |

## 원인

Samsung IMS (`com.sec.imsservice`)는 LG U+ 프로필(`LGU VoLTE`, mmtel+smsip)로 등록되어 있었습니다. 그러나 프레임워크 `ImsSmsDispatcher`는 구형 모뎀이 ROM이 기대하는 방식으로 IMS 등록을 보고하지 않아 `mImsRegistered=false`로 판단했고, SMS가 CS/GSM으로 내려갔습니다. LG U+는 CS SMS를 거부하므로 전송이 실패했습니다.

## 수정 방법

`/system/framework/telephony-common.jar` 안의 `classes.dex`를 바이너리 패치합니다.

대상 메서드(첫 명령어를 `const/4 v0, 1; return v0` = 바이트 `12 10 0f 00`로 교체):

1. `ImsSmsDispatcher.isImsforNonLegacyImsSms()Z` (code off `0xf0520`)
2. `ImsSmsDispatcher.isAvailable(Ljava/lang/String;)Z` (code off `0xf01ec`)

패치 후 dex SHA1과 Adler32를 재계산합니다.

| 스크립트 | 입력 → 출력 | 패치 |
|----------|-------------|------|
| `scripts/patch.py` | `telephony-common.jar` → `patched.jar` | ① isImsforNonLegacyImsSms |
| `scripts/patch2.py` | `patched.jar` → `patched2.jar` | ② isAvailable |
| `scripts/patch_all.py` | 한 번에 둘 다 | ①+② (권장) |

## KernelSU 모듈

`ksud` 3.x는 `system/`을 자동 마운트하지 않으므로 **bind mount**를 사용합니다.

```
module/
  module.prop
  post-fs-data.sh
  files/
    telephony-common.jar   # 패치본 (직접 배치)
```

`module.prop`:

```
id=smsims
name=SMS over IMS fix
version=1
versionCode=1
author=Koa
description=Force SMS over IMS for LG U+
```

`post-fs-data.sh`:

```sh
#!/system/bin/sh
MODDIR=${0%/*}
mount -o bind $MODDIR/files/telephony-common.jar /system/framework/telephony-common.jar
```

## 설치

1. 원본 JAR 추출:
   ```bash
   adb pull /system/framework/telephony-common.jar
   ```
2. 패치:
   ```bash
   python3 scripts/patch_all.py telephony-common.jar patched2.jar
   cp patched2.jar module/files/telephony-common.jar
   ```
3. 모듈 설치 (택1):
   - `/data/adb/modules/smsims`에 `module/` 내용 복사 후 재부팅
   - 또는 모듈 폴더를 zip으로 묶어 KernelSU 앱에서 설치
4. 재부팅

## 제거

모듈 디렉터리(`/data/adb/modules/smsims`)를 삭제한 뒤 재부팅합니다.

## 결과

- SMS / LMS / MMS 송수신 확인 (로그 예: `sendSms: - IMS isIms()=true ... onSent`, MMS `resp_st=128`)
- 통화는 정상 유지

## 주의사항

- **ROM 업데이트 전에 모듈을 비활성화**하고, 업데이트 후 **해당 빌드의 JAR로 다시 패치**하세요.
- **이 ROM 빌드 전용**입니다. 다른 기기/ROM/빌드에 그대로 쓰지 마세요.
- 잘못된 JAR를 바인드하면 부팅 루프 등이 날 수 있습니다. 복구 수단(TWRP/커스텀 리커버리 등)을 준비하세요.

## 면책

이 프로젝트는 개인 실험·연구 목적입니다. 사용으로 인한 기기 손상, 보증 무효, 서비스 제한, 법적 문제에 대해 작성자는 책임지지 않습니다. 삼성 프레임워크 JAR를 재배포하지 마세요. 루팅·시스템 수정은 본인 책임입니다.
