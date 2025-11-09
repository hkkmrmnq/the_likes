from sqlalchemy import text

from src.config import constants as CNST
from src.config.config import CFG
from src.config.enums import SearchAllowedStatus

prepare_funcs_and_matviews_commands: list[str] = [
    """
DROP FUNCTION IF EXISTS public.array_similarity CASCADE;
    """,
    """
DROP FUNCTION IF EXISTS public.compare_moral_profiles CASCADE;
    """,
    """
DROP FUNCTION IF EXISTS public.search_status_sort_priority CASCADE;
    """,
    """
DROP FUNCTION IF EXISTS public.choose_significant CASCADE;
    """,
    """
DROP FUNCTION IF EXISTS public.calculate_stability CASCADE;
    """,
    """
DROP MATERIALIZED VIEW IF EXISTS moral_profiles CASCADE;
    """,
    """
DROP MATERIALIZED VIEW IF EXISTS recommendations CASCADE;
    """,
    """
CREATE OR REPLACE FUNCTION public.array_similarity(
    arr1 INTEGER[], arr2 INTEGER[]
)
RETURNS FLOAT AS $$
DECLARE
    common_count INT;
    total_count INT;
BEGIN
    IF arr1 = '{}' AND arr2 = '{}' THEN
        RETURN 1.0;
    ELSIF arr1 = '{}' OR arr2 = '{}' THEN
        RETURN 0.0;
    END IF;

    SELECT COUNT(*) INTO common_count
    FROM UNNEST(arr1) AS elem
    WHERE elem = ANY(arr2);

    total_count :=
        array_length(arr1, 1) + array_length(arr2, 1) - common_count;

    RETURN common_count::float / NULLIF(total_count, 0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;
    """,
    """
CREATE OR REPLACE FUNCTION public.compare_moral_profiles(
    attitude1 INTEGER, best1 INTEGER[], worst1 INTEGER[], good1 INTEGER[],
    bad1 INTEGER[], neutral1 INTEGER[],
    attitude2 INTEGER, best2 INTEGER[], worst2 INTEGER[], good2 INTEGER[],
    bad2 INTEGER[], neutral2 INTEGER[]
)
RETURNS DOUBLE PRECISION AS $$
BEGIN
    IF attitude1 != attitude2
    THEN RETURN 0;
    END IF;

    RETURN
        CASE WHEN best1 = best2 THEN 0.35
        ELSE public.array_similarity(best1, best2) * 0.2 END +
        CASE WHEN worst1 = worst2 THEN 0.35
        ELSE public.array_similarity(worst1, worst2) * 0.2 END +
        public.array_similarity(good1, good2) * 0.1 +
        public.array_similarity(bad1, bad2) * 0.1 +
        public.array_similarity(neutral1, neutral2) * 0.1;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
    """,
    f"""
CREATE OR REPLACE FUNCTION public.search_status_sort_priority(
    status search_allowed_status
)
RETURNS INT AS $$
BEGIN
    RETURN CASE status
        WHEN '{SearchAllowedStatus.OK.value}' THEN 0
        WHEN '{SearchAllowedStatus.SUSPENDED.value}' THEN 1
        ELSE 4
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
    """,
    """
CREATE OR REPLACE FUNCTION public.choose_significant(
    now TIMESTAMP,
    all_changes TIMESTAMP[]
)
RETURNS TIMESTAMP[]
AS $$
DECLARE
    significant_changes TIMESTAMP[];
    current TIMESTAMP;
    previous TIMESTAMP;
    number_of_changes INT;
    i INT;
BEGIN
    significant_changes := '{}';
    number_of_changes := array_length(all_changes, 1);

    IF number_of_changes > 0 THEN
        current := all_changes[number_of_changes];
        significant_changes := significant_changes || current;

        IF number_of_changes > 1 THEN
            FOR i IN 1..(number_of_changes - 1) LOOP
                previous := all_changes[number_of_changes - i];

                IF current - previous > INTERVAL '1 day' THEN
                    significant_changes := significant_changes || previous;
                    current := previous;
                END IF;
            END LOOP;
        END IF;
    END IF;

    RETURN significant_changes;
END;
$$ LANGUAGE plpgsql;
    """,
    """
CREATE OR REPLACE FUNCTION public.calculate_stability(
    initial TIMESTAMP,
    now TIMESTAMP,
    changes TIMESTAMP[]
)
RETURNS FLOAT
AS $$
WITH significant_changes AS (
    SELECT unnest(public.choose_significant(now, changes)) as change
),
modifiers AS (
    SELECT (EXTRACT(EPOCH FROM (now - change)) /
            EXTRACT(EPOCH FROM (now - initial)))::FLOAT as modifier
    FROM significant_changes
)
SELECT COALESCE(EXP(SUM(LN(modifier))), 1.0) as stability
FROM modifiers;
$$ LANGUAGE sql;
    """,
    f"""
CREATE MATERIALIZED VIEW moral_profiles AS

SELECT
p.id AS profile_id,
p.distance_limit,
p.attitude_id,
p.user_id,

ARRAY(
    SELECT pv.unique_value_id
    FROM personalvalues pv
    WHERE pv.user_id = p.user_id
    AND pv.polarity = 'positive'
    AND pv.user_order <= {CNST.NUMBER_OF_BEST_UVS}
    ORDER BY pv.user_order
) AS best_uv_ids,

ARRAY(
    SELECT pv.unique_value_id
    FROM personalvalues pv
    WHERE pv.user_id = p.user_id
    AND pv.polarity = 'positive'
    AND pv.user_order > {CNST.NUMBER_OF_BEST_UVS}
    ORDER BY pv.user_order
) AS good_uv_ids,

ARRAY(
    SELECT pv.unique_value_id
    FROM personalvalues pv
    WHERE pv.user_id = p.user_id
    AND pv.polarity = 'neutral'
    ORDER BY pv.user_order
) AS neutral_uv_ids,

ARRAY(
    SELECT pv.unique_value_id
    FROM personalvalues pv
    WHERE pv.user_id = p.user_id
    AND pv.polarity = 'negative'
    AND pv.user_order
    <= {CFG.PERSONAL_VALUE_MAX_ORDER - CNST.NUMBER_OF_WORST_UVS}
    ORDER BY pv.user_order
) AS bad_uv_ids,

ARRAY(
    SELECT pv.unique_value_id
    FROM personalvalues pv
    WHERE pv.user_id = p.user_id
    AND pv.polarity = 'negative'
    AND pv.user_order
    > {CFG.PERSONAL_VALUE_MAX_ORDER - CNST.NUMBER_OF_WORST_UVS}
    ORDER BY pv.user_order
) AS worst_uv_ids

FROM profiles p
JOIN userdynamics ud ON p.user_id = ud.user_id
WHERE EXISTS (SELECT 1 FROM personalvalues WHERE user_id = p.user_id);
    """,
    """
CREATE UNIQUE INDEX idx_moral_profiles_user_id_unique
ON moral_profiles (user_id);
    """,
    """
CREATE INDEX idx_moral_profiles_best_uv_ids
ON moral_profiles USING gin (best_uv_ids);
    """,
    """
CREATE INDEX idx_moral_profiles_good_uv_ids
ON moral_profiles USING gin (good_uv_ids);
    """,
    """
CREATE INDEX idx_moral_profiles_neutral_uv_ids
ON moral_profiles USING gin (neutral_uv_ids);
    """,
    """
CREATE INDEX idx_moral_profiles_bad_uv_ids
ON moral_profiles USING gin (bad_uv_ids);
    """,
    """
CREATE INDEX idx_moral_profiles_worst_uv_ids
ON moral_profiles USING gin (worst_uv_ids);
    """,
    f"""
CREATE MATERIALIZED VIEW recommendations AS
WITH
now_cte AS (
    SELECT LOCALTIMESTAMP as now
),
allowed_for_search AS (
    SELECT user_id, search_allowed_status, values_created, values_changes
    FROM userdynamics
    WHERE search_allowed_status IN (
         --'ok',
        '{SearchAllowedStatus.OK.value}',
        --'suspended'
        '{SearchAllowedStatus.SUSPENDED.value}'
    )
),
recommendable_profiles AS (
    SELECT
        mp.*,
        p.name,
        p.location,
        p.languages,
        afs.search_allowed_status,
        public.calculate_stability(
            afs.values_created,
            (SELECT now FROM now_cte),
            afs.values_changes
            ) as stability
    FROM moral_profiles mp
    JOIN profiles p ON mp.profile_id = p.id AND p.recommend_me
    JOIN users u ON mp.user_id = u.id AND u.is_active
    JOIN allowed_for_search afs ON mp.user_id = afs.user_id
),
profile_pairs AS (
    SELECT
        p1.profile_id as p_id_1,
        p2.profile_id as p_id_2,
        p1.user_id as u_id_1,
        p2.user_id as u_id_2,
        p1.name as name_1,
        p2.name as name_2,
        p1.distance_limit as distance_limit_1,
        p2.distance_limit as distance_limit_2,
        public.search_status_sort_priority(p1.search_allowed_status) +
        public.search_status_sort_priority(p2.search_allowed_status)
            as search_status_priority,
        LEAST(p1.stability, p2.stability) as stability_modifier,
        p1.attitude_id as attitude_1,
        p2.attitude_id as attitude_2,
        p1.best_uv_ids as best_1,
        p2.best_uv_ids as best_2,
        p1.worst_uv_ids as worst_1,
        p2.worst_uv_ids as worst_2,
        p1.good_uv_ids as good_1,
        p2.good_uv_ids as good_2,
        p1.bad_uv_ids as bad_1,
        p2.bad_uv_ids as bad_2,
        p1.neutral_uv_ids as neutral_1,
        p2.neutral_uv_ids as neutral_2,

        CASE
            WHEN
                p1.distance_limit IS NOT NULL
                OR p2.distance_limit IS NOT NULL
            THEN ST_Distance(p1.location, p2.location)::integer
            ELSE
                NULL
        END as distance_meters

        FROM recommendable_profiles p1
        JOIN recommendable_profiles p2 ON p1.profile_id < p2.profile_id
        WHERE
            p1.attitude_id = p2.attitude_id
            AND p1.languages && p2.languages
            AND public.array_similarity(
                p1.best_uv_ids::integer[], p2.best_uv_ids::integer[]
                ) = 1
),
filterd_pairs AS (
    SELECT
        u_id_1,
        u_id_2,
        ARRAY[u_id_1, u_id_2] as user_ids,
        ARRAY[p_id_1, p_id_2] as profile_ids,
        ARRAY[name_1, name_2] as profile_names,

        public.compare_moral_profiles(
            attitude_1, best_1, worst_1, good_1, bad_1, neutral_1,
            attitude_2, best_2, worst_2, good_2, bad_2, neutral_2
        )
            as similarity_score,
        distance_meters,
        search_status_priority,
        stability_modifier

    FROM profile_pairs
    WHERE
        (distance_meters IS NULL)
        OR
        (
            (distance_meters <= COALESCE(
                --distance_limit_1, 20037509)
                distance_limit_1, {CNST.DISTANCE_LIMIT_MAX})
                )
            AND
            (distance_meters <= COALESCE(
                --distance_limit_1, 20037509)
                distance_limit_1, {CNST.DISTANCE_LIMIT_MAX})
                )
        )
)

SELECT
    user_ids,
    profile_ids,
    profile_names,
    similarity_score,
    distance_meters,
    search_status_priority,
    stability_modifier

FROM filterd_pairs fp

WHERE NOT EXISTS (
    SELECT 1 FROM contacts c
    WHERE c.my_user_id = fp.u_id_1 AND c.other_user_id = fp.u_id_2
);
    """,
    """
CREATE INDEX idx_recommendations__user_ids_gin
ON recommendations USING GIN (user_ids);
    """,
    """
CREATE UNIQUE INDEX idx_recommendations__user_ids
ON recommendations (user_ids);
    """,
    """
CREATE INDEX idx_search_status_priority
ON recommendations (search_status_priority, similarity_score DESC);
    """,
]


