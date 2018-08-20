#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from distutils.spawn import find_executable
import os
import shutil
import configparser

class QtConan(ConanFile):

    name = "qt"
    version = "5.11.1"
    description = "Qt library."
    url = "https://gitlab.lan.local/conan/conan-qt"
    homepage = "https://www.qt.io/"
    license = "http://doc.qt.io/qt-5/lgpl.html"
    settings = "os", "arch", "compiler"
    no_copy_source = True
    short_paths = True

    def requirements(self):
        if not tools.os_info.is_linux:
            self.requires("zlib/1.2.11@fw4spl/stable")
            self.requires("libpng/1.6.34@fw4spl/stable")
            self.requires("libjpeg/9c@fw4spl/stable")
            self.requires("freetype/2.9.1@fw4spl/stable")

    def build_requirements(self):
        pack_names = []
        if tools.os_info.linux_distro == "ubuntu" or tools.os_info.linux_distro == "debian": 
            pack_names = ["libxcb1-dev", "libx11-dev", "libc6-dev", "libgl1-mesa-dev", 
                          "libgstreamer-1.0-dev", "libgstreamer-plugins-base1.0-dev"]

        if self.settings.arch == "x86":
            pack_names = [item+":i386" for item in pack_names]

        if pack_names:
            installer = tools.SystemPackageTool()
            installer.install(" ".join(pack_names)) # Install the package


    def system_requirements(self):
        pack_names = []
        if tools.os_info.linux_distro == "ubuntu" or tools.os_info.linux_distro == "debian": 
            pack_names = ["libxcb1", "libx11-6", "libgstreamer1.0-0", "libgstreamer-plugins-base1.0-0"]

        if self.settings.arch == "x86":
            pack_names = [item+":i386" for item in pack_names]

        if pack_names:
            installer = tools.SystemPackageTool()
            installer.install(" ".join(pack_names)) # Install the package

    def source(self):
        url = "http://download.qt.io/official_releases/qt/{0}/{1}/single/qt-everywhere-src-{1}"\
            .format(self.version[:self.version.rfind('.')], self.version)
        if tools.os_info.is_windows:
            tools.get("%s.zip" % url)
        else:
            self.run("wget -qO- %s.tar.xz | tar -xJ " % url)
        shutil.move("qt-everywhere-src-%s" % self.version, "qt5")

    def build(self):
        args = [ "-shared", "-opensource", "-confirm-license", "-silent", "-nomake examples", "-nomake tests",
                "-prefix %s" % self.package_folder]

        if self.settings.build_type == "Debug":
            args.append("-debug")
        else:
            args.append("-release")

        args.append("-no-fontconfig")
        args.append("-system-zlib")
        args.append("-system-libpng")
        args.append("-system-libjpeg")
        args.append("-system-freetype")

        # openGL
        args.append("-opengl desktop")

        # openSSL
        args.append("-no-openssl")

        # Qt skip modules list
        args.append("-skip qtactiveqt")
        args.append("-skip qtconnectivity")
        args.append("-skip qtsensors")
        args.append("-skip qttranslations")
        args.append("-skip qtwayland")
        args.append("-skip qtwebengine")
        args.append("-skip qtwebchannel")
        args.append("-skip qtwebsockets")
        args.append("-skip qtdeclarative")
        args.append("-skip qtquickcontrols")
        args.append("-skip qtcanvas3d")
        args.append("-skip qtgraphicaleffects")
        args.append("-skip qtscript")
        args.append("-skip qtserialport")
        args.append("-skip qtdoc")
        args.append("-skip qtlocation")

        if not tools.os_info.is_linux:
            args.append("-I %s" % i for i in self.deps_cpp_info["zlib"].include_paths)
            zlib_libs = self.deps_cpp_info["zlib"].libs
            zlib_lib_paths = self.deps_cpp_info["zlib"].lib_paths
            os.environ["ZLIB_LIBS"] = " ".join(["-L"+i for i in zlib_lib_paths] + ["-l"+i for i in zlib_libs])

            args.append("-I %s" % i for i in self.deps_cpp_info["libpng"].include_paths)
            libpng_libs = self.deps_cpp_info["libpng"].libs
            libpng_lib_paths = self.deps_cpp_info["libpng"].lib_paths
            os.environ["LIBPNG_LIBS"] = " ".join(["-L"+i for i in libpng_lib_paths] + ["-l"+i for i in libpng_libs])

            args.append("-I %s" % i for i in self.deps_cpp_info["libjpeg"].include_paths)
            libjpeg_libs = self.deps_cpp_info["libjpeg"].libs
            libjpeg_lib_paths = self.deps_cpp_info["libjpeg"].lib_paths
            os.environ["LIBJPEG_LIBS"] = " ".join(["-L"+i for i in libjpeg_lib_paths] + ["-l"+i for i in libjpeg_libs])

            args.append("-I %s" % i for i in self.deps_cpp_info["freetype"].include_paths)
            freetype_libs = self.deps_cpp_info["freetype"].libs
            freetype_lib_paths = self.deps_cpp_info["freetype"].lib_paths
            os.environ["FREETYPE_LIBS"] = " ".join(["-L"+i for i in freetype_lib_paths] + ["-l"+i for i in freetype_libs])
        
        if self.options.config:
            args.append(str(self.options.config))
            
        if self.settings.os == "Windows":
            self._build_windows(args)
        else:
            self._build_unix(args)
            
        with open('qtbase/bin/qt.conf', 'w') as f: 
            f.write('[Paths]\nPrefix = ..')

    def _build_windows(self, args):
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
                env.update({'QMAKESPEC': 'win32-msvc2015'})
                args += ["-platform win32-msvc2015"]
            if self.settings.compiler.version == "15":
                env.update({'QMAKESPEC': 'win32-msvc2017'})
                args += ["-platform win32-msvc2017"]


        with tools.vcvars(self.settings):
            self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)))
            self.run("%s %s" % (build_command, " ".join(build_args)))
            self.run("%s install" % build_command)

    def _build_unix(self, args):
        if self.settings.os == "Linux":
            args.append("-no-dbus")
            args.append("-c++std c++11")
            args.append("-qt-xcb")
            args.append("-gstreamer 1.0")
            if self.settings.arch == "x86":
                args += ["-xplatform linux-g++-32"]
        else:
            args.append("-no-framework")
            args.append("-c++std c++11")
            args.append("-no-xcb")
            args.append("-no-fontconfig")
            args.append("-no-glib")
            if self.settings.arch == "x86":
                args += ["-xplatform macx-clang-32"]

        with tools.environment_append({"MAKEFLAGS":"-j %d" % tools.cpu_count()}):
            self.output.info("Using '%d' threads" % tools.cpu_count())
            self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)))
            self.run("make")
            self.run("make install")

    def package(self):
        self.copy("bin/qt.conf", src="qtbase")

    def package_info(self):
        if self.settings.os == "Windows":
            self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
