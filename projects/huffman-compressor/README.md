# Huffman Compressor

A Python command-line program that compresses and decompresses files using Huffman coding. It is a strong CS portfolio project because it shows data structures, greedy algorithms, binary serialization, and test-driven CLI work in one compact repo slice.

## Features
- compresses any non-empty file into a `.huf` archive
- reconstructs the Huffman tree from frequency metadata during decompression
- preserves original byte content for text or binary files
- validates archive format and decoded output size
- prints compression statistics including ratio, entropy estimate, and average bits per symbol
- inspects archive metadata without fully decompressing the payload
- keeps the implementation dependency-free

## Usage
```bash
python3 huffman_compressor.py compress sample.txt
python3 huffman_compressor.py compress sample.txt --stats
python3 huffman_compressor.py compress image.bin -o image_archive.huf --stats
python3 huffman_compressor.py inspect image_archive.huf
python3 huffman_compressor.py decompress sample.txt.huf
python3 huffman_compressor.py decompress image_archive.huf -o restored.bin --stats
```

## Sample statistics output
```text
Statistics:
  Original size: 110 bytes
  Archive size: 180 bytes
  Header size: 132 bytes
  Encoded payload size: 48 bytes
  Unique symbols: 19
  Bit length: 379
  Average bits/symbol: 3.445
  Entropy estimate: 3.351 bits/symbol
  Compression ratio: 1.636 (163.64%)
  Space savings: -0.636 (-63.64%)
```

Small files can still grow after compression because the archive stores a frequency table header. That trade-off is useful to surface in a portfolio project because it shows realistic engineering analysis instead of only happy-path algorithms.

## Run tests
```bash
python3 -m unittest test_huffman_compressor.py
```

## Why it matters for a portfolio
- demonstrates heap-based tree construction with `heapq`
- shows binary file IO and compact metadata design
- includes CLI ergonomics, instrumentation, and automated regression tests
- creates a useful bridge between textbook algorithms and practical software engineering
- explains algorithmic limits with entropy-based reporting rather than treating compression like magic

## Future improvements
- support streaming large files in chunks
- add canonical Huffman codes to reduce header size further
- compare the current archive format against alternative header strategies
