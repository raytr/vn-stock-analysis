"""Cho phép test import gói `tpb` và các script CLI ở thư mục này."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
