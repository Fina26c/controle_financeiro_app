[app]
title = Controle Financeiro
package.name = controlefinanceiro
package.domain = com.seuapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.0
requirements = python3,kivy==2.1.0,fpdf
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[android]
api = 30
minapi = 21
ndk = 22b