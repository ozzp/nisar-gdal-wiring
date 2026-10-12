.. _raster.nisar:

================================================================================
NISAR -- NASA-ISRO SAR (NISAR) HDF5 products
================================================================================

.. shortname:: NISAR

.. versionadded:: 3.14

.. build_dependencies:: libhdf5

This driver reads the HDF5 products of the NASA-ISRO Synthetic Aperture Radar
(`NISAR <https://nisar.jpl.nasa.gov/>`__) mission:

.. list-table::
   :header-rows: 1

   * - Level
     - Product types
     - Raster location inside the HDF5 file
   * - L1 (radar coordinates)
     - RSLC, RIFG, RUNW
     - ``/science/<INST>/<PRODUCT>/swaths/frequency{A,B}/...``
   * - L2 (geocoded)
     - GSLC, GCOV, GUNW, GOFF
     - ``/science/<INST>/<PRODUCT>/grids/frequency{A,B}/...``
   * - L3 (geocoded)
     - SME2
     - ``/science/<INST>/<PRODUCT>/grids/radarData/frequency{A,B}/...``

``<INST>`` is ``LSAR`` (L-band) or ``SSAR`` (S-band). A file is recognized when
it starts with the HDF5 signature and contains a
``/science/LSAR/identification`` or ``/science/SSAR/identification`` group. The
``productType`` and ``productLevel`` datasets of that group select the product
level.

The driver is read-only. Compared to the generic :ref:`raster.hdf5` driver, it
knows the NISAR product layout, so it can georeference L1 and L2/L3 rasters,
expose NISAR metadata groups as metadata domains and read remote products
efficiently. NISAR is registered before HDF5, so it takes precedence for NISAR
products.

Driver capabilities
-------------------

.. supports_georeferencing::

.. supports_virtualio::

Subdatasets
-----------

When a NISAR file is opened without a dataset path (and without the ``INST``,
``FREQ`` or ``POL`` open options), the driver returns a container dataset with
no bands. Each HDF5 dataset of rank 2 or more under ``/science/<INST>/`` that
is not a string dataset is listed in the ``SUBDATASETS`` metadata domain. The
names have the following syntax:

::

    NISAR:"file_name":hdf5_path

where *file_name* is the local path or remote URL of the product, and
*hdf5_path* is the absolute path of the HDF5 dataset, for example
``/science/LSAR/GCOV/grids/frequencyA/HHHH``. The double quotes around
*file_name* are optional when it contains no colon. The ``NISAR:`` prefix is
optional for local ``.h5`` files.

.. code-block:: console

    $ gdalinfo NISAR_L2_PR_GCOV_..._001.h5
    ...
    Subdatasets:
      SUBDATASET_1_NAME=NISAR:"NISAR_L2_PR_GCOV_..._001.h5":/science/LSAR/GCOV/grids/frequencyA/HHHH
      SUBDATASET_1_DESC=[16704x16272] /science/LSAR/GCOV/grids/frequencyA/HHHH (Float32)
    ...

A 2-D dataset is exposed as a single band. For a 3-D dataset, such as a
metadata cube, the first dimension is exposed as bands. If a sibling
``heightAboveEllipsoid`` dataset exists, each band description and its
``HEIGHT_METERS`` metadata item are set from it.

Complex rasters (SLC products) also have ``AMPLITUDE``, ``PHASE``, ``REAL``,
``IMAG``, ``INTENSITY`` and ``CONJ`` entries in the ``DERIVED_SUBDATASETS``
metadata domain, and real rasters have ``LOGAMPLITUDE``. Open them with the
:ref:`raster.derived` syntax, for example
``DERIVED_SUBDATASET:AMPLITUDE:NISAR:"file.h5":/science/LSAR/GSLC/grids/frequencyA/HH``.

Georeferencing
--------------

- L2 and L3 products: the driver looks for ``xCoordinates`` and
  ``yCoordinates`` 1-D datasets in the group of the raster or one of its
  parent groups. The geotransform is derived from them. The coordinates are
  pixel centers, so the origin is shifted by half a pixel. The SRS comes from
  the ``epsg_code`` attribute of the ``projection`` dataset next to the raster.
  If ``epsg_code`` is missing, the ``spatial_ref`` WKT attribute is used.

- L1 products: rasters are in radar (slant range / zero-Doppler azimuth)
  geometry and have no geotransform. The driver generates ground control points
  from the ``metadata/geolocationGrid`` group (``coordinateX``,
  ``coordinateY``, ``zeroDopplerTime``, ``slantRange`` and ``epsg``) of the
  product. Use :program:`gdalwarp` with ``-tps`` or ``-order`` to project them.

Validity masks
--------------

With the ``MASK=YES`` open option, each band gets a mask band built from the
product's ``mask`` layer. Rasters whose path contains ``/mask`` get a nodata
value of 255 and category names.

Metadata
--------

The default metadata domain has the attributes of the raster dataset. The
``NISAR_GLOBAL`` domain has the scalar datasets of the identification group.
The ``METADATA`` open option loads groups under
``/science/<INST>/<PRODUCT>/metadata`` (for example ``ORBIT`` or
``RADARGRID``) as ``NISAR_<GROUP>`` metadata domains.

The ``NISAR_DUMP`` metadata domain (:program:`gdalinfo` ``-mdd NISAR_DUMP``)
gives an ``h5dump``-like listing of the HDF5 hierarchy. Use the ``DUMP``, ``DUMP_ROOT`` and
``DUMP_MODE`` open options to control it.

3-D metadata cube interpolation
-------------------------------

NISAR stores geometry quantities, such as incidence angle or look angle, as
coarse 3-D cubes indexed by height. When the ``QUANTITY`` open option is set,
the driver returns a virtual raster. The cube is interpolated onto the imaging
grid of the product, using the heights of the DEM given by the ``DEM_FILE``
open option.

