#!/usr/bin/env pytest
# -*- coding: utf-8 -*-
###############################################################################
#
# Project:  GDAL/OGR Test Suite
# Purpose:  Test read functionality for NISAR driver.
# Author:   NISAR project, Jet Propulsion Laboratory
#
###############################################################################
# Copyright 2025 California Institute of Technology
# U.S. Government sponsorship acknowledged.
#
# SPDX-License-Identifier: MIT
###############################################################################

import array
import shutil

import gdaltest
import pytest

from osgeo import gdal

pytestmark = pytest.mark.require_driver("NISAR")

###############################################################################
# data/nisar/NISAR_L2_GCOV_synthetic.h5 is a minimal synthetic L2 GCOV-like
# product (19 KB) generated with h5py:
#
#   NROWS, NCOLS = 20, 30
#   X0, DX, Y0, DY = 500010.0, 20.0, 3799990.0, -20.0
#   grid = "/science/LSAR/GCOV/grids/frequencyA"
#   with h5py.File("NISAR_L2_GCOV_synthetic.h5", "w") as f:
#       ident = f.create_group("/science/LSAR/identification")
#       ident.create_dataset("productType", data=np.bytes_("GCOV"))
#       ident.create_dataset("productLevel", data=np.bytes_("L2"))
#       g = f.create_group(grid)
#       g.create_dataset("listOfCovarianceTerms", data=np.array([b"HHHH", b"HVHV"]))
#       for name, scale in (("HHHH", 1), ("HVHV", 2)):
#           data = (np.arange(NROWS * NCOLS, dtype=np.float32) * scale)
#           g.create_dataset(name, data=data.reshape(NROWS, NCOLS),
#                            chunks=(10, 15), compression="gzip")
#       g.create_dataset("xCoordinates", data=X0 + DX * np.arange(NCOLS))
#       g.create_dataset("yCoordinates", data=Y0 + DY * np.arange(NROWS))
#       proj = g.create_dataset("projection", data=np.uint32(32611))
#       proj.attrs["epsg_code"] = np.uint32(32611)

GCOV = "data/nisar/NISAR_L2_GCOV_synthetic.h5"
NOT_NISAR = "data/hdf5/groups.h5"
GRID = "/science/LSAR/GCOV/grids/frequencyA"
NROWS, NCOLS = 20, 30
X0, DX = 500010.0, 20.0
Y0, DY = 3799990.0, -20.0
EPSG = 32611
CHECKSUM = {"HHHH": 6742, "HVHV": 6809}


def _expected_data(scale):
    return array.array("f", [i * scale for i in range(NROWS * NCOLS)]).tobytes()


@pytest.fixture(autouse=True)
def check_no_file_leaks():
    num_files = len(gdaltest.get_opened_files())

    yield

    diff = len(gdaltest.get_opened_files()) - num_files
    assert diff <= 0, "Leak of file handles: %d leaked" % diff


###############################################################################
# Identify: NISAR granule with and without the NISAR: prefix, and a plain
# HDF5 file that must be left to the HDF5 driver.


def test_nisar_identify():

    drv = gdal.IdentifyDriverEx(GCOV, allowed_drivers=["NISAR"])
    assert drv is not None and drv.ShortName == "NISAR"

    drv = gdal.IdentifyDriver("NISAR:" + GCOV)
    assert drv is not None and drv.ShortName == "NISAR"

    assert gdal.IdentifyDriverEx(NOT_NISAR, allowed_drivers=["NISAR"]) is None


def test_nisar_open_non_nisar_fails():

    with pytest.raises(Exception):
        gdal.OpenEx(NOT_NISAR, allowed_drivers=["NISAR"])

    with pytest.raises(Exception):
        gdal.Open("NISAR:" + NOT_NISAR)

    with pytest.raises(Exception):
        gdal.Open(f'NISAR:"{GCOV}":{GRID}/does_not_exist')


def test_nisar_open_prefixed_without_extension(tmp_path):

    # An explicit NISAR: prefix claims the file whatever its extension, for
    # Open() as well as Identify().
    dst = tmp_path / "granule_without_extension"
    shutil.copy(GCOV, dst)

    assert gdal.IdentifyDriver(f'NISAR:"{dst}":{GRID}/HHHH').ShortName == "NISAR"
    ds = gdal.Open(f'NISAR:"{dst}":{GRID}/HHHH')
    assert ds.GetRasterBand(1).Checksum() == CHECKSUM["HHHH"]


###############################################################################
# Container open: no bands, subdataset inventory, metadata domains.


def test_nisar_subdatasets():

    ds = gdal.OpenEx(GCOV, allowed_drivers=["NISAR"])
    assert ds.GetDriver().ShortName == "NISAR"
    assert ds.RasterCount == 0

    sds = ds.GetSubDatasets()
    assert [name for name, _ in sds] == [
        f'NISAR:"{GCOV}":{GRID}/HHHH',
        f'NISAR:"{GCOV}":{GRID}/HVHV',
    ]
    assert sds[0][1] == f"[{NROWS}x{NCOLS}] {GRID}/HHHH (Float32)"

    domains = ds.GetMetadataDomainList()
    assert "SUBDATASETS" in domains
    assert "NISAR_GLOBAL" in domains
    assert len(domains) == len(set(domains)), "duplicated metadata domains"

    # Repeated reads must return the same (dataset-owned) inventory
    assert ds.GetMetadata("SUBDATASETS") == ds.GetMetadata("SUBDATASETS")

    ds = None
    assert not gdaltest.is_file_open(GCOV), "file still opened."


