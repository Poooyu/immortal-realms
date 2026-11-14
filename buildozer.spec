[app]

title = Immortal Realms
package.name = immortal_realms
package.domain = com.immortalrealms
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
requirements = python3,kivy
orientation = landscape
fullscreen = 1
android.presplash_color = #000000
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 34
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.skip_update = False
android.logcat_filters = *:S python:D
android.copy_libs = 1

[buildozer]

log_level = 2
warn_on_root = 1
