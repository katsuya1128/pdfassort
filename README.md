# pdfassort.py - PDFの盛り合わせ (PDF Assort)

CSVで検索キーワードと出力ファイル名の組み合わせを指定し、PDFのファイル群を調べて
キーワードが含まれるページを集めて出力ファイルにまとめる。

Specify combinations of search keywords and output file names in a CSV file,
examine PDF files, collect pages containing keywords,
and combine them in an output file.

## Usage

```text
usage: pdfassort.py [-h] [-v] [-o OUTPUT_DIR] [-ns] [-nf] CSV PDF [PDF ...]

pdfassort.py -- PDFの盛り合わせ v0.1a (2019/05/15)

        CSVによるリストとPDFの内容に基づきPDFファイルを仕分けする。
        sort PDF pages according to CSV list and PDF contents.

positional arguments:
  CSV                   CSVによるキーと出力ファイル名のリスト
                        list of keywords and output file names in CSV
  PDF                   PDFファイル
                        PDF files

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         処理の進捗表示を詳細にする
                        verbose mode
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        出力ディレクトリ, default: '.'
                        output directory, default: '.'
  -ns, --no-skip-csv-header
                        CSVファイルのヘッダ行 (1行目) をスキップしない
                        don't skip header (first) line in CSV file
  -nf, --no-fast-mode   ファイル名にキーが含まれていても無視する
                        default: ファイル名にキーが含まれていたらファイル全体を追加し
                        ファイルの内容は見ない
                        ignore even if the file name contains keywords
                        default: if the file name contains a key,
                        add the whole file and do not see the file contents
```
