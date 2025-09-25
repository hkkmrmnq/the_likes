from sqlalchemy import text

from ..config import constants as CNST

create_func_array_intersect = text("""
CREATE OR REPLACE FUNCTION array_intersect(arr1 ANYARRAY, arr2 ANYARRAY)
RETURNS ANYARRAY AS $$
    SELECT ARRAY(
        SELECT UNNEST(arr1)
        INTERSECT
        SELECT UNNEST(arr2)
    );
$$ LANGUAGE sql
""")


create_func_array_jaccard_similarity = text("""
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


similarity_scores_exists = text("""
SELECT EXISTS (
    SELECT 1 FROM pg_matviews
    WHERE matviewname = 'similarity_scores'
    )""")


create_mat_view_similarity_scores = text(f"""
CREATE MATERIALIZED VIEW similarity_scores AS
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
        THEN ST_Distance(p1.location::geography,
                         p2.location::geography)::integer
        ELSE NULL
    END as distance_meters,
    cardinality(array_intersect(p1.languages, p2.languages))
    as common_languages_count,
    pv1.attitude_id_and_best_uv_ids as attitude_id_and_best_uv_ids
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
            ELSE 0.0
        END
    ) <= COALESCE(pv1.distance_limit, {CNST.DISTANCE_MAX_LIMIT})::integer
    AND (
        CASE
            WHEN p1.location IS NOT NULL AND p2.location IS NOT NULL
            THEN ST_Distance(p1.location::geography, p2.location::geography)
            ELSE 0.0
        END
    ) <= COALESCE(pv2.distance_limit, {CNST.DISTANCE_MAX_LIMIT})::integer;
""")


refresh_mat_view_similarity_scores = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY similarity_scores
""")


create_unique_idx_similarity_scores = text("""
CREATE UNIQUE INDEX idx_similarity_scores_unique
ON similarity_scores (profile1_id, profile2_id)
""")

create_idx_similarity_scores_profile1 = text("""
CREATE INDEX idx_similarity_scores_profile1
ON similarity_scores (profile1_id)
""")


create_idx_similarity_scores_profile2 = text("""
CREATE INDEX idx_similarity_scores_profile2
ON similarity_scores (profile2_id)
""")

recommendations_exists = text("""
SELECT EXISTS (
    SELECT 1 FROM pg_matviews
    WHERE matviewname = 'recommendations'
    )""")


refresh_mat_view_recommendations = text("""
REFRESH MATERIALIZED VIEW CONCURRENTLY recommendations
""")


create_func_generate_recommendations = text("""
CREATE OR REPLACE FUNCTION generate_recommendations()
RETURNS TABLE (
    profile_id INTEGER,
    similar_profile_id INTEGER,
    distance_meters FLOAT,
    similarity_score FLOAT,
    matched_at TIMESTAMP,
    attitude_id_and_best_uv_ids INTEGER[]
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
        attitude_id_and_best_uv_ids := rec.attitude_id_and_best_uv_ids;
        RETURN NEXT;

        profile_id := rec.profile2_id;
        similar_profile_id := rec.profile1_id;
        RETURN NEXT;
    END LOOP;
END;
$$ LANGUAGE plpgsql
""")

create_mat_view_reccomendations = text("""
CREATE MATERIALIZED VIEW recommendations AS
SELECT * FROM generate_recommendations()
""")


create_unique_index_for_recommendations = text("""
CREATE UNIQUE INDEX idx_recommendations_unique
ON recommendations (profile_id)
""")


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
