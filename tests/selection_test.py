import os
import pytest
import yaml

from photoshell.selection import Selection


@pytest.fixture
def sidecar(tmpdir):
    tmpdir.join("test.sidecar").write(yaml.dump({
        'developed_path': os.path.join(tmpdir.strpath, "test.jpeg"),
        'datetime': '2014-10-10 00:00'
    }, default_flow_style=False))
    return os.path.join(tmpdir.strpath, "test.sidecar")


@pytest.fixture
def empty_selection():
    s = Selection('', '')
    return s


@pytest.fixture
def selection(empty_selection):
    empty_selection.photos.append('photo')
    return empty_selection


def test_current_photo_default_selection(selection):
    assert selection.current_photo()


def test_current_photo_is_none_if_selection_empty(empty_selection):
    assert empty_selection.current_photo() is None


def test_next_prev_does_nothing_single_photo(selection):
    assert selection.current_photo() == selection.next_photo()
    assert selection.current_photo() == selection.prev_photo()


def test_next_prev_wrap_around(selection):
    selection.photos.append('photo2')

    assert selection.next_photo() == 'photo2'
    assert selection.next_photo() == 'photo'
    assert selection.prev_photo() == 'photo2'
    assert selection.prev_photo() == 'photo'
