import os
import platform
from concurrent.futures import ThreadPoolExecutor as Pool
import glob
import sys
from sys import platform as _platform
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext as _build_ext
from setuptools.command.sdist import sdist as _sdist
from setupext import \
    check_for_openmp, \
    check_for_pyembree, \
    read_embree_location, \
    in_conda_env
from distutils.version import LooseVersion
from distutils.ccompiler import CCompiler
import pkg_resources


def _get_cpu_count():
    if platform.system() != "Windows":
        return os.cpu_count()
    return 0


def _compile(
    self, sources, output_dir=None, macros=None, include_dirs=None,
    debug=0, extra_preargs=None, extra_postargs=None, depends=None,
):
    """Function to monkey-patch distutils.ccompiler.CCompiler"""
    macros, objects, extra_postargs, pp_opts, build = self._setup_compile(
        output_dir, macros, include_dirs, sources, depends, extra_postargs
    )
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)

    for obj in objects:
        try:
            src, ext = build[obj]
        except KeyError:
            continue
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

    # Return *all* object filenames, not just the ones we just built.
    return objects

CCompiler.compile = _compile

if sys.version_info < (3, 5):
    print("yt currently supports versions newer than Python 3.5")
    print("certain features may fail unexpectedly and silently with older "
          "versions.")
    sys.exit(1)

try:
    distribute_ver = \
        LooseVersion(pkg_resources.get_distribution("distribute").version)
    if distribute_ver < LooseVersion("0.7.3"):
        print("Distribute is a legacy package obsoleted by setuptools.")
        print("We strongly recommend that you just uninstall it.")
        print("If for some reason you cannot do it, you'll need to upgrade it")
        print("to latest version before proceeding:")
        print("    pip install -U distribute")
        sys.exit(1)
except pkg_resources.DistributionNotFound:
    pass  # yay!

VERSION = "4.0.dev0"

if os.path.exists('MANIFEST'):
    os.remove('MANIFEST')

with open('README.md') as file:
    long_description = file.read()

if check_for_openmp() is True:
    omp_args = ['-fopenmp']
else:
    omp_args = None

if os.name == "nt":
    std_libs = []
else:
    std_libs = ["m"]

