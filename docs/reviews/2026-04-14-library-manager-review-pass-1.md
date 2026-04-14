# Library Manager Review Pass 1 — 2026-04-14

## Focus
Domain model and state transitions.

## Issue found
The original project only flipped an `available` flag, which made the checkout flow too shallow to feel like a real circulation system.

## Fix applied
Added borrower, checkout date, due date, return flow, search, and overdue reporting so the project demonstrates richer state transitions and query behavior.

## Result
The project now reads like a real mini-system instead of a CRUD stub.
