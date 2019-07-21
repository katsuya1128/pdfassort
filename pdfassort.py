#!/usr/bin/python3
#
# Copyright (c) 2019 Katsuya
#

VERSION = "v0.2a (2019/07/05)"
AUTHOR = "Katsuya"

f"""
pdfassort.py -- PDFの盛り合わせ {VERSION}

CSVで検索キーワードと出力ファイル名の組み合わせを指定し、PDFのファイル群を調べて
キーワードが含まれるページを集めて出力ファイルにまとめる。
"""

"""
## 設計メモ

pdfminer.sixでテキストを解析して、PyPDF2で連結・出力する。

### 解析

PDFを解析して以下の構造に組み立てる。

```
{key1:
    {in_file1: [p1, p2, ...]},
    {in_file2: [p1, p2, ...]},
    ...},

{key2:
    {in_file1: [p1, p2, ...]},
    {in_file2: [p1, p2, ...]},
    ...},
...

```

### 出力

構造に基づいてファイルを集約する。

* in_fileのテキストにkeyが含まれているページはout_fileに。

## 必要なパッケージ

* pdfminer.six
* PyPDF2
* chardet (pdfminerでも使用している)

### パッケージインストール方法

```
$ pip isntall pdfminer.six PyPDF2 chardet
```

### その他

仮想PDFプリンタ (CubePDFやMicrosoft Print to PDFなど) で出力されたPDFは
解析に時間がかかるようです。
プログラム直接出力のPDFを用意しましょう。

テキスト解析できないPDF (例えばスキャンされたものとか、保護されたものなど) は、
ファイル名にキーを含めましょう。
"""

# バーバスモード
VERBOSE = 0

# デフォルトの出力先ディレクトリ
OUT_DIR = "."

# ファイル構造のデータベース
PDF_PAGES = {}

import sys
import io
import os.path
import argparse
from argparse import RawDescriptionHelpFormatter, RawTextHelpFormatter
import glob
import csv
import chardet

from PyPDF2 import PdfFileReader, PdfFileWriter

# リダイレクト時も UTF=8 に
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="UTF-8")

# Some code from https://qiita.com/mczkzk/items/894110558fb890c930b5

from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTContainer, LTTextBox
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage

def find_textboxes_recursively(layout_obj):
    """
    再帰的にテキストボックス（LTTextBox）を探して、テキストボックスのリストを取得する。
    """
    # LTTextBoxを継承するオブジェクトの場合は1要素のリストを返す。
    if isinstance(layout_obj, LTTextBox):
        return [layout_obj]

    # LTContainerを継承するオブジェクトは子要素を含むので、再帰的に探す。
    if isinstance(layout_obj, LTContainer):
        boxes = []
        for child in layout_obj:
            boxes.extend(find_textboxes_recursively(child))

        return boxes

    return []  # その他の場合は空リストを返す。


def entry_pdf_pages(key, text, infile, page):
    """
    textにkeyが含まれていればPDF_PAGESにエントリーを追加する。

    Args:
        key (str): 検査するキー
        text (str): 検査する対象のテキスト
        infile (str): textが含まれるファイル名
        page (int): infile中のページ番号
    
    Returns:
        bool: keyがtextに含まれていればTrue
    """

    if not key in text:
        return False
    elif not key in PDF_PAGES:
        PDF_PAGES[key] = {infile: [page]}
    elif not infile in PDF_PAGES[key]:
        PDF_PAGES[key][infile] = [page]
    elif not page in PDF_PAGES[key][infile]:
        PDF_PAGES[key][infile].append(page)
    else:
        # 多重登録はしない
        pass

    return True


