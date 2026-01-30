from sqlalchemy import select

from src.config.config import CFG
from src.db.core import Attitude, Value
from src.services.utils.other import generate_random_personal_values


async def test_random_pv_input_generation(asession):
    result = await asession.scalars(select(Attitude.id))
    assert result is not None
    db_attitude_ids = set(sorted(result))
    result = await asession.scalars(select(Value.id))
    assert result is not None
    db_value_ids = set(sorted(result))
    for _ in range(CFG.RANDOM_PV_TEST_ATTEMPTS):
        input_data = await generate_random_personal_values(asession=asession)
        assert isinstance(input_data, dict)
        assert 'attitude_id' in input_data
        assert input_data['attitude_id'] in db_attitude_ids
        assert 'value_links' in input_data
        input_personal_values = input_data['value_links']
        assert isinstance(input_personal_values, list)
        assert len(input_personal_values) == CFG.PERSONAL_VALUE_MAX_ORDER
        polarity_order = {'positive': 1, 'neutral': 2, 'negative': 3}
        for personal_value in input_personal_values:
            assert isinstance(personal_value, dict)
            assert 'polarity' in personal_value
            assert 'user_order' in personal_value
            assert 'value_id' in personal_value
            assert 'aspects' in personal_value
            personal_aspects = personal_value['aspects']
            assert isinstance(personal_aspects, list)
            for personal_aspect in personal_aspects:
                assert isinstance(personal_aspect, dict)
                assert 'aspect_id' in personal_aspect
                assert 'included' in personal_aspect
        assert all(
            polarity_order[a['polarity']] <= polarity_order[b['polarity']]
            for a, b in zip(input_personal_values, input_personal_values[1:])
        )
        input_value_ids = set(
            sorted([pv['value_id'] for pv in input_personal_values])
        )
        assert db_value_ids == input_value_ids
        input_personal_value_orders = set(
            sorted([pv['user_order'] for pv in input_personal_values])
        )
        assert input_personal_value_orders == set(
            range(1, CFG.PERSONAL_VALUE_MAX_ORDER + 1)
        )
