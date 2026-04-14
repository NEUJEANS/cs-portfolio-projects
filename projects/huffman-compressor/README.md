# Huffman Compressor

A Python command-line program that compresses and decompresses files using Huffman coding. It is a strong CS portfolio project because it shows data structures, greedy algorithms, binary serialization, and test-driven CLI work in one compact repo slice.

## Features
- compresses any non-empty file into a `.huf` archive
- reconstructs the Huffman tree from frequency metadata during decompression
- preserves original byte content for text or binary files
- validates archive format and decoded output size
- keeps the implementation dependency-free

## Usage
```bash
python3 huffman_compressor.py compress sample.txt
python3 huffman_compressor.py compress image.bin -o image_archive.huf
python3 huffman_compressor.py decompress sample.txt.huf
python3 huffman_compressor.py decompress image_archive.huf -o restored.bin
```

## Run tests
```bash
python3 -m unittest test_huffman_compressor.py
```

## Why it matters for a portfolio
- demonstrates heap-based tree construction with `heapq`
- shows binary file IO and compact metadata design
- includes CLI ergonomics and automated regression tests
- creates a useful bridge between textbook algorithms and practical software engineering

## Future improvements
- add archive statistics such as compression ratio and entropy estimates
- support streaming large files in chunks
- add canonical Huffman codes to reduce header size further
