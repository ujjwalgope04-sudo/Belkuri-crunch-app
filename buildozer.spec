[app]
title = Belkuri Crunch
package.name = belkuricrunch
package.domain = org.belkuricrunch

source.dir = .
source.include_exts = py,kv,png,jpg,atlas

version = 1.0
requirements = python3,kivy==2.3.1,pyjnius

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
