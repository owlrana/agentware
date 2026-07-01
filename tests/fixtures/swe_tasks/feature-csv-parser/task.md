# Task: Implement CSV Row Parser

The file `csv_parser.py` contains a stub `parse_row` function. Implement it so
that it correctly parses a single CSV row string into a list of field values.

Requirements:
1. Fields are comma-separated.
2. A field enclosed in double quotes may contain commas (they are literal, not delimiters).
3. Inside a quoted field, two consecutive double-quotes ("") represent a single literal double-quote character.
4. Leading/trailing whitespace around unquoted fields should be stripped.
5. Quoted fields preserve their internal whitespace as-is (do not strip).
6. An empty string input returns an empty list.
