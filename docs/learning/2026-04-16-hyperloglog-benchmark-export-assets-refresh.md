# HyperLogLog benchmark export assets refresh

## Python refresh
- `csv.writer` is the simplest standard-library path for stable tabular exports.
- `io.StringIO` lets the CLI render CSV text before writing it to disk.
- Raw SVG is just XML text, so a small helper can keep text escaping and repeated label styling consistent.

## Mini self-test
1. If benchmark rows already contain observed error, theory bound, precision, and dense bytes, can both CSV and SVG be derived without rerunning simulations differently?  
   - Yes. They are pure presentation layers over the existing report structure.
2. What is the safest low-dependency export format for a portfolio chart in a Python-only repo?  
   - Self-contained SVG.
3. What should the x-axis labels communicate for interview value?  
   - Precision plus the dense-memory cost, because that turns the chart into a clear accuracy-vs-space conversation.

## Slice rule
Keep the new export outputs deterministic and dependency-free.
