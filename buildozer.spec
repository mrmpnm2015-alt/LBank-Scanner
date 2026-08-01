[app]
title = LBank Scanner
package.name = lbankscanner
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json,js,html

version = 1.0.0

requirements = python3,kivy,ccxt,pandas,numpy,requests

orientation = portrait
fullscreen = 0

# تنظیمات Android
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 23b
android.accept_sdk_license = True

# غیرفعال کردن aidl
android.gradle_dependencies = 
android.enable_androidx = True

# معماری‌های پشتیبانی‌شده
android.arm64_v8a = True
android.armeabi_v7a = False
android.x86 = False
android.x86_64 = False

# حذف ابزارهای اضافی
android.add_src = 
android.meta_data = 
android.extra_java_dirs = 
android.extra_activities = 
android.extra_manifest_entries = 
android.extra_android_xml =
