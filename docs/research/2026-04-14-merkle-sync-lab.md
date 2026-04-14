# Merkle Sync Lab Research

## Goal
Create a compact portfolio project that demonstrates how Merkle-tree-style hashing can summarize directory state and speed up change detection.

## Practical references from prior knowledge
- Git stores content by hash and relies on tree objects to summarize directory state.
- Merkle trees are a standard way to prove or compare large state efficiently in distributed systems and storage systems.
- For a student portfolio slice, a deterministic file-tree manifest plus diff reporting is enough to show the core idea clearly without needing a full network protocol.

## Chosen scope for this slice
- hash each file with SHA-256
- build parent directory digests from sorted child entries
- save manifests as JSON for reproducible comparisons
- diff two directories or manifests and report added / removed / changed paths

## Why this is a good portfolio addition
- adds a recognizable systems/data-integrity topic that complements the repo's existing CLI and algorithm projects
- is easy to demo locally in an interview
- leaves clear room for advanced follow-ups such as chunking, proof paths, and sync planning
