#!/usr/bin/env bash
# Rebuild working databases from scratch.
#   ./reset.sh            -> all (shop, transit, lab, scenario)
#   ./reset.sh shop       -> just one
cd "$(dirname "$0")" && exec ./drill reset "${@:-all}"
