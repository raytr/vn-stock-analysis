"""Hợp đồng cột giữa Python và Apps Script phải luôn khớp.

Đây là ranh giới liên ngôn ngữ duy nhất của hệ thống, và là chỗ dễ lệch nhất:
sửa một bên mà quên bên kia thì dữ liệu ghi lệch cột mà không có gì báo lỗi.
"""
import os
import re

from push_to_sheet import COLUMNS

def _repo_root():
    """Đi ngược lên tới thư mục chứa .git — bền hơn đếm số cấp ../"""
    d = os.path.dirname(os.path.abspath(__file__))
    while d != os.path.dirname(d):
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    raise RuntimeError("không tìm thấy repo root")


CODE_GS = os.path.join(_repo_root(), "apps-script/Code.gs")


def _apps_script_fields():
    with open(CODE_GS, encoding="utf-8") as fh:
        gs = fh.read()
    block = re.search(r"FIELDS = \[(.*?)\];", gs, re.S).group(1)
    return re.findall(r"'(\w+)'", block)


def test_apps_script_file_exists():
    assert os.path.exists(CODE_GS), CODE_GS


def test_writable_columns_match_apps_script_exactly():
    # COLUMNS[0] là 'date' (cột A, dùng để tìm dòng), B..I là phần ghi
    assert COLUMNS[1:] == _apps_script_fields()


def test_exactly_eight_writable_columns():
    assert len(_apps_script_fields()) == 8


def test_apps_script_never_touches_user_columns():
    with open(CODE_GS, encoding="utf-8") as fh:
        gs = fh.read()
    # ghi bắt đầu từ cột B và dài đúng 8 cột -> không thể chạm J, L, M
    assert "FIRST_WRITE_COL = 2" in gs
    assert "FIELDS.length" in gs
