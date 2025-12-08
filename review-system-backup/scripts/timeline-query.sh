#!/bin/bash
#
# Timeline Query Helper - Query chronological event log
#
# Usage:
#   timeline-query.sh                  # Last 20 events
#   timeline-query.sh today            # Today's events
#   timeline-query.sh week             # Last 7 days
#   timeline-query.sh commits          # All commits
#   timeline-query.sh reviews          # All reviews
#   timeline-query.sh facts            # All fact extractions
#   timeline-query.sh <search>         # Search for pattern
#   timeline-query.sh stats            # Summary statistics
#

# Find project root
find_project_root() {
    local dir="${1:-$(pwd)}"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.knowledge-db" ] || [ -d "$dir/.serena" ] || [ -d "$dir/.claude" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    echo ""
}

PROJECT_ROOT=$(find_project_root)
if [ -z "$PROJECT_ROOT" ]; then
    echo "❌ No project root found (no .knowledge-db/, .serena/, or .claude/)"
    exit 1
fi

TIMELINE="$PROJECT_ROOT/.knowledge-db/timeline.txt"

if [ ! -f "$TIMELINE" ]; then
    echo "📋 Timeline: $TIMELINE"
    echo "ℹ️  No timeline events yet. Events are logged automatically after:"
    echo "   - Code reviews (fact extraction)"
    echo "   - Git commits"
    exit 0
fi

QUERY="${1:-last}"

case "$QUERY" in
    last|"")
        echo "📋 Last 20 events from $TIMELINE"
        echo "─────────────────────────────────────────────"
        tail -20 "$TIMELINE"
        ;;
    today)
        TODAY=$(date '+%m-%d')
        echo "📋 Today's events ($TODAY)"
        echo "─────────────────────────────────────────────"
        grep "^$TODAY" "$TIMELINE" || echo "No events today"
        ;;
    yesterday)
        YESTERDAY=$(date -d "yesterday" '+%m-%d' 2>/dev/null || date -v-1d '+%m-%d')
        echo "📋 Yesterday's events ($YESTERDAY)"
        echo "─────────────────────────────────────────────"
        grep "^$YESTERDAY" "$TIMELINE" || echo "No events yesterday"
        ;;
    week)
        echo "📋 Last 7 days of events"
        echo "─────────────────────────────────────────────"
        for i in $(seq 0 6); do
            DAY=$(date -d "$i days ago" '+%m-%d' 2>/dev/null || date -v-${i}d '+%m-%d')
            grep "^$DAY" "$TIMELINE" 2>/dev/null
        done | sort -r
        ;;
    commits)
        echo "📋 All commits"
        echo "─────────────────────────────────────────────"
        grep "| commit |" "$TIMELINE" || echo "No commits logged"
        ;;
    reviews)
        echo "📋 All reviews"
        echo "─────────────────────────────────────────────"
        grep "| review |" "$TIMELINE" || echo "No reviews logged"
        ;;
    facts)
        echo "📋 All fact extractions"
        echo "─────────────────────────────────────────────"
        grep "facts" "$TIMELINE" || echo "No facts logged"
        ;;
    stats)
        TOTAL=$(wc -l < "$TIMELINE")
        COMMITS=$(grep -c "| commit |" "$TIMELINE" 2>/dev/null || echo 0)
        REVIEWS=$(grep -c "| review |" "$TIMELINE" 2>/dev/null || echo 0)
        FIRST=$(head -1 "$TIMELINE" | cut -d'|' -f1 | xargs)
        LAST=$(tail -1 "$TIMELINE" | cut -d'|' -f1 | xargs)

        echo "📊 Timeline Statistics"
        echo "─────────────────────────────────────────────"
        echo "Total events:  $TOTAL"
        echo "Commits:       $COMMITS"
        echo "Reviews:       $REVIEWS"
        echo "First event:   $FIRST"
        echo "Last event:    $LAST"
        echo ""
        echo "📁 File: $TIMELINE"
        echo "📦 Size: $(du -h "$TIMELINE" | cut -f1)"
        ;;
    help|-h|--help)
        echo "Timeline Query Helper"
        echo ""
        echo "Usage: timeline-query.sh [command|search]"
        echo ""
        echo "Commands:"
        echo "  last       Last 20 events (default)"
        echo "  today      Today's events"
        echo "  yesterday  Yesterday's events"
        echo "  week       Last 7 days"
        echo "  commits    All git commits"
        echo "  reviews    All code reviews"
        echo "  facts      All fact extractions"
        echo "  stats      Summary statistics"
        echo ""
        echo "Search:"
        echo "  <pattern>  Search for pattern (case-insensitive)"
        echo ""
        echo "Examples:"
        echo "  timeline-query.sh security    # Find security-related events"
        echo "  timeline-query.sh BLE         # Find BLE-related events"
        echo "  timeline-query.sh stats       # Show statistics"
        ;;
    *)
        echo "📋 Search results for: $QUERY"
        echo "─────────────────────────────────────────────"
        grep -i "$QUERY" "$TIMELINE" || echo "No matches found for '$QUERY'"
        ;;
esac
