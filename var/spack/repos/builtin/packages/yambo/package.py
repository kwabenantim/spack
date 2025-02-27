# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Yambo(AutotoolsPackage):
    """Yambo is a FORTRAN/C code for Many-Body calculations in solid
    state and molecular physics.

    Yambo relies on the Kohn-Sham wavefunctions generated by two DFT
    public codes: abinit, and PWscf. The code was originally developed
    in the Condensed Matter Theoretical Group of the Physics Department
    at the University of Rome "Tor Vergata" by Andrea Marini. Previous
    to its release under the GPL license, yambo was known as SELF.
    """

    homepage = "https://www.yambo-code.org/index.php"
    url = "https://github.com/yambo-code/yambo/archive/4.2.2.tar.gz"

    license("GPL-2.0-or-later")

    version("5.2.1", sha256="0ac362854313927d75bbf87be98ff58447f3805f79724c38dc79df07f03a7046")
    version("5.1.1", sha256="c85036ca60507e627c47b6c6aee8241830349e88110e1ce9132ef03ab2c4e9f6")
    version("4.2.2", sha256="86b4ebe679387233266aba49948246c85a32b1e6840d024f162962bd0112448c")
    version("4.2.1", sha256="8ccd0ca75cc32d9266d4a37edd2a7396cf5038f3a68be07c0f0f77d1afc72bdc")
    version("4.2.0", sha256="9f78c4237ff363ff4e9ea5eeea671b6fff783d9a6078cc31b0b1abeb1f040f4d")

    depends_on("c", type="build")  # generated
    depends_on("fortran", type="build")  # generated

    variant("dp", default=False, description="Enable double precision")
    variant(
        "profile",
        values=any_combination_of("time", "memory"),
        description="Activate profiling of specific sections",
    )

    variant(
        "io",
        values=any_combination_of("iotk", "etsf-io"),
        description="Activate support for different io formats (requires network access)",
    )

    # MPI + OpenMP parallelism
    variant("mpi", default=True, description="Enable MPI support")
    variant("openmp", default=False, description="Enable OpenMP support")

    depends_on("blas")
    depends_on("lapack")

    # MPI dependencies are forced, until we have proper forwarding of variants
    #
    # Note that yambo is used as an application, and not linked as a library,
    # thus there will be no case where another package pulls-in e.g.
    # netcdf-c+mpi and wants to depend on yambo~mpi.
    depends_on("mpi", when="+mpi")
    depends_on("netcdf-c+mpi", when="+mpi")
    depends_on("hdf5+mpi", when="+mpi")
    depends_on("fftw+mpi", when="+mpi")
    depends_on("scalapack", when="+mpi")

    depends_on("netcdf-c~mpi", when="~mpi")
    depends_on("hdf5~mpi", when="~mpi")
    depends_on("fftw~mpi", when="~mpi")

    depends_on("hdf5+fortran")
    depends_on("netcdf-c")
    depends_on("netcdf-fortran")
    depends_on("libxc@2.0.3:")

    build_targets = ["all"]

    parallel = False

    # The configure in the package has the string 'cat config/report'
    # hard-coded, which causes a failure at configure time due to the
    # current working directory in Spack. Fix this by using the absolute
    # path to the file.
    @run_before("configure")
    def filter_configure(self):
        report_abspath = join_path(self.build_directory, "config", "report")
        filter_file("config/report", report_abspath, "configure")

    def enable_or_disable_time(self, activated):
        return "--enable-time-profile" if activated else "--disable-time-profile"

    def enable_or_disable_memory(self, activated):
        return "--enable-memory-profile" if activated else "--disable-memory-profile"

    def enable_or_disable_openmp(self, activated):
        return "--enable-open-mp" if activated else "--disable-open-mp"

    def configure_args(self):
        args = [
            # As of version 4.2.1 there are hard-coded paths that make
            # the build process fail if the target prefix is not the
            # configure directory
            f"--prefix={self.stage.source_path}",
            "--disable-keep-objects",
            "--with-editor=none",
        ]
        spec = self.spec

        # Double precision
        args.extend(self.enable_or_disable("dp"))

        # Application profiling
        args.extend(self.enable_or_disable("profile"))

        # MPI + threading
        args.extend(self.enable_or_disable("mpi"))
        args.extend(self.enable_or_disable("openmp"))

        # LAPACK
        if spec.satisfies("+mpi"):
            args.append(
                "--with-scalapack-libs={0}".format(
                    spec["scalapack"].libs + spec["lapack"].libs + spec["blas"].libs
                )
            )

        args.extend(
            [f"--with-blas-libs={spec['blas'].libs}", f"--with-lapack-libs={spec['lapack'].libs}"]
        )

        # Netcdf
        args.extend(
            [
                "--enable-netcdf-hdf5",
                "--enable-hdf5-compression",
                f"--with-hdf5-libs={spec['hdf5'].libs}",
                f"--with-netcdf-path={spec['netcdf-c'].prefix}",
                f"--with-netcdff-path={spec['netcdf-fortran'].prefix}",
            ]
        )

        args.extend(self.enable_or_disable("io"))

        # Other dependencies
        args.append(f"--with-fft-path={spec['fftw'].prefix}")
        args.append(f"--with-libxc-path={spec['libxc'].prefix}")

        return args

    def install(self, spec, prefix):
        # As of version 4.2.1 an 'install' target is advertized,
        # but not present
        install_tree("bin", prefix.bin)
        install_tree("lib", prefix.lib)
        install_tree("include", prefix.include)
        install_tree("driver", prefix.driver)
