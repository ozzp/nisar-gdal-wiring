# NISAR driver: GDAL integration wiring (verification-only extract)

This tree is a **verification-only extract** of the GDAL source files touched by the NISAR
driver integration, taken verbatim from the local GDAL `nisar-driver` branch described in
[`UPSTREAM_CHECKLIST.md`](https://github.com/JPL-Devin/nisar-hdf5-gdalplugin/blob/main/UPSTREAM_CHECKLIST.md)
of `JPL-Devin/nisar-hdf5-gdalplugin`. Each file sits at its real GDAL-relative path so it can be
searched and reviewed without the full OSGeo/gdal tree.

It is **not a standalone or buildable tree**: everything else in GDAL is omitted, and the C++
driver sources (`frmts/nisar/*.cpp`, `*.h`) are intentionally left out. They are identical to
[`frmts/nisar/`](https://github.com/JPL-Devin/nisar-hdf5-gdalplugin/tree/main/frmts/nisar) in
`JPL-Devin/nisar-hdf5-gdalplugin`.

## Provenance

- Base: OSGeo/gdal `master` at
  [`d6cd7744`](https://github.com/OSGeo/gdal/commit/d6cd774498e26feaa42f6c74fbfed3f47433e490)
  (3.14.0dev, 2026-10-05), the commit the `nisar-driver` branch was created from.
- `nisar-driver` = that base plus one commit, "NISAR: add NISAR HDF5 raster driver
  (frmts/nisar)" (final `gdal-nisar-driver.patch`, regenerated after plugin commit `7ebf827`).
  The files here were taken from that commit; their git blob hashes match the patch's
  post-image `index` lines, and the base blobs match `d6cd7744`.
- `frmts/nisar/CMakeLists.txt` is byte-identical to the plugin repo's
  `frmts/nisar/CMakeLists.gdal.txt`.

## What each file contributes

| File | NISAR change |
| --- | --- |
| `frmts/CMakeLists.txt` | line 168: `gdal_dependent_format(nisar "NASA-ISRO SAR (NISAR) HDF5 products" "GDAL_USE_HDF5")` |
| `frmts/drivers.ini` | line 131: `NISAR` (after `KEA`, before `BAG`) |
| `gcore/gdal_frmts.h` | line 109: `void CPL_DLL GDALRegister_NISAR(void);` |
| `frmts/gdalallregister.cpp` | lines 671-674: `GDALRegister_NISAR()` under `#ifdef FRMT_nisar`, before `GDALRegister_HDF5()` |
| `frmts/nisar/CMakeLists.txt` | new: in-tree `add_gdal_driver()` build (copy of `CMakeLists.gdal.txt`) |
| `doc/source/drivers/raster/nisar.rst` | new: driver documentation page |
| `doc/source/drivers/raster/index.rst` | line 133: `nisar` toctree entry |
| `doc/source/spelling_wordlist.txt` | lines 555-556 `dataspace`, `dataspaces`; line 1539 `Kerchunk` |
| `autotest/gdrivers/nisar.py` | new: autotest (`require_driver("NISAR")`) |
| `autotest/gdrivers/data/nisar/NISAR_L2_GCOV_synthetic.h5` | new: 19 000-byte static fixture used by `nisar.py` |

Line numbers refer to the files in this tree. Nothing here has been proposed upstream; see
`UPSTREAM_CHECKLIST.md` for the open policy, licensing and review items.
