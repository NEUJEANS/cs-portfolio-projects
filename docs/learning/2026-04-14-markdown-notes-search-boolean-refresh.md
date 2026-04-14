# Markdown Notes Search Boolean Query Refresh

Date: 2026-04-14

## Refresh focus
- shunting-yard style parsing to respect operator precedence
- postfix evaluation with unary `NOT`
- keeping phrase matching simple via quoted substring terms

## Tiny self-test
Target expression:

`(graph OR tree) AND NOT archived`

Expected behavior:
- matches notes containing `graph` unless they also contain `archived`
- matches notes containing `tree` unless they also contain `archived`
- honors parentheses before outer `AND`

Implementation choice passed this self-test through automated unit coverage.
