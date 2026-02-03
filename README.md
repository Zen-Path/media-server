# Media Server

A script that handles download requests for URLs.

- [Media Server](#media-server)
    - [Dependencies](#dependencies)
    - [Installation](#installation)
    - [Usage](#usage)
    - [Technical Notes](#technical-notes)

## Dependencies

- `gallery-dl` - for image downloads
- `yt-dlp` - for video downloads and gallery-dl fallback

If configured, `gallery-dl` can use `yt-dlp` as a fallback, so it needs to be installed system-wide, not in the venv.

## Installation

1. Install the `ViolentMonkey` extension (guide [here](https://violentmonkey.github.io/get-it/))
2. Add the [client script](./../../userscripts/mediaServerClient.js) to ViolentMonkey (guide [here](https://violentmonkey.github.io/guide/creating-a-userscript/))
3. (Optional) Set up the environmental variables:

    Copy `example.env` to `.env` in `src/`. Paths should be absolute.

## Usage

To launch the app:

```sh
cd $FLEXYCON_HOME
source venv/bin/activate
media_server --verb
```

## Technical Notes

The expansion logic utilizes **Level Homogeneity** to differentiate between single galleries and collections based on `gallery-dl` JSON output.

1. Single Gallery

Direct galleries produce a nested hierarchy. Metadata is followed by individual media files.

```sh
gallery-dl 'https://site.com/chapter/1' -j -s
# Example: https://dynasty-scans.com/chapters/tonari_no_robot_ch01
```

```json
[
  [2, {"author": "Nishi Uko", "title": "Ch.1"}], // Metadata
  [3, "https://site.com/img_01.webp", {...}]     // Image File
]
```

2. Collection

Collections produce a flat list of sub-galleries.

```sh
gallery-dl 'https://site.com/series/manga_name' -s -j
# Example: https://dynasty-scans.com/series/tonari_no_robot
```

```json
[
    [6, "https://site.com/chapter/1", { "subcategory": "manga" }],
    [6, "https://site.com/chapter/2", { "subcategory": "manga" }]
]
```
