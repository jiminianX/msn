import states.query as qry


def test_query():
    states = qry.get_states()
    assert isinstance(states, dict)


def test_get_state():
    state = qry.get_state('AL')
    assert isinstance(state, dict)
    assert state['name'] == 'Alabama'
    assert qry.get_state('al') == state


def test_get_state_not_found():
    assert qry.get_state('ZZ') is None


def test_get_state_non_string():
    assert qry.get_state(None) is None
    assert qry.get_state(17) is None


def test_get_states_db_down(monkeypatch):
    monkeypatch.setattr(qry, 'is_db_up', lambda: False)
    assert qry.get_states() is None


def test_get_state_db_down(monkeypatch):
    monkeypatch.setattr(qry, 'is_db_up', lambda: False)
    assert qry.get_state('AL') is None


def test_main_db_down(monkeypatch):
    """
    main() must not raise when the database is down.
    """
    monkeypatch.setattr(qry, 'is_db_up', lambda: False)
    qry.main()
