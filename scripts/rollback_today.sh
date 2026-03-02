#!/usr/bin/env bash
# rollback_today.sh — Back out all XP, gold, attempts, questions and quests from today
#
# Usage: bash scripts/rollback_today.sh [YYYY-MM-DD]
# Defaults to today's date if no argument given.
#
# What it does:
#   1. Shows a DRY-RUN summary of what will be rolled back
#   2. Asks for confirmation
#   3. Subtracts today's XP/gold from user.xp / user.gold
#   4. Subtracts today's XP/gold/counts from subject_progress
#   5. Rolls back user_skill_progress for skills touched today
#   6. Deletes today's attempt rows
#   7. Deletes today's question_instance rows
#   8. Deletes today's quest_session rows

set -euo pipefail

DB="${1:-./data/app.sqlite3}"
TARGET_DATE="${2:-$(date -u +%Y-%m-%d)}"

if [[ ! -f "$DB" ]]; then
    echo "ERROR: Database not found at $DB"
    exit 1
fi

echo "=== Rollback earnings for date: $TARGET_DATE ==="
echo "Database: $DB"
echo ""

# --- Dry-run summary ---
echo "--- DRY-RUN SUMMARY ---"

echo ""
echo "User totals to subtract:"
sqlite3 "$DB" "
SELECT '  XP to remove: ' || COALESCE(SUM(xp_earned), 0) || ', Gold to remove: ' || COALESCE(SUM(gold_earned), 0) || ', Attempts: ' || COUNT(*)
FROM attempt WHERE date(created_at) = '$TARGET_DATE';
"

echo ""
echo "Subject progress to adjust:"
sqlite3 "$DB" "
SELECT '  ' || qs.subject || ' → XP: ' || SUM(a.xp_earned) || ', Gold: ' || SUM(a.gold_earned) || ', Qs: ' || COUNT(*)
FROM attempt a
JOIN question_instance qi ON qi.id = a.question_id
JOIN quest_session qs ON (',' || qs.question_ids || ',') LIKE ('%,' || qi.id || ',%')
WHERE date(a.created_at) = '$TARGET_DATE'
GROUP BY qs.subject;
"

echo ""
echo "Quests to delete:"
sqlite3 "$DB" "
SELECT '  Quest #' || id || ' (' || COALESCE(skill, unit) || ') — ' || completed || '/' || total_questions || ' completed'
FROM quest_session WHERE date(started_at) = '$TARGET_DATE';
"

echo ""
echo "Skill progress rows touched today:"
sqlite3 "$DB" "
SELECT '  ' || skill || ' — band=' || current_band || ' attempts=' || attempts_total || ' correct=' || attempts_correct
FROM user_skill_progress WHERE date(last_attempted) = '$TARGET_DATE';
"

echo ""
read -r -p "Proceed with rollback? (yes/no): " CONFIRM
if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

# --- Execute rollback ---
echo ""
echo "Rolling back..."

sqlite3 "$DB" <<SQL
BEGIN TRANSACTION;

-- 1. Subtract today's XP and gold from user totals
UPDATE user SET
    xp   = xp   - COALESCE((SELECT SUM(xp_earned)   FROM attempt WHERE date(created_at) = '$TARGET_DATE' AND user_id = user.id), 0),
    gold = gold - COALESCE((SELECT SUM(gold_earned)  FROM attempt WHERE date(created_at) = '$TARGET_DATE' AND user_id = user.id), 0)
WHERE id IN (SELECT DISTINCT user_id FROM attempt WHERE date(created_at) = '$TARGET_DATE');

-- 2. Subtract from subject_progress (join via quest_session to get subject)
UPDATE subject_progress SET
    xp_earned = xp_earned - COALESCE((
        SELECT SUM(a.xp_earned) FROM attempt a
        JOIN question_instance qi ON qi.id = a.question_id
        JOIN quest_session qs ON (',' || qs.question_ids || ',') LIKE ('%,' || qi.id || ',%')
        WHERE date(a.created_at) = '$TARGET_DATE'
        AND a.user_id = subject_progress.user_id
        AND qs.subject = subject_progress.subject
    ), 0),
    gold_earned = gold_earned - COALESCE((
        SELECT SUM(a.gold_earned) FROM attempt a
        JOIN question_instance qi ON qi.id = a.question_id
        JOIN quest_session qs ON (',' || qs.question_ids || ',') LIKE ('%,' || qi.id || ',%')
        WHERE date(a.created_at) = '$TARGET_DATE'
        AND a.user_id = subject_progress.user_id
        AND qs.subject = subject_progress.subject
    ), 0),
    questions_answered = questions_answered - COALESCE((
        SELECT COUNT(*) FROM attempt a
        JOIN question_instance qi ON qi.id = a.question_id
        JOIN quest_session qs ON (',' || qs.question_ids || ',') LIKE ('%,' || qi.id || ',%')
        WHERE date(a.created_at) = '$TARGET_DATE'
        AND a.user_id = subject_progress.user_id
        AND qs.subject = subject_progress.subject
    ), 0),
    questions_correct = questions_correct - COALESCE((
        SELECT COUNT(*) FROM attempt a
        JOIN question_instance qi ON qi.id = a.question_id
        JOIN quest_session qs ON (',' || qs.question_ids || ',') LIKE ('%,' || qi.id || ',%')
        WHERE date(a.created_at) = '$TARGET_DATE'
        AND a.user_id = subject_progress.user_id
        AND a.is_correct = 1
        AND qs.subject = subject_progress.subject
    ), 0)
WHERE user_id IN (SELECT DISTINCT user_id FROM attempt WHERE date(created_at) = '$TARGET_DATE');

-- 3. Roll back user_skill_progress for skills touched today
-- Subtract today's attempts/correct from totals
UPDATE user_skill_progress SET
    attempts_total = attempts_total - COALESCE((
        SELECT COUNT(*) FROM attempt a
        JOIN question_instance qi ON qi.id = a.question_id
        WHERE date(a.created_at) = '$TARGET_DATE'
        AND a.user_id = user_skill_progress.user_id
        AND qi.skill = user_skill_progress.skill
    ), 0),
    attempts_correct = attempts_correct - COALESCE((
        SELECT COUNT(*) FROM attempt a
        JOIN question_instance qi ON qi.id = a.question_id
        WHERE date(a.created_at) = '$TARGET_DATE'
        AND a.user_id = user_skill_progress.user_id
        AND a.is_correct = 1
        AND qi.skill = user_skill_progress.skill
    ), 0),
    streak = 0
WHERE date(last_attempted) = '$TARGET_DATE';

-- 4. Delete today's attempts
DELETE FROM attempt WHERE date(created_at) = '$TARGET_DATE';

-- 5. Delete today's question instances
DELETE FROM question_instance WHERE date(created_at) = '$TARGET_DATE';

-- 6. Delete today's quest sessions
DELETE FROM quest_session WHERE date(started_at) = '$TARGET_DATE';

COMMIT;
SQL

echo ""
echo "Done. Post-rollback state:"
sqlite3 "$DB" "
SELECT display_name, xp, gold FROM user;
"
sqlite3 "$DB" "
SELECT 'Subject: ' || subject || ' XP=' || xp_earned || ' Gold=' || gold_earned || ' Qs=' || questions_answered
FROM subject_progress;
"

echo ""
echo "Rollback complete for $TARGET_DATE."
