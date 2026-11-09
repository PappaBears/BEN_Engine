# Brand v2 fonts: sources and licences

All three families are licensed under the **SIL Open Font License, Version 1.1**. The full licence texts are in this folder (`OFL-Archivo.txt`, `OFL-IBM-Plex-Sans.txt`, `OFL-IBM-Plex-Mono.txt`) and are copied next to every vendored copy (`dashboard/static/fonts/`, `web/fonts/`). The OFL allows use, embedding (web, PDF, print, signage), modification and redistribution with the product; the fonts may not be sold on their own, and modified versions may not use the reserved font names.

| Family | Copyright | Source package (npm, fetched 2026-11-09) | Files here |
| --- | --- | --- | --- |
| Archivo (variable, axes wght 100–900 and **wdth 62–125**) | Copyright 2020 The Archivo Project Authors (https://github.com/Omnibus-Type/Archivo) | `@fontsource-variable/archivo@5.3.0`, `files/archivo-{latin,latin-ext}-wdth-normal.woff2` (the `wdth.css` set: both axes) | `archivo-latin-wdth-normal.woff2`, `archivo-latin-ext-wdth-normal.woff2` |
| IBM Plex Sans 400 / 500 / 600 / 700 (+ Greek 400/500/600 for "φ") | Copyright 2019 IBM Corp. | `@fontsource/ibm-plex-sans@5.3.0` | `ibm-plex-sans-{latin,latin-ext,greek}-<w>-normal.woff2` |
| IBM Plex Mono 400 / 500 / 600 | Copyright 2017 IBM Corp. | `@fontsource/ibm-plex-mono@5.3.0` | `ibm-plex-mono-{latin,latin-ext}-<w>-normal.woff2` |

`fonts.css` registers them as `"Archivo"`, `"IBM Plex Sans"` and `"IBM Plex Mono"` (the Plex Sans Greek subset is also registered under the Mono family, because Plex Mono has no Greek and the data plate prints `3φ`).

## Static TTF instances (`ttf/`)

Generated here from the files above with fontTools (`varLib.instancer` for Archivo; WOFF2 → TTF for Plex). They are Modified Versions under the OFL only in format and named instance; the family names are kept and the licence applies unchanged. Use them where a variable WOFF2 cannot be used: matplotlib title blocks, vinyl/sign software, outlining text for production files.

| File | Instance | Use |
| --- | --- | --- |
| `Archivo-Black-Expanded125.ttf` | wght 900, wdth 125 | Display |
| `Archivo-ExtraBold-Expanded125.ttf` | wght 800, wdth 125 | H1, "BEN Engine" product line on livery |
| `Archivo-Bold.ttf` | wght 700, wdth 100 | H2 and below |
| `Archivo-ExtraBold.ttf` | wght 800, wdth 100 | Tier numbers in tables |
| `IBMPlexSans-{Regular,Medium,SemiBold,Bold}.ttf` | 400/500/600/700 | Body |
| `IBMPlexSans-Greek-{Regular,SemiBold}.ttf` | Greek subset | φ fallback |
| `IBMPlexMono-{Regular,Medium,SemiBold}.ttf` | 400/500/600 | Labels, data, the data plate band |

The TTFs carry the Latin subset only (U+0000–00FF plus punctuation). For other scripts use the WOFF2 set.
