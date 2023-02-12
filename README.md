# True Server Reticle (TSR)
A mod fixing several issues with the reticle in World of Tanks:
- Reticle being desynchronized from actual turret rotation
  - [Source](https://github.com/StranikS-Scan/WorldOfTanks-Decompiled/blob/1.19.1/source/res/scripts/client/vehiclegunrotator.py#L188)
- Reticle being 1.71x bigger than the actual shell distribution (credit to Jak_Atackka and [his mod](https://wgmods.net/6349))
  - Speaking of that, Jak, if you want this taken down or modified so it doesn't include your fix, contact me on Discord ``Archie#3274``

## What's the difference between TSR and FixReticleSize?
| Modification | True Server Reticle | Fix Reticle Size (v0.1)|
| - | - | - |
| Scales down reticle to its true size |:heavy_check_mark:|:heavy_check_mark:|
| Works with double-barrel tanks |:heavy_check_mark:|:x:|
| Fixes gun angle desync |:heavy_check_mark:|:x:|
| Displays current dispersion |:heavy_check_mark:|:x:|
| Toggleable in the garage |:heavy_check_mark:|:x:|

## Any dependencies?
Yes, there are two:
- [CH4MPi's GUIFlash](https://github.com/CH4MPi/GUIFlash)
- [IzeBerg's ModSettingsAPI](https://bitbucket.org/IzeBerg/modssettingsapi/src/master/)
