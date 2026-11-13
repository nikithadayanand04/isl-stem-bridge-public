#!/bin/sh
# Re-bake every sign whose motion passed QC, validate each one, then export the GLB.
#
#   sh tools/bake_all.sh            # all signs with motion_qc = pass and a motion/v2 file
#   sh tools/bake_all.sh leaf sun   # only these
#
# Needs Blender 4.5 (set BLENDER=/path/to/blender if it is not in the default place) and the
# project venv (.venv) for the reports. Signs that fail QC are never baked: the baker refuses.
set -e
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
PY=".venv/bin/python"
[ -x "$PY" ] || PY=python3

if [ "$#" -gt 0 ]; then
  SIGNS="$*"
else
  SIGNS=$(python3 -c "
import csv
for r in csv.DictReader(open('registry/signs.csv')):
    if r['motion_qc'] in ('pass', 'pass_exception') and r['motion_file'].startswith('motion/v2/'):
        print(r['sign_id'])")
fi

for s in $SIGNS; do
  echo "=== $s"
  # A documented exception in the registry (motion_qc = pass_exception, QC EXCEPTION in notes) is
  # passed on to the baker; anything else that fails QC is refused by the baker.
  EXC=$(python3 -c "
import csv, sys
r = next(r for r in csv.DictReader(open('registry/signs.csv')) if r['sign_id'] == sys.argv[1])
print('see registry/signs.csv notes: QC EXCEPTION' if r['motion_qc'] == 'pass_exception' else '')" "$s")
  set -- --motion "motion/v2/$s.json" --bone-map tools/bone_maps/mixamo.json --save
  [ -n "$EXC" ] && set -- "$@" --qc-exception "$EXC"
  "$BLENDER" -b avatar/avatar_source.blend --python tools/retarget_blender.py -- "$@" 2>&1 \
      | grep -E "Finger joint|Thumb overlap|Rest pose|Resampled|Detector switches|Face neutral|Depth-flipped|world points|QC EXCEPTION|Arm IK|Baked|baked|Error|refus|quality" || true
  SRC_FPS=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['fps'])" "motion/v2/$s.json")
  "$BLENDER" -b avatar/avatar_source.blend --python tools/animation_validator.py -- \
      --track "$s" --bone-map tools/bone_maps/mixamo.json --source-fps "$SRC_FPS" \
      --out "reports/v2/$s/avatar_samples.json" 2>&1 \
      | grep -E "Sampled|Error" || true
  "$PY" tools/motion_report.py --motion "motion/v2/$s.json" --avatar "reports/v2/$s/avatar_samples.json" \
      --out "reports/v2/$s" | grep -E "geometric|Report"
done

# Idle = the natural rest pose (tools/rest_pose.py); every sign starts and ends in it.
"$BLENDER" -b avatar/avatar_source.blend --python tools/retarget_blender.py -- \
    --make-idle --bone-map tools/bone_maps/mixamo.json --save 2>&1 | grep -E "idle|Error" || true
python3 tools/clip_timing.py > /dev/null
"$BLENDER" -b avatar/avatar_source.blend --python tools/retarget_blender.py -- --export avatar/avatar.glb 2>&1 \
    | grep -E "Exported|Error"
python3 tools/check_registry.py | tail -1