cython_extensions = [
    Extension("yt.geometry.grid_visitors",
              ["yt/geometry/grid_visitors.pyx"],
              include_dirs=["yt/utilities/lib"],
              libraries=std_libs),
    Extension("yt.geometry.grid_container",
              ["yt/geometry/grid_container.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.geometry.oct_container",
              ["yt/geometry/oct_container.pyx",
               "yt/utilities/lib/tsearch.c"],
              include_dirs=["yt/utilities/lib"],
              libraries=std_libs),
    Extension("yt.geometry.oct_visitors",
              ["yt/geometry/oct_visitors.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.geometry.particle_oct_container",
              ["yt/geometry/particle_oct_container.pyx"],
              include_dirs=["yt/utilities/lib/",
                            "yt/utilities/lib/ewahboolarray"],
              language="c++",
              libraries=std_libs,
              extra_compile_args=["-std=c++11"]),
    Extension("yt.geometry.selection_routines",
              ["yt/geometry/selection_routines.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.geometry.particle_deposit",
              ["yt/geometry/particle_deposit.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.geometry.particle_smooth",
              ["yt/geometry/particle_smooth.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.geometry.fake_octree",
              ["yt/geometry/fake_octree.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.utilities.lib.autogenerated_element_samplers",
              ["yt/utilities/lib/autogenerated_element_samplers.pyx"],
              include_dirs=["yt/utilities/lib/"]),
    Extension("yt.utilities.lib.bitarray",
              ["yt/utilities/lib/bitarray.pyx"],
              libraries=std_libs),
    Extension("yt.utilities.lib.bounding_volume_hierarchy",
              ["yt/utilities/lib/bounding_volume_hierarchy.pyx"],
              include_dirs=["yt/utilities/lib/"],
              extra_compile_args=omp_args,
              extra_link_args=omp_args,
              libraries=std_libs,
              depends=["yt/utilities/lib/mesh_triangulation.h"]),
    Extension("yt.utilities.lib.contour_finding",
              ["yt/utilities/lib/contour_finding.pyx"],
              include_dirs=["yt/utilities/lib/",
                            "yt/geometry/"],
              libraries=std_libs),
    Extension("yt.utilities.lib.cykdtree.kdtree",
              [
                  "yt/utilities/lib/cykdtree/kdtree.pyx",
                  "yt/utilities/lib/cykdtree/c_kdtree.cpp",
                  "yt/utilities/lib/cykdtree/c_utils.cpp",
              ],
              depends=[
                  "yt/utilities/lib/cykdtree/c_kdtree.hpp",
                  "yt/utilities/lib/cykdtree/c_utils.hpp",
              ],
              libraries=std_libs,
              language="c++",
              extra_compile_args=["-std=c++03"]),
    Extension("yt.utilities.lib.cykdtree.utils",
              [
                  "yt/utilities/lib/cykdtree/utils.pyx",
                  "yt/utilities/lib/cykdtree/c_utils.cpp",
              ],
              depends=["yt/utilities/lib/cykdtree/c_utils.hpp"],
              libraries=std_libs,
              language="c++",
              extra_compile_args=["-std=c++03"]),
    Extension("yt.utilities.lib.fnv_hash",
              ["yt/utilities/lib/fnv_hash.pyx"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs),
    Extension("yt.utilities.lib.geometry_utils",
              ["yt/utilities/lib/geometry_utils.pyx"],
              extra_compile_args=omp_args,
              extra_link_args=omp_args,
              libraries=std_libs),
    Extension("yt.utilities.lib.marching_cubes",
              ["yt/utilities/lib/marching_cubes.pyx",
               "yt/utilities/lib/fixed_interpolator.c"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs,
              depends=["yt/utilities/lib/fixed_interpolator.h"]),
    Extension("yt.utilities.lib.mesh_triangulation",
              ["yt/utilities/lib/mesh_triangulation.pyx"],
              depends=["yt/utilities/lib/mesh_triangulation.h"]),
    Extension("yt.utilities.lib.particle_kdtree_tools",
              ["yt/utilities/lib/particle_kdtree_tools.pyx"],
              language="c++"),
    Extension("yt.utilities.lib.bounded_priority_queue",
              ["yt/utilities/lib/bounded_priority_queue.pyx"]),
    Extension("yt.utilities.lib.pixelization_routines",
              ["yt/utilities/lib/pixelization_routines.pyx",
               "yt/utilities/lib/pixelization_constants.c"],
              include_dirs=["yt/utilities/lib/"],
              extra_compile_args=omp_args,
              extra_link_args=omp_args,
              language='c++',
              libraries=std_libs,
              depends=["yt/utilities/lib/pixelization_constants.h"]),
    Extension("yt.utilities.lib.cyoctree",
              ["yt/utilities/lib/cyoctree.pyx"],
              extra_compile_args=omp_args,
              extra_link_args=omp_args,
              libraries=std_libs,
              language='c++'),
    Extension("yt.utilities.lib.primitives",
              ["yt/utilities/lib/primitives.pyx"],
              libraries=std_libs),
    Extension("yt.utilities.lib.cosmology_time",
              ["yt/utilities/lib/cosmology_time.pyx"]),
    Extension("yt.utilities.lib.origami",
              ["yt/utilities/lib/origami.pyx",
               "yt/utilities/lib/origami_tags.c"],
              include_dirs=["yt/utilities/lib/"],
              depends=["yt/utilities/lib/origami_tags.h"]),
    Extension("yt.utilities.lib.grid_traversal",
              ["yt/utilities/lib/grid_traversal.pyx",
               "yt/utilities/lib/fixed_interpolator.c"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs,
              depends=["yt/utilities/lib/fixed_interpolator.h"]),
    Extension("yt.utilities.lib.ewah_bool_wrap",
              ["yt/utilities/lib/ewah_bool_wrap.pyx"],
              include_dirs=["yt/utilities/lib/",
                            "yt/utilities/lib/ewahboolarray"],
              language="c++"),
    Extension("yt.utilities.lib.image_samplers",
              ["yt/utilities/lib/image_samplers.pyx",
               "yt/utilities/lib/fixed_interpolator.c"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs,
              extra_compile_args=omp_args,
              extra_link_args=omp_args,
              depends=["yt/utilities/lib/fixed_interpolator.h"]),
    Extension("yt.utilities.lib.partitioned_grid",
              ["yt/utilities/lib/partitioned_grid.pyx",
               "yt/utilities/lib/fixed_interpolator.c"],
              include_dirs=["yt/utilities/lib/"],
              libraries=std_libs,
              depends=["yt/utilities/lib/fixed_interpolator.h"]),
    Extension("yt.utilities.lib.element_mappings",
              ["yt/utilities/lib/element_mappings.pyx"],
              libraries=std_libs),
    Extension("yt.utilities.lib.alt_ray_tracers",
              ["yt/utilities/lib/alt_ray_tracers.pyx"],
              libraries=std_libs),
    Extension("yt.utilities.lib.misc_utilities",
              ["yt/utilities/lib/misc_utilities.pyx"],
              extra_compile_args=omp_args,
              extra_link_args=omp_args,
              libraries=std_libs),
    Extension("yt.frontends.ramses.io_utils",
              ["yt/frontends/ramses/io_utils.pyx"],
              include_dirs=["yt/utilities/lib"],
              libraries=std_libs),
    Extension("yt.utilities.cython_fortran_utils",
              ["yt/utilities/cython_fortran_utils.pyx"],
              libraries=std_libs),
]

lib_exts = [
    "particle_mesh_operations", "depth_first_octree", "fortran_reader",
    "interpolators", "basic_octree", "image_utilities",
    "points_in_volume", "quad_tree", "mesh_utilities",
    "amr_kdtools", "lenses", "distance_queue", "allocation_container",
]
for ext_name in lib_exts:
    cython_extensions.append(
        Extension("yt.utilities.lib.{}".format(ext_name),
                  ["yt/utilities/lib/{}.pyx".format(ext_name)],
                  libraries=std_libs))

lib_exts = ["write_array", "ragged_arrays", "line_integral_convolution"]
for ext_name in lib_exts:
    cython_extensions.append(
        Extension("yt.utilities.lib.{}".format(ext_name),
                  ["yt/utilities/lib/{}.pyx".format(ext_name)]))

extensions = [
    Extension("yt.frontends.artio._artio_caller",
              ["yt/frontends/artio/_artio_caller.pyx"] +
              glob.glob("yt/frontends/artio/artio_headers/*.c"),
              include_dirs=["yt/frontends/artio/artio_headers/",
                            "yt/geometry/",
                            "yt/utilities/lib/"],
              depends=glob.glob("yt/frontends/artio/artio_headers/*.c")),
]

# EMBREE
if check_for_pyembree() is not None:
    embree_extensions = [
        Extension("yt.utilities.lib.mesh_construction",
                  ["yt/utilities/lib/mesh_construction.pyx"],
                  depends=["yt/utilities/lib/mesh_triangulation.h"]),
        Extension("yt.utilities.lib.mesh_traversal",
                  ["yt/utilities/lib/mesh_traversal.pyx"]),
        Extension("yt.utilities.lib.mesh_samplers",
                  ["yt/utilities/lib/mesh_samplers.pyx"]),
        Extension("yt.utilities.lib.mesh_intersection",
                  ["yt/utilities/lib/mesh_intersection.pyx"]),
    ]

    embree_prefix = os.path.abspath(read_embree_location())
    embree_inc_dir = [os.path.join(embree_prefix, 'include')]
    embree_lib_dir = [os.path.join(embree_prefix, 'lib')]
    if in_conda_env():
        conda_basedir = os.path.dirname(os.path.dirname(sys.executable))
        embree_inc_dir.append(os.path.join(conda_basedir, 'include'))
        embree_lib_dir.append(os.path.join(conda_basedir, 'lib'))

    if _platform == "darwin":
        embree_lib_name = "embree.2"
    else:
        embree_lib_name = "embree"

    for ext in embree_extensions:
        ext.include_dirs += embree_inc_dir
        ext.library_dirs += embree_lib_dir
        ext.language = "c++"
        ext.libraries += std_libs
        ext.libraries += [embree_lib_name]

    cython_extensions += embree_extensions

class build_ext(_build_ext):
    # subclass setuptools extension builder to avoid importing cython and numpy
    # at top level in setup.py. See http://stackoverflow.com/a/21621689/1382869
    def finalize_options(self):
        try:
            import cython
            import numpy
        except ImportError:
            raise ImportError(
"""Could not import cython or numpy. Building yt from source requires
cython and numpy to be installed. Please install these packages using
the appropriate package manager for your python environment.""")
        if LooseVersion(cython.__version__) < LooseVersion('0.26.1'):
            raise RuntimeError(
"""Building yt from source requires Cython 0.26.1 or newer but
Cython %s is installed. Please update Cython using the appropriate
package manager for your python environment.""" %
                cython.__version__)
        if LooseVersion(numpy.__version__) < LooseVersion('1.13.3'):
            raise RuntimeError(
"""Building yt from source requires NumPy 1.13.3 or newer but
NumPy %s is installed. Please update NumPy using the appropriate
package manager for your python environment.""" %
                numpy.__version__)
        from Cython.Build import cythonize
        self.distribution.ext_modules[:] = cythonize(
            self.distribution.ext_modules,
            compiler_directives={'language_level': 2},
            nthreads=_get_cpu_count(),
        )
        _build_ext.finalize_options(self)
        # Prevent numpy from thinking it is still in its setup process
        # see http://stackoverflow.com/a/21621493/1382869
        if isinstance(__builtins__, dict):
            # sometimes this is a dict so we need to check for that
            # https://docs.python.org/3/library/builtins.html
            __builtins__["__NUMPY_SETUP__"] = False
        else:
            __builtins__.__NUMPY_SETUP__ = False
        import numpy
        self.include_dirs.append(numpy.get_include())

    def build_extensions(self):
        self.check_extensions_list(self.extensions)

        ncpus = _get_cpu_count()
        if ncpus > 0:
            with Pool(ncpus) as pool:
                pool.map(self.build_extension, self.extensions)
        else:
            super().build_extensions()


class sdist(_sdist):
    # subclass setuptools source distribution builder to ensure cython
    # generated C files are included in source distribution.
    # See http://stackoverflow.com/a/18418524/1382869
    def run(self):
        # Make sure the compiled Cython files in the distribution are up-to-date
        from Cython.Build import cythonize
        cythonize(
            cython_extensions,
            compiler_directives={'language_level': 2},
            nthreads=_get_cpu_count(),
        )
        _sdist.run(self)


if __name__ == "__main__":
    setup(
        name="yt",
        version=VERSION,
        description="An analysis and visualization toolkit for volumetric data",
        long_description = long_description,
        long_description_content_type='text/markdown',
        classifiers=["Development Status :: 5 - Production/Stable",
                     "Environment :: Console",
                     "Intended Audience :: Science/Research",
                     "License :: OSI Approved :: BSD License",
                     "Operating System :: MacOS :: MacOS X",
                     "Operating System :: POSIX :: AIX",
                     "Operating System :: POSIX :: Linux",
                     "Programming Language :: C",
                     "Programming Language :: Python :: 3",
                     "Programming Language :: Python :: 3.5",
                     "Programming Language :: Python :: 3.6",
                     "Programming Language :: Python :: 3.7",
                     "Topic :: Scientific/Engineering :: Astronomy",
                     "Topic :: Scientific/Engineering :: Physics",
                     "Topic :: Scientific/Engineering :: Visualization"],
        keywords='astronomy astrophysics visualization ' +
        'amr adaptivemeshrefinement',
        entry_points={'console_scripts': [
            'yt = yt.utilities.command_line:run_main',
        ],
            'nose.plugins.0.10': [
                'answer-testing = yt.utilities.answer_testing.framework:AnswerTesting'
        ]
        },
        packages=find_packages(),
        include_package_data = True,
        install_requires=[
            'matplotlib>=1.5.3',
            'setuptools>=19.6',
            'sympy>=1.2',
            'numpy>=1.10.4',
            'IPython>=1.0',
            'unyt>=2.2.2',
        ],
        extras_require = {
            'hub':  ["girder_client"],
            'mapserver': ["bottle"]
        },
        cmdclass={'sdist': sdist, 'build_ext': build_ext},
        author="The yt project",
        author_email="yt-dev@python.org",
        url="https://github.com/yt-project/yt",
        project_urls={
            'Homepage': 'https://yt-project.org/',
            'Documentation': 'https://yt-project.org/doc/',
            'Source': 'https://github.com/yt-project/yt/',
            'Tracker': 'https://github.com/yt-project/yt/issues'
        },
        license="BSD 3-Clause",
        zip_safe=False,
        scripts=["scripts/iyt"],
        ext_modules=cython_extensions + extensions,
        python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*'
    )
