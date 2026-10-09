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
