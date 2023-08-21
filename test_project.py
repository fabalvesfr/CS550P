import project
import pytest
import re


def test_get_token():
    token = project.get_token()

    pattern = r"^.+$"
    match = re.search(pattern, token, flags=re.IGNORECASE)
    assert match != None

    assert type(token) == str


def test_get_auth_header():
    assert type(project.get_auth_header("some_rdm_input")) == dict


def test_search_for_playlist():
    token = project.get_token()
    valid_country = "Brazil"
    invalid_country = "Cat"

    assert project.search_for_playlist(token, valid_country)['name'] == 'Top 50 - Brazil'

    with pytest.raises(ValueError):
        assert project.search_for_playlist(token, invalid_country)


def test_get_playlist_tracks():
    token = project.get_token()
    valid_playlist_id = project.search_for_playlist(token, "Brazil")['id']
    invalid_playlist_id = "cat"

    assert len(project.get_playlist_tracks(token, valid_playlist_id)["track_name_and_artist"]) == 20 # If my GET request was successful, then my track_name_and_artist list should have 20 items

    with pytest.raises(project.NoResultError):
        project.get_playlist_tracks(token, invalid_playlist_id)
