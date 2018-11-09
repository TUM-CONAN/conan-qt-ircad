#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from distutils.spawn import find_executable
import os
import shutil

class QtConan(ConanFile):

    name = "qt"
    version = "5.11.2"
    description = "Qt library."
    url = "https://gitlab.lan.local/conan/conan-qt"
    homepage = "https://www.qt.io/"
    license = "http://doc.qt.io/qt-5/lgpl.html"
    settings = "os", "arch", "compiler", "build_type"
    short_paths = True
    no_copy_source = False

    def configure(self):
        del self.settings.compiler.libcxx
        if 'CI' not in os.environ:
            os.environ["CONAN_SYSREQUIRES_MODE"] = "verify"

    def requirements(self):
        if tools.os_info.is_windows:
            self.requires("zlib/1.2.11@sight/stable")
            
        if not tools.os_info.is_linux:
            self.requires("libpng/1.6.34@sight/stable")
            self.requires("libjpeg/9c@sight/stable")
            self.requires("freetype/2.9.1@sight/stable")

    def build_requirements(self):
        if tools.os_info.is_windows:
            self.build_requires("jom/1.1.2@sight/stable")

        if tools.os_info.linux_distro == "linuxmint":
            pack_names = [
                "libxcb1-dev", "libx11-dev", "libc6-dev", "libgl1-mesa-dev", 
                "libgstreamer1.0-dev", "libgstreamer-plugins-base1.0-dev",
                "libpng-dev", "libjpeg-turbo8-dev", "libfreetype6-dev", 
                "libfontconfig1-dev"
            ]
            installer = tools.SystemPackageTool()
            for p in pack_names:
                installer.install(p)

    def system_requirements(self):
        if tools.os_info.linux_distro == "linuxmint": 
            pack_names = [
                "libxcb1", "libx11-6", "libgstreamer1.0-0", "libgstreamer-plugins-base1.0-0",
                "libpng16-16", "libjpeg-turbo8", "libfreetype6", "libfontconfig1"
            ]
            installer = tools.SystemPackageTool()
            for p in pack_names:
                installer.install(p)

    def source(self):
        url = "http://download.qt.io/official_releases/qt/{0}/{1}/single/qt-everywhere-src-{1}"\
            .format(self.version[:self.version.rfind('.')], self.version)
        
        tools.get("%s.tar.xz" % url)
        shutil.move("qt-everywhere-src-%s" % self.version, "qt5")

    def build(self):
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

        args = [ "-shared", "-opensource", "-confirm-license", "-silent", "-nomake examples", "-nomake tests",
                "-prefix %s" % self.package_folder]

        if self.settings.build_type == "Debug":
            args.append("-debug")
        else:
            args.append("-release")

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
        
        if tools.os_info.is_macos:
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