###############################################################################
# Open a subdataset through the standard GDALTest harness (checksum,
# geotransform, projection).


@pytest.mark.parametrize("pol", ["HHHH", "HVHV"])
def test_nisar_gdaltest_open(pol):

    tst = gdaltest.GDALTest(
        "NISAR",
        f'NISAR:"{GCOV}":{GRID}/{pol}',
        1,
        CHECKSUM[pol],
        filename_absolute=1,
    )
    tst.testOpen(
        check_gt=(X0 - DX / 2, DX, 0, Y0 - DY / 2, 0, DY),
        check_prj=f"EPSG:{EPSG}",
    )


###############################################################################


@pytest.mark.parametrize(
    "connection",
    [
        f'NISAR:"{GCOV}":{GRID}/HVHV',
        f"NISAR:{GCOV}:{GRID}/HVHV",
    ],
    ids=["quoted", "unquoted"],
)
def test_nisar_open_subdataset(connection):

    ds = gdal.Open(connection)
    assert ds.GetDriver().ShortName == "NISAR"
    assert (ds.RasterXSize, ds.RasterYSize, ds.RasterCount) == (NCOLS, NROWS, 1)
    assert ds.GetMetadataItem("HDF5_PATH") == f"{GRID}/HVHV"

    band = ds.GetRasterBand(1)
    assert band.DataType == gdal.GDT_Float32
    assert band.ReadRaster() == _expected_data(2)
    assert band.Checksum() == CHECKSUM["HVHV"]


def test_nisar_read_window():

    ds = gdal.Open(f'NISAR:"{GCOV}":{GRID}/HHHH')
    band = ds.GetRasterBand(1)
    # Window straddling the 10x15 HDF5 chunk boundaries
    data = band.ReadRaster(12, 7, 6, 5)
    expected = array.array(
        "f", [float(y * NCOLS + x) for y in range(7, 12) for x in range(12, 18)]
    ).tobytes()
    assert data == expected


###############################################################################
# Georeferencing: xCoordinates / yCoordinates are pixel centers, SRS comes
# from the epsg_code attribute of the sibling "projection" dataset.


def test_nisar_georeferencing():

    ds = gdal.Open(f"NISAR:{GCOV}:{GRID}/HHHH")
    assert ds.GetGeoTransform() == pytest.approx(
        (X0 - DX / 2, DX, 0, Y0 - DY / 2, 0, DY)
    )
    srs = ds.GetSpatialRef()
    assert srs is not None
    assert srs.GetAuthorityName(None) == "EPSG"
    assert srs.GetAuthorityCode(None) == str(EPSG)
    assert ds.GetGCPCount() == 0


###############################################################################
# Open options


@pytest.mark.parametrize(
    "options,expected",
    [
        (["FREQ=A"], "HHHH"),
        (["INST=LSAR", "POL=HVHV"], "HVHV"),
        (["pol=hvhv"], "HVHV"),
    ],
)
def test_nisar_open_options(options, expected):

    ds = gdal.OpenEx(GCOV, allowed_drivers=["NISAR"], open_options=options)
    assert ds.GetMetadataItem("HDF5_PATH") == f"{GRID}/{expected}"
    assert ds.GetRasterBand(1).ReadRaster() == _expected_data(
        1 if expected == "HHHH" else 2
    )


@pytest.mark.parametrize(
    "options,message",
    [
        (["INST=XSAR"], "Invalid INST"),
        (["FREQ=C"], "Invalid FREQ"),
        (["POL=VVVV"], "Invalid POL"),
        (["DUMP_MODE=BOGUS"], "Invalid DUMP_MODE"),
        (["QUANTITY=incidenceAngle"], "DEM_FILE"),
    ],
)
def test_nisar_open_options_invalid(options, message):

    with pytest.raises(Exception, match=message):
        gdal.OpenEx(GCOV, allowed_drivers=["NISAR"], open_options=options)


###############################################################################
# Read-only driver


def test_nisar_update_rejected():

    with pytest.raises(Exception, match="only supports read access"):
        gdal.OpenEx(
            f"NISAR:{GCOV}:{GRID}/HHHH",
            gdal.OF_RASTER | gdal.OF_UPDATE,
            allowed_drivers=["NISAR"],
        )


def test_nisar_no_create():

    drv = gdal.GetDriverByName("NISAR")
    assert drv.GetMetadataItem(gdal.DCAP_CREATE) is None
    assert drv.GetMetadataItem(gdal.DCAP_CREATECOPY) is None
    assert drv.GetMetadataItem(gdal.DCAP_RASTER) == "YES"
    assert drv.GetMetadataItem(gdal.DMD_HELPTOPIC) == "drivers/raster/nisar.html"
    assert drv.GetMetadataItem(gdal.DMD_OPENOPTIONLIST) is not None
