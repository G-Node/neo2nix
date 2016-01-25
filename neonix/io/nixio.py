# Copyright (c) 2014, German Neuroinformatics Node (G-Node)
#                     Achilleas Koutsou <achilleas.k@gmail.com>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted under the terms of the BSD License. See
# LICENSE file in the root of the Project.

from __future__ import absolute_import

import numpy as np
import quantities as pq

from neo.io.baseio import BaseIO
from neo.core import Block, Segment

try:
    import nix
except ImportError:
    raise ImportError("Failed to import NIX (NIXPY not found). "
                      "The NixIO requires the Python bindings for NIX.")


attribute_mappings = {"name": "name",
                      "description": "definition"}
container_mappings = {"segments": "groups"}


class NixIO(BaseIO):
    """
    Class for reading and writing NIX files.
    """

    is_readable = False  # for now
    is_writable = True

    supported_objects = [Block, Segment]
    readable_objects = []
    writeable_objects = [Block, Segment]

    name = "NIX"
    extensions = ["h5"]
    mode = "file"

    def __init__(self, filename=None):
        """
        Initialise IO instance.

        :param filename: full path to the file
        :return:
        """
        BaseIO.__init__(self, filename=filename)

    def write_block(self, neo_block, cascade=True):
        """
        Write the provided block to the self.filename

        :param neo_block: Neo block to be written
        :param cascade: save all child objects (default: True)
        :return:
        """
        nix_name = neo_block.name
        nix_type = "neo.block"
        nix_definition = neo_block.description
        nix_file = nix.File.open(self.filename, nix.FileMode.Overwrite)
        nix_block = nix_file.create_block(nix_name, nix_type)
        nix_block.definition = nix_definition
        if cascade:
            for segment in neo_block.segments:
                self.write_segment(segment, neo_block)
        nix_file.close()

    def write_segment(self, segment, parent_block, cascade=True):
        """
        Write the provided segment to the self.filename

        :param segment: Neo segment to be written
        :param parent_block: The parent neo block of the provided segment
        :param cascade: True/False save all child objects (default: True)
        :return:
        """
        nix_name = segment.name
        nix_type = "neo.segment"
        nix_definition = segment.description
        nix_file = nix.File.open(self.filename, nix.FileMode.ReadWrite)
        for nix_block in nix_file.blocks:
            if NixIO._equals(parent_block, nix_block, False):
                nix_block = nix_file.blocks[0]
                nix_group = nix_block.create_group(nix_name, nix_type)
                nix_group.definition = nix_definition
                break
        else:
            raise LookupError("Parent block with name '{}' for segment with "
                              "name '{}' does not exist in file '{}'.".format(
                                parent_block.name, segment.name, self.filename))
        nix_file.close()

    @staticmethod
    def _equals(neo_obj, nix_obj, cascade=True):
        """
        Returns 'true' if the attributes of the neo object (neo_obj) match the
        attributes of the nix object (nix_obj)

        :param neo_obj: a neo object (block, segment, etc.)
        :param nix_obj: a nix object to compare to (block, group, etc.)
        :param cascade: test all child objects for equivalence recursively
                        (default: True)
        :return: true if the attributes of the two objects, as defined in the
         object mapping, are identical
        """
        for neo_attr_name, nix_attr_name in attribute_mappings.items():
            neo_attr = getattr(neo_obj, neo_attr_name, None)
            nix_attr = getattr(nix_obj, nix_attr_name, None)
            if neo_attr != nix_attr:
                return False
        if cascade:
            for neo_container_name, nix_container_name\
                    in container_mappings.items():
                neo_container = getattr(neo_obj, neo_container_name, None)
                nix_container = getattr(nix_obj, nix_container_name, None)
                if not (neo_container is nix_container is None):
                    if len(neo_container) != len(nix_container):
                        return False
                    for neo_child_obj, nix_child_obj in zip(neo_container,
                                                            nix_container):
                        if not NixIO._equals(neo_child_obj, nix_child_obj):
                            return False
        return True


