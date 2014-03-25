#!/bin/sh
set -e

FULL_LOGS=$1
AUTOGEN_DIR=./nova_ocl_autogen
STRIPPED_LOGS=$AUTOGEN_DIR/stripped_logs.txt
PARSED_LOGS=$AUTOGEN_DIR/parsed_logs.txt
CALL_DB=$AUTOGEN_DIR/call_db.json
API_STATS=$AUTOGEN_DIR/api_stats.txt
#API_JSON=api.json

echo "Stripping logs..."
$AUTOGEN_DIR/strip_logs.sh $1 > $STRIPPED_LOGS
echo "Parsing logs..."
$AUTOGEN_DIR/parse_logs.py $STRIPPED_LOGS > $PARSED_LOGS
echo "Building call database..."
$AUTOGEN_DIR/build_call_db.py $PARSED_LOGS > $CALL_DB
echo "Dumping API stats..."
$AUTOGEN_DIR/api_stats.py $CALL_DB > $API_STATS
echo "Building API..."
$AUTOGEN_DIR/build_api.py $CALL_DB