refresh_moral_profiles = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY moral_profiles;
""")

vacuum_moral_profiles = text("""
VACUUM moral_profiles;
""")

refresh_recommendations = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY recommendations;
""")

vacuum_recommendations = text("""
VACUUM recommendations;
""")


read_user_recommendations = text("""
WITH ranked_recommendations AS (
SELECT
user_ids[3 - array_position(user_ids, :my_user_id)]
    as user_id,
profile_names[3 - array_position(user_ids, :my_user_id)]
    as name,
    similarity_score,
    search_status_priority,
    stability_modifier,
    distance_meters
FROM recommendations
WHERE :my_user_id = ANY(user_ids)
AND (:other_user_id IS NULL OR :other_user_id = ANY(user_ids))
)

SELECT
    rec.user_id,
    rec.name,
    rec.search_status_priority,
    rec.stability_modifier,
    rec.similarity_score,
    rec.distance_meters

FROM ranked_recommendations rec

ORDER BY search_status_priority ASC,
    stability_modifier DESC,
    similarity_score DESC
LIMIT :limit_param;
""")


users_to_notify_of_match = text(f"""
WITH matches as
    (SELECT DISTINCT unnest(user_ids) as match_user_id FROM recommendations)
SELECT match_user_id, email
FROM matches
JOIN users ON matches.match_user_id = users.id
JOIN userdynamics ON matches.match_user_id = userdynamics.user_id
JOIN profiles ON matches.match_user_id = profiles.user_id
WHERE
    userdynamics.search_allowed_status IN (
        '{SearchAllowedStatus.OK.value}',
        '{SearchAllowedStatus.SUSPENDED.value}'
    )
    AND profiles.recommend_me;
""")


