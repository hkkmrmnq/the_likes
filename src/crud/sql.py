from sqlalchemy import text

from ..config import constants as CNST

prepare_pv_aggregated: list[str] = [
    """
CREATE MATERIALIZED VIEW pv_aggregated AS
SELECT
p.id AS profile_id,
p.distance_limit,
p.attitude_id,

ARRAY(
    SELECT pvl.unique_value_id
    FROM profilevaluelinks pvl
    WHERE pvl.profile_id = p.id
    AND pvl.polarity = 'positive'
    AND pvl.user_order < 3
    ORDER BY pvl.user_order
) AS best_uv_ids,

ARRAY(
    SELECT pvl.unique_value_id
    FROM profilevaluelinks pvl
    WHERE pvl.profile_id = p.id
    AND pvl.polarity = 'positive'
    AND pvl.user_order > 2
    ORDER BY pvl.user_order
) AS good_uv_ids,

ARRAY(
    SELECT pvl.unique_value_id
    FROM profilevaluelinks pvl
    WHERE pvl.profile_id = p.id
    AND pvl.polarity = 'neutral'
    ORDER BY pvl.user_order
) AS neutral_uv_ids,

ARRAY(
    SELECT pvl.unique_value_id
    FROM profilevaluelinks pvl
    WHERE pvl.profile_id = p.id
    AND pvl.polarity = 'negative'
    AND pvl.user_order < 10
    ORDER BY pvl.user_order
) AS bad_uv_ids,

ARRAY(
    SELECT pvl.unique_value_id
    FROM profilevaluelinks pvl
    WHERE pvl.profile_id = p.id
    AND pvl.polarity = 'negative'
    AND pvl.user_order > 9
    ORDER BY pvl.user_order
) AS worst_uv_ids

FROM profiles p
WHERE EXISTS (SELECT 1 FROM profilevaluelinks WHERE profile_id = p.id)
""",
    """
CREATE UNIQUE INDEX IF NOT EXISTS idx_pv_aggregated_profile_id_unique
ON pv_aggregated (profile_id)
""",
    """
CREATE INDEX IF NOT EXISTS idx_pv_aggregated_best_uv_ids
ON pv_aggregated USING gin (best_uv_ids)
""",
    """
CREATE INDEX IF NOT EXISTS idx_pv_aggregated_good_uv_ids
ON pv_aggregated USING gin (good_uv_ids)
""",
    """
CREATE INDEX IF NOT EXISTS idx_pv_aggregated_neutral_uv_ids
ON pv_aggregated USING gin (neutral_uv_ids)
""",
    """
CREATE INDEX IF NOT EXISTS idx_pv_aggregated_bad_uv_ids
ON pv_aggregated USING gin (bad_uv_ids)
""",
    """
CREATE INDEX IF NOT EXISTS idx_pv_aggregated_worst_uv_ids
ON pv_aggregated USING gin (worst_uv_ids)
""",
]

