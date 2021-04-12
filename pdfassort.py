#!/usr/bin/python3
#
# Copyright (c) 2019-2021 Katsuya
#
# 公開URL: https://github.com/katsuya1128/pdfassort/
#

"""
pdfassort.py -- PDFの盛り合わせ

CSVで検索キーワードと出力ファイル名の組み合わせを指定し、
PDFのファイル群を調べてキーワードが含まれるページを集めて
出力ファイルにまとめる。


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
pip isntall pdfminer.six PyPDF2 chardet
```

### その他

仮想PDFプリンタ (CubePDFやMicrosoft Print to PDFなど) で
出力されたPDFは解析に時間がかかるようです。
プログラム直接出力のPDFを用意しましょう。

テキスト解析できないPDF (例えばスキャンされたものとか、
保護されたものなど) は、ファイル名にキーを含めましょう。
"""

import sys
import io
import os.path
import argparse
from argparse import RawTextHelpFormatter
import glob
import csv
import chardet
import magic
from io import StringIO

# Some code from https://qiita.com/mczkzk/items/894110558fb890c930b5
# https://pdfminersix.readthedocs.io/en/latest/tutorials/composable.html

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

import PyPDF2


VERSION = "v0.4 (2021/04/12)"
AUTHOR = "Katsuya https://github.com/katsuya1128/"

# バーバスモード
VERBOSE = 0

# デフォルトの出力先ディレクトリ
OUT_DIR = "."

# ファイル構造のデータベース
PDF_PAGES = {}

# エラー・ログ・ファイル
ERR_LOG = None

# リダイレクト時も UTF=8 に
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="UTF-8")


def err_log(message, outfile=None):
    """
    エラーログの記録

    Args:
        msg (str): 表示するメッセージ
        file (file object): 出力するログファイル

    Returns:
        None
    """

    print(message, file=sys.stderr)
    if outfile:
        print(message, file=outfile)


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

    if key not in text:
        if VERBOSE > 2:
            print(" {}:{}:{}:{}".format(infile, page, key, text),
                  file=sys.stderr)
        return False
    elif key not in PDF_PAGES:
        PDF_PAGES[key] = {infile: [page]}
    elif infile not in PDF_PAGES[key]:
        PDF_PAGES[key][infile] = [page]
    elif page not in PDF_PAGES[key][infile]:
        PDF_PAGES[key][infile].append(page)
    else:
        # 多重登録はしない
        pass

    if VERBOSE > 2:
        print("*{}:{}:{}:{}".format(infile, page, key, text),
              file=sys.stderr)

    return True


def is_encripted(infile):
    """
    PDFが暗号化されていないかを調べる。

    Args:
        infile (str): 入力ファイル

    Returns:
        None: ファイルは暗号化されていない
        True: 暗号化されている
        str: PDF以外のファイル
    """

    result = None

    with open(infile, mode="rb") as in_file:
        # ファイルが暗号化されていないかをチェック
        try:
            reader = PyPDF2.PdfFileReader(in_file, strict=False)
            if reader.isEncrypted:
                result = True
        except PyPDF2.utils.PdfReadError:
            in_file.seek(0)
            result = magic.from_buffer(in_file.read(2048))
        except Exception as err:
            result = err

    return result


def parse_pdf(keydb, infile, fastmode=True):
    """
    PDFを解析して入力リストを作成する。

    Args:
        keydb (dict): キーと出力ファイル名の辞書 (実際はキーしか
            使用していない)
        infile (str): 入力ファイル
        fastmode (bool): ファイル名にキーが含まれていたら内容を
            解析せずにファイル全体を追加

    Returns:
        None
    """

    # ファイルが暗号化されているかどうかのチェック
    is_enc = is_encripted(infile)
    if is_enc:
        if type(is_enc) is str:
            # PDFでない
            err_log("Error: {}: Not PDF ({})".format(infile, is_enc), ERR_LOG)
        else:
            # 暗号化されている
            err_log("Error: {}: Encrypted".format(infile), ERR_LOG)

        return

    # 総ページ数の取得
    inpdf = PyPDF2.PdfFileReader(infile, strict=False)
    num_pages = inpdf.getNumPages()

    # ファイル名とkeyの比較
    if fastmode:
        found = False
        for key in keydb:
            if key in infile:
                found = True
                for p in range(0, num_pages):
                    entry_pdf_pages(key, infile, infile, p)
                if VERBOSE > 0:
                    print(infile, "{} for {:,} (fast)".format(key, num_pages),
                          file=sys.stderr, sep=": ")

        if found:
            # ファーストモードではファイル名に見つかったら中身は見ない
            return

    output_string = StringIO()
    with open(infile, mode="rb") as in_file:

        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        p = 0

        for page in PDFPage.create_pages(doc):

            print(infile, "{:,}/{:,}".format(p + 1, num_pages),
                  file=sys.stderr, sep=": ", end="\r")

            # ページを処理する。
            interpreter.process_page(page)
            text = output_string.getvalue()
            output_string.truncate(0)

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
        outpdf = PyPDF2.PdfFileWriter()

        # 画面に１ページ全体を表示
        outpdf.setPageLayout("/SinglePage")

        # タイトルの設定
        outpdf.addMetadata({"/Title": key})

        # ページを集約
        for infilename in PDF_PAGES[key]:
            inpdf = PyPDF2.PdfFileReader(infilename, strict=False)
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
            next(reader)
        for row in reader:
            db[row[0]] = row[1]
            n += 1
            print(file_name, n, sep=": ", file=sys.stderr, end="\r")

        print(file=sys.stderr)

    return db


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=f"""%(prog)s -- PDFの盛り合わせ {VERSION}

        CSVによるリストとPDFの内容に基づきPDFファイルを仕分けする""",
        formatter_class=RawTextHelpFormatter)

    parser.add_argument(
        "CSV", help="CSVによるキーと出力ファイル名のリスト")

    parser.add_argument(
        "PDF", nargs="+", help="PDFファイル")

    parser.add_argument(
        "-v", "--verbose", action="count", default=VERBOSE,
        help="処理の進捗表示を詳細にする")

    parser.add_argument(
        "-o", "--output-dir", default=OUT_DIR,
        help="出力ディレクトリ, default: '%(default)s'")

    parser.add_argument(
        "-c", "--auto-char-detect", action="store_true",
        help="CSVの文字コードを自動判別する")
    # ファイルによってはCP1253と勘違いしてエラーが出るので、
    # 基本は、SJISとして処理するように変更。

    parser.add_argument(
        "-ns", "--no-skip-csv-header", action="store_false",
        help="CSVファイルのヘッダ行 (1行目) をスキップしない")

    parser.add_argument(
        "-nf", "--no-fast-mode", action="store_false",
        help="ファイル名にキーが含まれていても無視する\n"
        "default: ファイル名にキーが含まれていたらファイル全体を追加し\n"
        "ファイルの内容は見ない")

    parser.add_argument(
        "-l", "--log-file",
        help="エラー・ログ・ファイル, default: なし")

    args = parser.parse_args()

    VERBOSE = args.verbose
    OUT_DIR = os.path.normpath(args.output_dir)

    if args.log_file:
        ERR_LOG = open(args.log_file, "wt", encoding="utf-8")

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

    epmties = [key for key in keydb if key not in PDF_PAGES]

    if epmties:
        print("警告[出力するPDFがありません]", ", ".join(epmties),
              sep=": ", file=sys.stderr)

    ERR_LOG.close()
