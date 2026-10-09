import os

import states.load as ld

CSV = os.path.join(os.path.dirname(__file__),
                   '..', 'raw_data', 'states.csv')


def test_load_states():
    states = ld.load_states(CSV)
    assert isinstance(states, list)
    assert len(states) > 50


def test_load_states_california():
    states = ld.load_states(CSV)
    ca = [row for row in states if row['Abbrev'] == 'CA']
    assert len(ca) == 1
    assert ca[0]['State'] == 'California'
