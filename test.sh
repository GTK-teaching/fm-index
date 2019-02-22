#!/bin/bash

python src/fm-build.py data/test_data data/test_idx
python src/fm-search.py data/test_idx "acgt"
