# pdfassort

PDFの盛り合わせ (PDF Assort)

CSVで検索キーワードと出力ファイル名の組み合わせを指定し、PDFのファイル群を調べてキーワードが含まれるページを集めて出力ファイルにまとめる。

Specify combinations of search keywords and output file names in a CSV
file, examine PDF files, collect pages containing keywords, and
combine them in an output file.

## Usage

`pdfassort.py -h`で表示されるメッセージを確認ください。

Sorry, help messages are Japanese only.

## Dependent Packages

* pdfminer.six
* PyPDF2
* chardet

## Miscellaneous

仮想PDFプリンタ (CubePDFやMicrosoft Print to PDFなど) で出力されたPDFは解析に時間がかかるようです。プログラム直接出力のPDFを用意しましょう。

It seems that analysis of PDF files output by virtual PDF printer
(CubePDF, Microsoft Print to PDF, etc.) takes time.  Prepare PDF files
output directly from the program.

テキスト解析できないPDF (例えばスキャンされたものとか、保護されたものなど) は、ファイル名にキーを含めましょう。

Include a key in the file name for PDF files that can not be parsed
(for example, scanned or protected).