def parse_pdf(keydb, infile, fastmode=True):
    """
    PDFを解析して入力リストを作成する。

    Args:
        keydb (dict): キーと出力ファイル名の辞書 (実際はキーしか使用していない)
        infile (str): 入力ファイル
        fastmode (bool): ファイル名にキーが含まれていたら内容を解析せずにファイル全体を追加

    Returns:
        None
    """

    # 総ページ数の取得
    inpdf = PdfFileReader(infile, strict=False)
    num_pages = inpdf.getNumPages()

    # ファイル名とkeyの比較
    if fastmode:
        found = False
        for key in keydb:
            if key in infile:
                found = True
                for p in range(0, num_pages):
                    entry_pdf_pages(key, infile, infile, p)
                print(infile, "{} for {:,} (fast)".format(key, num_pages),
                    file=sys.stderr, sep=": ")

        if found:
            # ファーストモードではファイル名に見つかったら中身は見ない
            return

    with open(infile, mode="rb") as f:

        # Layout Analysisのパラメーターを設定。縦書きの検出を有効にする。
        laparams = LAParams(detect_vertical=True)

        # 共有のリソースを管理するリソースマネージャーを作成。
        resource_manager = PDFResourceManager()

        # ページを集めるPageAggregatorオブジェクトを作成。
        device = PDFPageAggregator(resource_manager, laparams=laparams)

        # Interpreterオブジェクトを作成。
        interpreter = PDFPageInterpreter(resource_manager, device)

        # ページ番号: 0オリジン
        p = 0

        # PDFPage.get_pages()にファイルオブジェクトを指定して、
        # PDFPageオブジェクトを順に取得する。
        # 時間がかかるファイルは、キーワード引数pagenosで処理する
        # ページ番号（0始まり）のリストを指定するとよい。
        for page in PDFPage.get_pages(f):

            print(infile, "{:,}/{:,}".format(p + 1, num_pages),
                file=sys.stderr, sep=": ", end="\r")

            # ページを処理する。
            interpreter.process_page(page)
            # LTPageオブジェクトを取得。
            layout = device.get_result()

            # ページ内のテキストボックスのリストを取得する。
            boxes = find_textboxes_recursively(layout)

            # テキストボックスの左上の座標の順でテキストボックスをソートする。
            # y1（Y座標の値）は上に行くほど大きくなるので、正負を反転させている。
            # boxes.sort(key=lambda b: (-b.y1, b.x0))

            for box in boxes:
                text = box.get_text().strip()
                for key in keydb:
                    entry_pdf_pages(key, text, infile, p)

            p += 1

        print(file=sys.stderr)


def output_pdf(keydb, dir):
    """
    解析したページ構造に従って出力する。

    Args:
        keydb (dict): キーと出力ファイル名の辞書
        dir (str): 出力ディレクトリ
    
    Returns:
        int: 出力ファイル数
    """

    # 出力ファイル数のカウント
    count = 0

    for key in PDF_PAGES:

        # 出力ファイル名を取得
        outfilename = os.path.join(dir, keydb[key])

        # 拡張子に".pdf"を追加
        if not outfilename.casefold().endswith(".pdf"):
            outfilename += ".pdf"

        # 処理中ファイル名表示
        print(outfilename, end="", file=sys.stderr)
        if VERBOSE > 0:
            print(":", PDF_PAGES[key], end="", file=sys.stderr)
        print(file=sys.stderr)

        # PDF出力用クラス
        outpdf = PdfFileWriter()

        # 画面に１ページ全体を表示
        outpdf.setPageLayout("/SinglePage")

        # タイトルの設定
        outpdf.addMetadata({"/Title": key})

        # ページを集約
        for infilename in PDF_PAGES[key]:
            inpdf = PdfFileReader(infilename, strict=False)
            for p in PDF_PAGES[key][infilename]:
                outpdf.addPage(inpdf.getPage(p))

        # ファイルに書き出し
        with open(outfilename, "wb") as outfile:
            outpdf.write(outfile)
        
        count += 1


    return count

