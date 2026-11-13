# Visual loop check: grow_plants

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.106 | ≤ 0.15 | pass |
| left wrist error p90 | 0.198 | ≤ 0.3 | pass |
| left elbow height error median | 0.062 | ≤ 0.2 | pass |
| left peak height error | 0.074 | ≤ 0.2 | pass |
| left handshape error median | 0.549 | ≤ 0.3 | FAIL |
| right wrist error median | 0.112 | ≤ 0.15 | pass |
| right wrist error p90 | 0.202 | ≤ 0.3 | pass |
| right elbow height error median | 0.092 | ≤ 0.2 | pass |
| right peak height error | 0.078 | ≤ 0.2 | pass |
| right handshape error median | 0.205 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.106 | 0.198 |
| wrist height error signed | 0.099 | 0.161 |
| wrist sideways error signed | 0.03 | 0.052 |
| wrist height vs nose error signed | 0.086 | 0.139 |
| elbow height error | 0.062 | 0.095 |
| handshape error | 0.549 | 1.413 |

Highest wrist point (y, shoulder widths): source 0.389, avatar 0.463, difference 0.074.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.112 | 0.202 |
| wrist height error signed | 0.092 | 0.157 |
| wrist sideways error signed | -0.062 | -0.001 |
| wrist height vs nose error signed | 0.076 | 0.132 |
| elbow height error | 0.092 | 0.192 |
| handshape error | 0.205 | 1.437 |

Highest wrist point (y, shoulder widths): source 0.047, avatar 0.125, difference 0.078.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
