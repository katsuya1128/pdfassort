# pdfassort

PDFの盛り合わせ (PDF Assort)

CSVで検索キーワードと出力ファイル名の組み合わせを指定し、PDFのファイル群を調べてキーワードが含まれるページを集めて出力ファイルにまとめる。

## 使い方

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

## 依存しているパッケージ

* pdfminer.six
* PyPDF2
* chardet

## その他

仮想PDFプリンタ (CubePDFやMicrosoft Print to PDFなど) で出力されたPDFは解析に時間がかかるようです。プログラム直接出力のPDFを用意しましょう。

テキスト解析できないPDF (例えばスキャンされたものとか、保護されたものなど) は、ファイル名にキーを含めましょう。
