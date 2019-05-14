#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from distutils.spawn import find_executable
import os
import shutil

class QtConan(ConanFile):

    name = "qt"
    upstream_version = "5.12.2"
    package_revision = ""
    version = "{0}{1}".format(upstream_version, package_revision)

    description = "Qt library."
    url = "https://git.ircad.fr/conan/conan-qt"
    homepage = "https://www.qt.io/"
    license = "http://doc.qt.io/qt-5/lgpl.html"
    settings = "os", "arch", "compiler", "build_type"
    exports = [
        "patches/c++11.patch",
    ]

    short_paths = True
    no_copy_source = False

    def configure(self):
        del self.settings.compiler.libcxx
        if 'CI' not in os.environ:
            os.environ["CONAN_SYSREQUIRES_MODE"] = "verify"

    def requirements(self):
        if tools.os_info.is_windows:
            self.requires("zlib/1.2.11-r1@sight/stable")
            self.requires("openssl/1.1.1b@sight/stable")

        if not tools.os_info.is_linux:
            self.requires("libpng/1.6.34-r1@sight/stable")
            self.requires("libjpeg/9c-r1@sight/stable")
            self.requires("freetype/2.9.1-r1@sight/stable")

    def build_requirements(self):
        if tools.os_info.is_windows:
            self.build_requires("jom/1.1.2-r1@sight/stable")

        if tools.os_info.linux_distro == "linuxmint":
            pack_names = [
                'libfontconfig1-dev',
                'libfreetype6-dev',
                'libx11-dev',
                'libxext-dev',
                'libxfixes-dev',
                'libxi-dev',
                'libxrender-dev',
                'libxcomposite-dev',
                'libxcursor-dev',
                'libxtst-dev',
                'libxkbcommon-dev',
                'libxkbcommon-x11-dev',
                'libxcb1-dev',
                'libx11-xcb-dev',
                'libxcb-glx0-dev',
                'libxcb-keysyms1-dev',
                'libxcb-image0-dev',
                'libxcb-shm0-dev',
                'libxcb-icccm4-dev',
                'libxcb-sync0-dev',
                'libxcb-xfixes0-dev',
                'libxcb-shape0-dev',
                'libxcb-randr0-dev',
                'libxcb-render-util0-dev',
                'libc6-dev',
                'libgstreamer1.0-dev',
                'libgstreamer-plugins-base1.0-dev',
                'libjpeg-turbo8-dev',
                'openssl'
            ]

            if tools.os_info.os_version.major(fill=False) == "18":
                pack_names += [
                    'libpng12-dev'
                ]
            elif tools.os_info.os_version.major(fill=False) == "19":
                pack_names += [
                    'libpng-dev'
                ]
            
            installer = tools.SystemPackageTool()
            for p in pack_names:
                installer.install(p)

    def system_requirements(self):
        if tools.os_info.linux_distro == "linuxmint":
            pack_names = [
                'libfontconfig1',
                'libfreetype6',
                'libxcb1',
                'libxcb-glx0',
                'libxcb-keysyms1',
                'libxcb-image0',
                'libxcb-shm0',
                'libxcb-icccm4',
                'libxcb-xfixes0',
                'libxcb-shape0',
                'libxcb-randr0',
                'libxcb-render-util0',
                'libgstreamer1.0-0',
                'libgstreamer-plugins-base1.0-0',
                'libjpeg-turbo8',
                'openssl'
            ]

            if tools.os_info.os_version.major(fill=False) == "18":
                pack_names += [
                    'libpng12-0'
                ]
            elif tools.os_info.os_version.major(fill=False) == "19":
                pack_names += [
                    'libpng16-16'
                ]
            
            installer = tools.SystemPackageTool()
            for p in pack_names:
                installer.install(p)

    def source(self):
        url = "http://download.qt.io/official_releases/qt/{0}/{1}/single/qt-everywhere-src-{1}"\
            .format(self.upstream_version[:self.upstream_version.rfind('.')], self.upstream_version)

        tools.get("%s.tar.xz" % url)
        shutil.move("qt-everywhere-src-%s" % self.upstream_version, "qt5")

    def build(self):

        # TODO: remove this once this patch from upstream is merged in Qt >= 5.12.2
        tools.patch(
            os.path.join(self.source_folder, "qt5", "qtdeclarative"),
            "patches/c++11.patch"
        )

        if tools.os_info.is_windows:
            tools.replace_in_file(
                os.path.join(self.source_folder, "qt5", "qtbase", "configure.json"),
                "-lzdll",
                "-l{0}".format(self.deps_cpp_info["zlib"].libs[0])
            )
            tools.replace_in_file(
                os.path.join(self.source_folder, "qt5", "qtbase", "src", "gui", "configure.json"),
                "-llibpng",
                "-l{0}".format(self.deps_cpp_info["libpng"].libs[0])
            )
            tools.replace_in_file(
                os.path.join(self.source_folder, "qt5", "qtbase", "src", "gui", "configure.json"),
                "-llibjpeg",
                "-l{0}".format(self.deps_cpp_info["libjpeg"].libs[0])
            )
            tools.replace_in_file(
                os.path.join(self.source_folder, "qt5", "qtbase", "src", "gui", "configure.json"),
                "-lfreetype",
                "-l{0}".format(self.deps_cpp_info["freetype"].libs[0])
            )

        # Since we removed sym links of libpng on macos, we need to tell qt to look for "libpng16d".
        elif tools.os_info.is_macos and self.settings.build_type == "Debug":
            tools.replace_in_file(
                os.path.join(self.source_folder, "qt5", "qtbase", "src", "gui", "configure.json"),
                "-lpng16",
                "-l{0}".format(self.deps_cpp_info["libpng"].libs[0])
            )

        args = [ "-shared", "-opensource", "-confirm-license", "-silent", "-nomake examples", "-nomake tests",
                "-prefix %s" % self.package_folder]

        if self.settings.build_type == "Debug":
            args.append("-debug")
        else:
            args.append("-release")

        # Increase compilation time, but significally decrease startup time, binaries size of Qt application
        # See https://wiki.qt.io/Performance_Tip_Startup_Time
        if tools.os_info.is_linux:
            args.append("-reduce-relocations")
        else:
            args.append("-ltcg")

        # Use optimized qrc, uic, moc... even in debug for faster build later
        args.append("-optimized-tools")

        args.append("-system-zlib")
        args.append("-system-libpng")
        args.append("-system-libjpeg")
        args.append("-system-freetype")

        # openGL
        args.append("-opengl desktop")

        # SSL
        args.append("-ssl")

        # Qt skip modules list
        args.append("-skip qtactiveqt")
        args.append("-skip qtconnectivity")
        args.append("-skip qtsensors")
        args.append("-skip qttranslations")
        args.append("-skip qtwayland")
        args.append("-skip qtwebchannel")
        args.append("-skip qtwebsockets")
        args.append("-skip qtserialport")
        args.append("-skip qtdoc")
        args.append("-skip qtlocation")

        if tools.os_info.is_windows:
            zlib_lib_paths = self.deps_cpp_info["zlib"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["zlib"].include_paths]
            args += [" ".join(["-L"+i for i in zlib_lib_paths])]

            libpng_lib_paths = self.deps_cpp_info["libpng"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["libpng"].include_paths]
            args += [" ".join(["-L"+i for i in libpng_lib_paths])]

            libjpeg_lib_paths = self.deps_cpp_info["libjpeg"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["libjpeg"].include_paths]
            args += [" ".join(["-L"+i for i in libjpeg_lib_paths])]

            freetype_lib_paths = self.deps_cpp_info["freetype"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["freetype"].include_paths]
            args += [" ".join(["-L"+i for i in freetype_lib_paths])]

            openssl_lib_paths = self.deps_cpp_info["openssl"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["openssl"].include_paths]
            args += [" ".join(["-L"+i for i in openssl_lib_paths])]

        elif tools.os_info.is_macos:
            libpng_lib_paths = self.deps_cpp_info["libpng"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["libpng"].include_paths]
            args += [" ".join(["-L"+i for i in libpng_lib_paths])]

            libjpeg_lib_paths = self.deps_cpp_info["libjpeg"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["libjpeg"].include_paths]
            args += [" ".join(["-L"+i for i in libjpeg_lib_paths])]

            freetype_lib_paths = self.deps_cpp_info["freetype"].lib_paths
            args += ["-I %s" % i for i in self.deps_cpp_info["freetype"].include_paths]
            args += [" ".join(["-L"+i for i in freetype_lib_paths])]

        if tools.os_info.is_windows:
            self._build_windows(args)
        else:
            self._build_unix(args)

        with open('qtbase/bin/qt.conf', 'w') as f:
            f.write('[Paths]\nPrefix = ..')

    def _build_windows(self, args):
        args.append("-mp")
        args.append("-no-angle")
        args.append("-mediaplayer-backend wmf")
        build_command = find_executable("jom.exe")
        if build_command:
            build_args = ["-j", str(tools.cpu_count())]
        else:
            build_command = "nmake.exe"
            build_args = []
        self.output.info("Using '%s %s' to build" % (build_command, " ".join(build_args)))

        if self.settings.compiler == "Visual Studio":
            if self.settings.compiler.version == "14":
                args.append("-platform win32-msvc2015")
            if self.settings.compiler.version == "15":
                args.append("-platform win32-msvc2017")

        args.append("-plugindir " + os.path.join(self.package_folder, "bin", "qt5", "plugins"))

        with tools.vcvars(self.settings):
            with tools.environment_append({"PATH": self.deps_cpp_info["zlib"].bin_paths}):
                self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)))
                self.run("%s %s > build.log" % (build_command, " ".join(build_args)))
                self.run("%s install > install.log" % build_command)

    def _build_unix(self, args):
        if tools.os_info.is_linux:
            args.append("-ccache")
            args.append("-fontconfig")
            args.append("-no-dbus")
            args.append("-c++std c++11")
            args.append("-qt-xcb")
            args.append("-gstreamer 1.0")
            if self.settings.arch == "x86":
                args += ["-xplatform linux-g++-32"]

        if tools.os_info.is_macos:
            args.append("-no-framework")
            args.append("-c++std c++11")
            args.append("-no-xcb")
            args.append("-no-glib")
            if self.settings.arch == "x86":
                args += ["-xplatform macx-clang-32"]

        args.append("-plugindir " + os.path.join(self.package_folder, "lib", "qt5", "plugins"))

        with tools.environment_append({"MAKEFLAGS":"-j %d" % tools.cpu_count()}):
            self.output.info("Using '%d' threads" % tools.cpu_count())
            self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)))
            self.run("make ")
            self.run("make install > install.log")

    def package(self):
        self.copy("bin/qt.conf", src="qtbase")

        if self.settings.os == "Windows":
            self.copy("*.dll", dst="bin", src=self.deps_cpp_info["zlib"].bin_paths[0])

    def package_info(self):
        if self.settings.os == "Windows":
            self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
