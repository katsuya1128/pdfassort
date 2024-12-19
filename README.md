# pdfassort

[日本語](README.ja.md)

PDF Assort

Specify combinations of search keywords and output file names in a CSV
file, examine PDF files, collect pages containing keywords, and
combine them in an output file.

## Usage

pdfassort.py [-h] [-v] [-o *OUTPUT_DIR*] [-c] [-ns] [-nf] [-l *LOG_FILE*] *CSV* *PDF* [*PDF* ...]

| Option Flag | Description |
| :--- | :---- |
| -h, --help |  show help message end exit |
| -v, --verbose | verbose mode |
| -o *OUTPUT_DIR*, --output-dir *OUTPUT_DIR* | output directory, default: `.` |
| -c, --auto-char-detect |  auto character detect in CSV file |
| -ns, --no-skip-csv-header | don't skip fist line in CSV file |
| -nf, --no-fast-mode | parse file if file name has any key |
| -l *LOG_FILE* | output to *LOG_FILE* |

## Dependent Packages

* pdfminer.six
* pypdf
* chardet

## Miscellaneous

It seems that analysis of PDF files output by virtual PDF printer
(CubePDF, Microsoft Print to PDF, etc.) takes time.  Prepare PDF files
output directly from the program.

Include a key in the file name for PDF files that can not be parsed
(for example, scanned or protected).
