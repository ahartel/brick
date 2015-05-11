#!/bin/bash

pdflatex -shell-escape manual.latex
makeglossaries manual
bibtex manual
makeindex manual
pdflatex -shell-escape manual.latex
pdflatex -shell-escape manual.latex