Open options
------------

|about-open-options|
The following open options are available:

-  .. oo:: INST
      :choices: LSAR, SSAR
      :default: LSAR

      Instrument to open when the connection string has no HDF5 path.

-  .. oo:: FREQ
      :choices: A, B
      :default: A

      Frequency sub-band to open.

-  .. oo:: POL

      Polarization or covariance term to open, for example ``HH`` or
      ``HHHH``. The value is checked against ``listOfPolarizations`` (or
      ``listOfCovarianceTerms`` for GCOV). The default is ``HHHH`` for GCOV
      and ``HH`` for other products. When :oo:`INST`, :oo:`FREQ` or
      :oo:`POL` is set, the driver opens that raster instead of the
      container.

-  .. oo:: METADATA

      ``ALL`` or a comma-separated list of metadata groups (``ATTITUDE``,
      ``CALIBRATIONINFORMATION``, ``CEOSANALYSISREADYDATA``, ``ORBIT``,
      ``PROCESSINGINFORMATION``, ``RADARGRID``, ``SOURCEDATA``) to load as
      ``NISAR_<GROUP>`` metadata domains.

-  .. oo:: MASK
      :choices: YES, NO
      :default: NO

      Whether to attach a validity mask band built from the product mask.

-  .. oo:: QUANTITY

      Name of a metadata cube (for example ``incidenceAngle``) to interpolate
      onto the imaging grid. If the connection string has no HDF5 path, the
      cube is looked up under ``metadata/radarGrid`` (L2/L3) or
      ``metadata/geolocationGrid`` (L1). Requires :oo:`DEM_FILE`.

-  .. oo:: DEM_FILE

      Path of the DEM used by :oo:`QUANTITY`.

-  .. oo:: DEM_RESAMPLING
      :choices: NEAREST, BILINEAR, CUBIC, CUBICSPLINE
      :default: CUBICSPLINE

      Resampling method used to warp the DEM onto a geocoded grid.

-  .. oo:: DEM_NODATA_HEIGHT
      :default: 0

      Height, in meters, used where the DEM is nodata or absent (L1
      interpolation).

-  .. oo:: DUMP
      :choices: YES, NO
      :default: NO

      Whether to list ``NISAR_DUMP`` in the metadata domain list, so that it is
      included by :program:`gdalinfo` ``-mdd all``.

-  .. oo:: DUMP_ROOT
      :default: /science/<INST>

      HDF5 group where the ``NISAR_DUMP`` listing starts. Use ``/`` for the
      whole file.

-  .. oo:: DUMP_MODE
      :choices: HEADER, FULL
      :default: HEADER

      ``HEADER`` lists objects, datatypes, dataspaces and attributes. ``FULL``
      also prints the values of scalar and small 1-D datasets.

-  .. oo:: ENABLE_PAGE_BUFFERING
      :choices: YES, NO
      :default: NO

      Reserved. The driver always opens files with a 4 MiB HDF5 page buffer.

Configuration options
---------------------

|about-config-options|
The following configuration options are available:

-  .. config:: NISAR_PREFETCH_GRID
      :default: 1

      Size, in blocks, of the square grid of HDF5 chunks read in a single
      request when a block is missing from the cache. Larger values, such as
      24, speed up full-scene reads.

-  .. config:: NISAR_MAX_MEGAFETCH_BYTES
      :default: 16777216

      Maximum size, in bytes, of one coalesced read.

-  .. config:: NISAR_MAX_VIRTUAL_OVR
      :default: 16

      Largest decimation factor of the virtual overviews (powers of two). Set
      to 1 to disable them.

-  .. config:: NISAR_DUMP_MAX_ELEMENTS
      :default: 64

      Largest number of elements printed for a value in ``NISAR_DUMP``.

-  .. config:: NISAR_DUMP_MAX_STRING_CHARS
      :default: 2048

      Longest string printed in ``NISAR_DUMP`` before truncation.

-  .. config:: NISAR_EXPORT_ZARR
      :choices: YES, NO
      :default: NO

      Whether to write a Kerchunk JSON file describing the HDF5 chunks of the
      opened raster.

:config:`GDAL_NUM_THREADS` sets the number of threads that decompress chunks.

Remote access
-------------

The driver supports :ref:`virtual_file_systems`. For ``/vsicurl/``,
``/vsis3/`` and other ``/vsi`` network file systems, HDF5 I/O goes through a
virtual file driver backed by GDAL's VSI API, not the HDF5 ROS3 driver.
GDAL's usual HTTP caching, retries (:config:`GDAL_HTTP_MAX_RETRY`) and
credentials (``AWS_*``) apply. ``s3://bucket/key`` is rewritten to
``/vsis3/bucket/key``, and ``http(s)://...`` to ``/vsicurl/http(s)://...``.

To avoid a network round trip, a remote file is recognized from its name: it
must contain ``NISAR``, or start with the ``NISAR:`` prefix.

GDAL block size is set to the HDF5 chunk size. Neighboring chunks are read in
a single range request, controlled by :config:`NISAR_PREFETCH_GRID`, and
decompressed in parallel.

.. code-block:: bash

    gdalinfo --config AWS_NO_SIGN_REQUEST YES \
        'NISAR:"/vsis3/bucket/NISAR_L2_PR_GCOV_..._001.h5":/science/LSAR/GCOV/grids/frequencyA/HHHH'

See Also
--------

-  :ref:`raster.hdf5`
-  `NISAR product specifications <https://science.nasa.gov/mission/nisar/>`__
-  `Standalone plugin repository <https://github.com/JPL-Devin/nisar-hdf5-gdalplugin>`__
