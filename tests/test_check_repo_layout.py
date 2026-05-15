from scripts.check_repo_layout import REPO_ROOT, check_repo_layout


def test_expected_repo_layout_is_present():
    assert (REPO_ROOT / "package.json").is_file()
    assert (REPO_ROOT / "dashboard" / "app" / "package.json").is_file()
    assert (REPO_ROOT / "showcase" / "app" / "package.json").is_file()
    assert check_repo_layout() == []
