#!/bin/bash
# Review Logger - Logs review activity for K-LEAN dashboard
# Usage: source this file, then call log_review_start/log_review_end

REVIEW_LOG="${KLEAN_DIR:-$HOME/.klean}/logs/reviews.log"
mkdir -p "$(dirname "$REVIEW_LOG")"

log_review_start() {
    local cmd="$1"
    local model="$2"
    local focus="$3"
    local output_path="$4"

    echo "{\"ts\": \"$(date -Iseconds)\", \"event\": \"start\", \"cmd\": \"$cmd\", \"model\": \"$model\", \"focus\": \"$focus\", \"output\": \"$output_path\"}" >> "$REVIEW_LOG"
}

log_review_end() {
    local cmd="$1"
    local model="$2"
    local output_path="$3"
    local status="${4:-success}"
    local duration_ms="$5"

    echo "{\"ts\": \"$(date -Iseconds)\", \"event\": \"end\", \"cmd\": \"$cmd\", \"model\": \"$model\", \"output\": \"$output_path\", \"status\": \"$status\", \"duration_ms\": $duration_ms}" >> "$REVIEW_LOG"
}

log_review_error() {
    local cmd="$1"
    local model="$2"
    local error="$3"

    echo "{\"ts\": \"$(date -Iseconds)\", \"event\": \"error\", \"cmd\": \"$cmd\", \"model\": \"$model\", \"error\": \"$error\"}" >> "$REVIEW_LOG"
}
