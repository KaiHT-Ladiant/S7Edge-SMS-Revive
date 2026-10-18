#!/system/bin/sh
MODDIR=${0%/*}
mount -o bind $MODDIR/files/telephony-common.jar /system/framework/telephony-common.jar
