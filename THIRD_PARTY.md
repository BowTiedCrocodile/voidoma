# Attribution and licensing

Original desktop configuration, scripts, documentation, and wallpaper are offered
under [MIT](LICENSE), using a project contributor credit rather than a personal
identity. This project is not affiliated with Void Linux, Hyprland, or Omarchy.

The optional fingerprint integration fetches these pinned upstream projects:

| Project | Copyright | License |
|---|---|---|
| [python-validity](https://github.com/uunicorn/python-validity) | 2020 uunicorn | [MIT](LICENSES/python-validity-MIT.txt) |
| [open-fprintd](https://github.com/uunicorn/open-fprintd) | 2020 uunicorn | [GPL-2.0-or-later](LICENSES/open-fprintd-GPL-2.0.txt) |

The open-fprintd license designation comes from its pinned `debian/copyright`.
The patch recipe in `fingerprint/prepare.py` contains excerpts of both projects:
those excerpts retain their upstream licenses. In particular, the open-fprintd
patches and resulting modified open-fprintd program are GPL-2.0-or-later, not
relicensed under the top-level MIT grant. Upstream code and its license files
remain in fetched/build trees; those trees are excluded from the release archive.
If distributing a built or modified fingerprint driver, retain its notices and
meet the applicable upstream source-distribution requirements.

System dependencies are installed separately and retain their own licenses.
The release contains no vendor fingerprint firmware or biometric templates.