read_contact_profile = text("""
WITH
my_mp_table AS (
    SELECT mp.*, p.location
    FROM moral_profiles mp
        JOIN profiles p ON mp.user_id = p.user_id
    WHERE mp.user_id = :my_user_id
    LIMIT 1
),
other_mp_table AS (
    SELECT mp.*, p.name, p.location
    FROM moral_profiles mp
        JOIN profiles p ON mp.user_id = p.user_id
    WHERE mp.user_id = :other_user_id
    LIMIT 1
)
SELECT
other_mp.user_id,
other_mp.name,
public.compare_moral_profiles(
    my_mp.attitude_id, my_mp.best_uv_ids, my_mp.worst_uv_ids,
    my_mp.good_uv_ids, my_mp.bad_uv_ids, my_mp.neutral_uv_ids,
    other_mp.attitude_id, other_mp.best_uv_ids, other_mp.worst_uv_ids,
    other_mp.good_uv_ids, other_mp.bad_uv_ids, other_mp.neutral_uv_ids
) as similarity_score,
CASE
    WHEN
        my_mp.distance_limit IS NOT NULL
        OR other_mp.distance_limit IS NOT NULL
    THEN ST_Distance(my_mp.location, other_mp.location)::integer
    ELSE
        NULL
END as distance_meters
FROM my_mp_table my_mp
    JOIN other_mp_table other_mp ON true
""")
