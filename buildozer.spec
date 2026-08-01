[app]
title = LBank Scanner
package.name = lbankscanner
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,json,js,html

version = 1.0.0

requirements = python3==3.10.0,kivy==2.2.0,ccxt==4.1.0,pandas==2.0.0,numpy==1.24.0,requests==2.31.0

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.enable_androidx = True
android.arm64_v8a = True
android.armeabi_v7a = False
android.x86 = False
android.x86_64 = False
