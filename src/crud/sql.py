from sqlalchemy import text

from .. import constants as cnst

create_array_intersect_func = text("""
CREATE OR REPLACE FUNCTION array_intersect(arr1 ANYARRAY, arr2 ANYARRAY)
RETURNS ANYARRAY AS $$
    SELECT ARRAY(
        SELECT UNNEST(arr1)
        INTERSECT
        SELECT UNNEST(arr2)
    );
$$ LANGUAGE sql
""")


create_array_jaccard_similarity_func = text("""
CREATE OR REPLACE FUNCTION
array_jaccard_similarity(arr1 ANYARRAY, arr2 ANYARRAY)
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
""")


recommendations_exists = text("""
SELECT EXISTS (
    SELECT 1 FROM pg_matviews
    WHERE matviewname = 'recommendations'
    )""")


create_recommendations_mat_view = text(f"""
CREATE MATERIALIZED VIEW recommendations AS
SELECT
    pv1.profile_id as profile1_id,
    pv2.profile_id as profile2_id,
    pv1.distance_limit as profile1_distance_limit,
    pv2.distance_limit as profile2_distance_limit,
    0.35 +
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
        THEN ST_Distance(p1.location::geography, p2.location::geography)
        ELSE NULL
    END as distance_meters,
    cardinality(array_intersect(p1.languages, p2.languages))
    as common_languages_count
FROM pvonelines pv1
JOIN pvonelines pv2 ON pv1.id < pv2.id
JOIN profiles p1 ON pv1.profile_id = p1.id
JOIN profiles p2 ON pv2.profile_id = p2.id
WHERE
    pv1.attitude_id_and_best_uv_ids = pv2.attitude_id_and_best_uv_ids
    AND p1.languages && p2.languages
AND (
        CASE
            WHEN p1.location IS NOT NULL AND p2.location IS NOT NULL
            THEN ST_Distance(p1.location::geography, p2.location::geography)
            ELSE NULL
        END
    ) <= COALESCE(pv1.distance_limit, {cnst.DISTANCE_MAX_LIMIT})::integer
    AND (
        CASE
            WHEN p1.location IS NOT NULL AND p2.location IS NOT NULL
            THEN ST_Distance(p1.location::geography, p2.location::geography)
            ELSE NULL
        END
    ) <= COALESCE(pv2.distance_limit, {cnst.DISTANCE_MAX_LIMIT})::integer;
""")

create_unique_idx_recommendations = text("""
CREATE UNIQUE INDEX idx_recommendations_unique
ON recommendations (profile1_id, profile2_id)
""")

create_idx_recommendations_profile1 = text("""
CREATE INDEX idx_recommendations_profile1
ON recommendations (profile1_id)
""")


create_idx_recommendations_profile2 = text("""
CREATE INDEX idx_recommendations_profile2
ON recommendations (profile2_id)
""")


read_recommendations_for_user = text("""
SELECT
    CASE
        WHEN profile1_id = :profile_id THEN profile2_id
        ELSE profile1_id
    END as similar_profile_id,
    similarity_score,
    distance_meters
FROM recommendations
WHERE
    (profile1_id = :profile_id OR profile2_id = :profile_id)
    AND (
        CASE
            WHEN profile1_id = :profile_id THEN profile2_id
            ELSE profile1_id
        END
    ) NOT IN (SELECT target_profile_id
              FROM contacts
              WHERE me_profile_id = :profile_id)
ORDER BY similarity_score DESC
LIMIT :limit
""")


refresh_recommendations = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY recommendations
""")
