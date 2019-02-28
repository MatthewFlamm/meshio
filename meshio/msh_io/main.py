# -*- coding: utf-8 -*-
#
from ctypes import c_int, sizeof
import struct
from . import msh2, msh4_0, msh4_1

versions = {"2": msh2, "4.0": msh4_0, "4.1": msh4_1, "4": msh4_1}


def read(filename):
    """Reads a Gmsh msh file.
    """
    with open(filename, "rb") as f:
        mesh = read_buffer(f)
    return mesh


def read_buffer(f):
    # The various versions of the format are specified at
    # <http://gmsh.info//doc/texinfo/gmsh.html#File-formats>.

    line = f.readline().decode("utf-8")
    assert line.strip() == "$MeshFormat"
    int_size = sizeof(c_int)
    format_version, data_size, is_ascii = _read_header(f, int_size)

    try:
        version = versions[format_version]
    except KeyError:
        try:
            version = versions[format_version.split(".")[0]]
        except KeyError:
            raise ValueError(
                "Need mesh format in {} (got {})".format(
                    versions.keys(), format_version
                )
            )

    return version.read_buffer(f, is_ascii, int_size, data_size)


def _read_header(f, int_size):
    """Read the mesh format block

    specified as

     version(ASCII double; currently 4.1)
       file-type(ASCII int; 0 for ASCII mode, 1 for binary mode)
       data-size(ASCII int; sizeof(size_t))
     < int with value one; only in binary mode, to detect endianness >

    though here the version is left as str
    """

    # http://gmsh.info/dev/doc/texinfo/gmsh.html#MSH-file-format-_0028version-4_0029

    line = f.readline().decode("utf-8")
    # Split the line
    # 4.1 0 8
    # into its components.
    str_list = list(filter(None, line.split()))
    format_version = str_list[0]
    assert str_list[1] in ["0", "1"]
    is_ascii = str_list[1] == "0"
    data_size = int(str_list[2])
    if not is_ascii:
        # The next line is the integer 1 in bytes. Useful for checking
        # endianness. Just assert that we get 1 here.
        one = f.read(int_size)
        assert struct.unpack("i", one)[0] == 1
        line = f.readline().decode("utf-8")
        assert line == "\n"
    line = f.readline().decode("utf-8")
    assert line.strip() == "$EndMeshFormat"
    return format_version, data_size, is_ascii


def write(filename, mesh, format_version, write_binary=True):

    try:
        version = versions[format_version]
    except KeyError:
        try:
            version = versions[format_version.split(".")[0]]
        except KeyError:
            raise ValueError(
                "Need mesh format in {} (got {})".format(
                    versions.keys(), format_version
                )
            )

    version.write(filename, mesh, write_binary=write_binary)
