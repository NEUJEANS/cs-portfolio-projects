# 2026-04-14 Huffman Compressor Research

Goal: add another portfolio project that highlights core CS ideas rather than only CRUD or filesystem tooling.

## Quick findings
- Huffman coding is one of the clearest student-friendly examples of a greedy algorithm with a real compression use case.
- It naturally demonstrates priority queues, binary trees, bit packing, and reversible encoding/decoding.
- A small CLI implementation is realistic to finish in one vertical slice while still feeling substantial on a portfolio.

## Chosen scope for this slice
- build a Python CLI that compresses and decompresses files
- store frequency-table metadata in a simple archive header
- support binary-safe round trips
- include tests for happy path and invalid input handling

## Why this is a good next addition
- increases algorithmic breadth in the repo
- complements the existing CLI/system projects with a textbook-to-practice example
- stays resumable: future slices can add canonical codes, streaming, and better archive statistics
