"""
Based on TSC SP8 FALCON File Format Description - LAS X Version 3.5.0.pdf
https://github.com/AllenCellModeling/aicsimageio/discussions/484#discussioncomment-5578771
https://drive.google.com/file/d/1qsGqlKry-HSXQqbOxq6tHix_98Ssig66/view?usp=sharing
and
https://github.com/rharkes/RawLIFreader
"""

import logging
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union, IO

from lxml import etree


def getconstants() -> dict[str, str]:
    return {
        "CBHi": "0x70",  # Common Block Header identifier(112)
        "MBHi": "0x2A",  # Metadata Block Header identifier(42)
        "LBBHi": "0x2A",  # LIF Binary Block Header identifier (42)
        "Leica Object File": ".lof",
        "Extended Leica Image Files": ".xlif",
        "Extended Leica File": ".xlef",
        "Leica Image File": ".lif",
    }


def _read64bit(fp:IO[bytes]) -> int:
    return int(struct.unpack("<Q", fp.read(8))[0])


def _read32bit(fp:IO[bytes]) -> int:
    return int(struct.unpack("<L", fp.read(4))[0])


def _read16bit(fp:IO[bytes]) -> int:
    return int(struct.unpack("<H", fp.read(2))[0])


def _read8bit(fp:IO[bytes]) -> int:
    return int(struct.unpack("<B", fp.read(1))[0])


@dataclass
class MemBlock:
    size: int
    memblockid: str
    xml: etree._Element


@dataclass
class BinaryBlockHeader:
    datasize: int
    offset: int
    identifier: str

    def getdata(self, fp:IO[bytes])->bytes:
        fp.seek(self.offset)
        return fp.read(self.datasize)


class LifFile:
    def __init__(self, filepath: Union[str, os.PathLike[Any]]) -> None:
        # open file
        if isinstance(filepath, str):
            self.path = Path(filepath)
        elif isinstance(filepath, Path):
            self.path = filepath
        else:
            raise ValueError("not a valid filename")
        if self.path.suffix != ".lif":
            raise ValueError("Not a valid extension")
        self.log = logging.getLogger("LifFile")
        self.binaryblocks = []

        with open(self.path, "rb") as fp:
            self.xml = etree.fromstring(self._readmetadatablock(fp).decode("utf-16"))
            while fp.tell() < self.path.stat().st_size:
                self.binaryblocks.append(self._getbinaryblockheader(fp))
        self.memblocks = self._getelementsfromxml()

    def _getelementsfromxml(self) -> list[MemBlock]:
        foundelements = self.xml.xpath("//Element")
        memblocks = []
        if isinstance(foundelements, list):
            elements = [x for x in foundelements if isinstance(x, etree._Element)]
            for element in elements:
                foundmem = element.xpath("Memory")
                if isinstance(foundmem, list):
                    mem = [x for x in foundmem if isinstance(x, etree._Element)]
                    memblocks.append(
                        MemBlock(
                            size=int(mem[0].attrib["Size"]),
                            memblockid=str(mem[0].attrib["MemoryBlockID"]),
                            xml=element,
                        )
                    )
        return memblocks

    def getbinaryblockdata(self, blockindex: Union[str, int])->bytes:
        if isinstance(blockindex, str):
            blocks = [x for x in self.binaryblocks if x.identifier == blockindex]
            if len(blocks) != 1:
                raise ValueError(f"BlockIndex {blockindex} not found")
            block = blocks[0]
        else:
            block = self.binaryblocks[blockindex]
        with open(self.path, "rb") as fp:
            return block.getdata(fp)

    def _getbinaryblockheader(self, fp:IO[bytes]) -> BinaryBlockHeader:
        self._readcommonblockheader(fp)
        const = getconstants()
        lbbhi = int(const["LBBHi"], 16)
        if lbbhi != _read8bit(fp):
            self.log.error("LIF Binary Block Header identifier")
            raise AssertionError
        bdsize = _read64bit(fp)
        if lbbhi != _read8bit(fp):
            self.log.error("LIF Binary Block Header identifier")
            raise AssertionError
        bdisize = _read32bit(fp)
        bindatid = str(fp.read(bdisize * 2).decode("utf-16"))
        offset = fp.tell()
        fp.seek(bdsize, 1)
        return BinaryBlockHeader(datasize=bdsize, offset=offset, identifier=bindatid)

    def _readmetadatablock(self, fp:IO[bytes])->bytes:
        self._readcommonblockheader(fp)
        mbhsize = self._readmetadatablockheader(fp)
        return fp.read(mbhsize * 2)

    def _readmetadatablockheader(self, fp:IO[bytes]) -> int:
        const = getconstants()
        mbhi = int(const["MBHi"], 16)
        if _read8bit(fp) != mbhi:
            self.log.error("Common Block Headeridentifier incorrect")
            raise AssertionError
        return _read32bit(fp)

    def _readcommonblockheader(self, fp:IO[bytes]) -> int:
        const = getconstants()
        cbhi = int(const["CBHi"], 16)
        if _read32bit(fp) != cbhi:
            self.log.error("Common Block Headeridentifier incorrect")
            raise AssertionError
        return _read32bit(fp)