prepare_similarity_scores: list[str] = [
    """
DROP FUNCTION IF EXISTS array_intersect(arr1 ANYARRAY, arr2 ANYARRAY)
""",
    """
CREATE FUNCTION array_intersect(arr1 ANYARRAY, arr2 ANYARRAY)
RETURNS ANYARRAY AS $$
    SELECT ARRAY(
        SELECT UNNEST(arr1)
        INTERSECT
        SELECT UNNEST(arr2)
    );
$$ LANGUAGE sql
    """,
    """
DROP FUNCTION IF EXISTS array_jaccard_similarity(arr1 ANYARRAY, arr2 ANYARRAY)
""",
    """
CREATE FUNCTION array_jaccard_similarity(arr1 ANYARRAY, arr2 ANYARRAY)
RETURNS FLOAT AS $$
DECLARE
    intersection INT;
    union_size INT;
BEGIN
    SELECT COUNT(*) INTO intersection
    FROM (SELECT UNNEST(arr1) INTERSECT SELECT UNNEST(arr2)) AS common;

    SELECT COUNT(*) INTO union_size
    FROM (SELECT UNNEST(arr1) UNION SELECT UNNEST(arr2)) AS combined;

    RETURN CASE
        WHEN union_size = 0 THEN 0
        ELSE intersection::float / union_size
    END;
END;
$$ LANGUAGE plpgsql
    """,
    f"""
CREATE MATERIALIZED VIEW similarity_scores AS
SELECT
    pv1.profile_id as profile1_id,
    pv2.profile_id as profile2_id,
    pv1.distance_limit as profile1_distance_limit,
    pv2.distance_limit as profile2_distance_limit,

    CASE
        WHEN pv1.best_uv_ids = pv2.best_uv_ids THEN 0.35
        ELSE array_jaccard_similarity(pv1.best_uv_ids, pv2.best_uv_ids) * 0.2
    END +
    CASE
        WHEN pv1.worst_uv_ids = pv2.worst_uv_ids THEN 0.35
        ELSE array_jaccard_similarity(pv1.worst_uv_ids, pv2.worst_uv_ids) * 0.2
    END +
    array_jaccard_similarity(pv1.good_uv_ids, pv2.good_uv_ids) * 0.1 +
    array_jaccard_similarity(pv1.bad_uv_ids, pv2.bad_uv_ids) * 0.1 +
    array_jaccard_similarity(pv1.neutral_uv_ids, pv2.neutral_uv_ids) * 0.1
    as similarity_score,

    CASE
        WHEN p1.location IS NOT NULL AND p2.location IS NOT NULL
        THEN ST_Distance(p1.location::geography,
                         p2.location::geography)::integer
        ELSE NULL
    END as distance_meters,
    cardinality(array_intersect(p1.languages, p2.languages))
    as common_languages_count,
    pv1.attitude_id as attitude_id
FROM pv_aggregated pv1
JOIN pv_aggregated pv2 ON pv1.profile_id < pv2.profile_id
JOIN profiles p1 ON pv1.profile_id = p1.id
JOIN profiles p2 ON pv2.profile_id = p2.id
WHERE
    pv1.attitude_id = pv2.attitude_id
    AND array_jaccard_similarity(pv1.best_uv_ids, pv2.best_uv_ids) = 1
    AND p1.languages && p2.languages
AND (
        CASE
            WHEN p1.location IS NOT NULL AND p2.location IS NOT NULL
            THEN ST_Distance(p1.location::geography, p2.location::geography)
            ELSE 0.0
        END
    ) <= COALESCE(pv1.distance_limit, {CNST.DISTANCE_LIMIT_MAX})::integer
    AND (
        CASE
            WHEN p1.location IS NOT NULL AND p2.location IS NOT NULL
            THEN ST_Distance(p1.location::geography, p2.location::geography)
            ELSE 0.0
        END
    ) <= COALESCE(pv2.distance_limit, {CNST.DISTANCE_LIMIT_MAX})::integer;
""",
    """
CREATE UNIQUE INDEX idx_similarity_scores_unique
ON similarity_scores (profile1_id, profile2_id)
""",
    """
CREATE INDEX idx_similarity_scores_profile1
ON similarity_scores (profile1_id)
""",
    """
CREATE INDEX idx_similarity_scores_profile2
ON similarity_scores (profile2_id)
""",
]


mat_view_exists = text("""
SELECT EXISTS (
    SELECT 1 FROM pg_matviews
    WHERE matviewname = :name
    )""")


refresh_mat_view_pv_aggregated = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY pv_aggregated
""")


# similarity_scores_exists = text("""
# SELECT EXISTS (
#     SELECT 1 FROM pg_matviews
#     WHERE matviewname = 'similarity_scores'
#     )""")


refresh_mat_view_similarity_scores = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY similarity_scores
""")


# recommendations_exists = text("""
# SELECT EXISTS (
#     SELECT 1 FROM pg_matviews
#     WHERE matviewname = 'recommendations'
#     )""")


refresh_mat_view_recommendations = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY recommendations
""")

prepare_recommendations = [
    """
DROP FUNCTION IF EXISTS generate_recommendations()
""",
    """
CREATE FUNCTION generate_recommendations()
RETURNS TABLE (
    profile_id INTEGER,
    similar_profile_id INTEGER,
    distance_meters FLOAT,
    similarity_score FLOAT,
    matched_at TIMESTAMP
) AS $$
DECLARE
    rec RECORD;
    used_ids INTEGER[] := '{}';
BEGIN
    FOR rec IN
        SELECT *
        FROM public.similarity_scores
        ORDER BY similarity_score DESC, profile1_id, profile2_id
    LOOP
        IF rec.profile1_id = ANY(used_ids) OR rec.profile2_id = ANY(used_ids)
            THEN CONTINUE;
        END IF;

        used_ids := array_append(used_ids, rec.profile1_id);
        used_ids := array_append(used_ids, rec.profile2_id);

        -- Return both directions
        profile_id := rec.profile1_id;
        similar_profile_id := rec.profile2_id;
        distance_meters := rec.distance_meters;
        similarity_score := rec.similarity_score;
        matched_at := NOW();
        RETURN NEXT;

        profile_id := rec.profile2_id;
        similar_profile_id := rec.profile1_id;
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql
""",
    """
CREATE MATERIALIZED VIEW recommendations AS
SELECT * FROM generate_recommendations()
""",
    """
CREATE UNIQUE INDEX idx_recommendations_unique
ON recommendations (profile_id)
""",
]


read_recommendation = text("""
SELECT
    similar_profile_id,
    similarity_score,
    distance_meters
FROM recommendations
WHERE
    profile_id = :profile_id
    AND similar_profile_id
    NOT IN (SELECT target_profile_id FROM contacts
                                     WHERE me_profile_id = :profile_id)
""")
