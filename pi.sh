#!/bin/bash

# PyInstaller for Windows

src='.'
dist='tmp/'
project='pdfassort'

if [ "${project}.py" -nt "dist/${project}.exe" ]; then
    # cp ${src}/${project}.py .
    pyinstaller --clean --onefile "${project}.py"
    cp "dist/${project}.exe" "${dist}/"
fi