def read_csv(file_name, skip_header=True, char_det=False):
    """
    CSVを読み込んで辞書を作成する。

    1列目と2列目のみ処理をして3列目以降は無視をする。

    Args:
        file_name (str): CSVファイル名
        skip_header (bool): 一行目をヘッダとしてスキップするかどうか
    
    Returns:
        dict: 作成した辞書
    """

    db = {}
    n = 0

    if char_det:
        # 文字コードの判定 (ファイル全体を読んでみる)
        with open(file_name, mode="rb") as csvfile:
            contents = csvfile.read()
        encode = chardet.detect(contents)
        encoding = encode["encoding"]
        if VERBOSE > 1:
            print(file_name, encode, sep=": ", file=sys.stderr)
    else:
        encoding = None

    # CSVの読み込み
    with open(file_name, newline="", encoding=encoding) as csvfile:
        reader = csv.reader(csvfile)
        if skip_header:
            # ヘッダ行を読み捨てる
            _header = next(reader)
        for row in reader:
            db[row[0]] = row[1]
            n += 1                
            print(file_name, n, sep=": ", file=sys.stderr, end="\r")

        print(file=sys.stderr)

    return db


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description=
        f"""%(prog)s -- PDFの盛り合わせ {VERSION}

        CSVによるリストとPDFの内容に基づきPDFファイルを仕分けする""",
        formatter_class=RawTextHelpFormatter)

    parser.add_argument("CSV",
        help="CSVによるキーと出力ファイル名のリスト")

    parser.add_argument("PDF", nargs="+", 
        help="PDFファイル")

    parser.add_argument("-v", "--verbose", action="count", default=VERBOSE,
        help="処理の進捗表示を詳細にする")

    parser.add_argument("-o", "--output-dir", default=OUT_DIR,
        help="出力ディレクトリ, default: '%(default)s'")

    parser.add_argument("-c", "--auto-char-detect", action="store_true",
        help="CSVの文字コードを自動判別する")
        # ファイルによってはCP1253と勘違いしてエラーが出るので、
        # 基本は、SJISとして処理するように変更。

    parser.add_argument("-ns", "--no-skip-csv-header", action="store_false",
        help="CSVファイルのヘッダ行 (1行目) をスキップしない")

    parser.add_argument("-nf", "--no-fast-mode", action="store_false",
        help="""\
ファイル名にキーが含まれていても無視する
default: ファイル名にキーが含まれていたらファイル全体を追加し
ファイルの内容は見ない""")

    args = parser.parse_args()

    VERBOSE = args.verbose
    OUT_DIR = os.path.normpath(args.output_dir)

    print(os.path.basename(sys.argv[0]), VERSION, AUTHOR, file=sys.stderr)
    print(file=sys.stderr)

    if VERBOSE > 1:
        print("-" * 16, file=sys.stderr)
        print("出力ディレクトリ", OUT_DIR, sep=": ", file=sys.stderr)
        print("=" * 16, file=sys.stderr)


    # Key & Filename変換リスト読込
    print("【変換リスト読込】", file=sys.stderr)
    print("-" * 16, file=sys.stderr)
    keydb = read_csv(os.path.normpath(args.CSV), args.no_skip_csv_header,
        args.auto_char_detect)
    print("=" * 16, file=sys.stderr)

    if VERBOSE > 1:
        print("【PDFファイル】", file=sys.stderr)
        print("-" * 16, file=sys.stderr)
        print("PDF files (arg)", args.PDF, sep=": ",  file=sys.stderr)

    # Windowsのためにグロブで展開
    # 解析しながらだと時間がかかるので先に確認をする
    pdfs = []
    for pdf in args.PDF:
        pdfglobed = glob.glob(pdf)
        if not pdfglobed:
            # グロブの展開に失敗した
            raise FileNotFoundError(pdf)
        else:
            pdfs.extend(os.path.normpath(f) for f in pdfglobed)

    if VERBOSE > 1:
        print("PDF files (glob)", pdfs, sep=": ",  file=sys.stderr)
        print("=" * 16, file=sys.stderr)

    # PDFの解析
    print("【解析】", file=sys.stderr)
    print("-" * 16, file=sys.stderr)
    for pdffile in pdfs:
        parse_pdf(keydb, pdffile, args.no_fast_mode)
    print("=" * 16, file=sys.stderr)

    # 解析結果の出力
    if VERBOSE > 0:
        print("【解析結果】", file=sys.stderr)
        print("-" * 16, file=sys.stderr)
        for key, value in PDF_PAGES.items():
            print(key, value, sep=": ", file=sys.stderr)
        print("=" * 16, file=sys.stderr)

    # 出力ディレクトリの作成
    os.makedirs(OUT_DIR, exist_ok=True)

    # 結果の出力
    print("【出力】", file=sys.stderr)

    print("-" * 16, file=sys.stderr)
    count = output_pdf(keydb, OUT_DIR)
    print("=" * 16, file=sys.stderr)

    # サマリの出力
    print("出力ファイル数: {:,}/{:,}".format(count, len(keydb)),
        file=sys.stderr)

    epmties = [key for key in keydb if not key in PDF_PAGES]

    if epmties:
        print("警告[出力するPDFがありません]", ", ".join(epmties),
            sep=": ", file=sys.stderr)
