#!/bin/bash

# PyInstaller for Windows

src='.'
dist='tmp/'
project='pdfassort'
pyversion='3.7'

if [ "${project}.py" -nt "dist/${project}.exe" ]; then
    # cp ${src}/${project}.py .
    py -"${pyversion}" -m PyInstaller --clean --onefile "${project}.py"
    # cp "dist/${project}.exe" "${dist}/"
fi
