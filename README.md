# PyRawLifReader
Simple reader for raw lif data. Will not encode anything to an image. Just gives metadata and bytes.

It is a python version of https://github.com/rharkes/RawLIFreader which was written for Matlab.
## Installation
````commandline
pip install .
````
## Examples
Export all metadata as xml:
```python
from lxml import etree
from pyrawlifreader import LifFile
liff = LifFile(r'c:\mylif.lif')
with open('metadata.xml', 'wt') as fp:
    fp.write(etree.tostring(liff.xml).decode('utf-8'))
```
Show xml of a single memoryblock:
```python
from lxml import etree
from pyrawlifreader import LifFile
liff = LifFile(r'c:\mylif.lif')
print(etree.tostring(liff.memblocks[6].xml).decode('utf-8'))
```
Load data from memoryblock
```python
from pyrawlifreader import LifFile
liff = LifFile(r'c:\mylif.lif')
data = liff.getbinaryblockdata('MemBlock_2644')
data2 = liff.getbinaryblockdata(1)
```