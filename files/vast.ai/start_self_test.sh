#!/bin/bash
#INFO: Redirect all output to self_test.log
exec &>>/var/lib/vastai_kaalia/self_test.log

MACHINE_ID=$1
GPU_PPH=$2
MIN_COUNT=$3
RESERVED_DISCOUNT=$4
SERVER_URL=$5
MACHINE_API_KEY=$6
SESSION_API_KEY=$7

export VAST_URL=$SERVER_URL

echo "========================================="
echo "Starting self-test for machine $MACHINE_ID"
echo "Server: $SERVER_URL"
echo "Timestamp: $(date)"
echo "========================================="

echo "Waiting 10 minutes for daemon to initialize..."
sleep 10m
echo "Done waiting."

echo "Checking if machine $MACHINE_ID is already listed..."
if python3 /var/lib/vastai_kaalia/vast show machine $MACHINE_ID --raw --url $SERVER_URL --api-key $SESSION_API_KEY 2>&1 | grep -q '"listed": true'; then
  echo "Machine $MACHINE_ID is already listed. Exiting early."
  echo "Timestamp: $(date)"
  echo "========================================="
  exit 0
fi

echo "Machine is not listed. Proceeding with self-test..."
current_time=$(date +%s)
three_hours_from_now=$((current_time + 10800))

echo ""
echo "Listing machine with parameters (GPU_PPH=$GPU_PPH, min_count=$MIN_COUNT, reserved_discount=$RESERVED_DISCOUNT)..."
python3 /var/lib/vastai_kaalia/vast list machine $MACHINE_ID -g $GPU_PPH -m $MIN_COUNT -r $RESERVED_DISCOUNT -e $three_hours_from_now --url $SERVER_URL --api-key $SESSION_API_KEY 2>&1
list_exit_code=$?
echo "List command exit code: $list_exit_code"

echo ""
echo "Running self-test..."
python3 /var/lib/vastai_kaalia/vast self-test machine $MACHINE_ID --ignore-requirements --url $SERVER_URL --api-key $SESSION_API_KEY 2>&1
EXIT_CODE=$?
echo "Self-test exit code: $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
  echo "Self-test PASSED. Sending notification to server..."
  response=$(curl -X POST "${SERVER_URL}/api/v0/daemon/report_self_test_results/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $SESSION_API_KEY" \
    -d "{\"machine_api_key\": \"$MACHINE_API_KEY\"}")
  echo "Server response:"
  echo "$response"
else
  echo "Self-test FAILED with exit code: $EXIT_CODE"
fi

echo "Unlisting machine..."
python3 /var/lib/vastai_kaalia/vast unlist machine $MACHINE_ID --url $SERVER_URL --api-key $SESSION_API_KEY 2>&1

echo "========================================="
echo "Self-test completed"
echo "Exit code: $EXIT_CODE"
echo "Timestamp: $(date)"
echo "========================================="
