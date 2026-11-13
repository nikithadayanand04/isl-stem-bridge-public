# Visual loop check: energy

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.152 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.342 | ≤ 0.3 | FAIL |
| left elbow height error median | 0.025 | ≤ 0.2 | pass |
| left peak height error | 0.077 | ≤ 0.2 | pass |
| left handshape error median | 0.318 | ≤ 0.3 | FAIL |
| right wrist error median | 0.096 | ≤ 0.15 | pass |
| right wrist error p90 | 0.138 | ≤ 0.3 | pass |
| right elbow height error median | 0.044 | ≤ 0.2 | pass |
| right peak height error | 0.001 | ≤ 0.2 | pass |
| right handshape error median | 0.141 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.152 | 0.342 |
| wrist height error signed | 0.116 | 0.338 |
| wrist sideways error signed | -0.012 | 0.059 |
| wrist height vs nose error signed | 0.067 | 0.213 |
| elbow height error | 0.025 | 0.074 |
| handshape error | 0.318 | 0.966 |

Highest wrist point (y, shoulder widths): source 0.191, avatar 0.267, difference 0.077.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.096 | 0.138 |
| wrist height error signed | 0.068 | 0.133 |
| wrist sideways error signed | -0.003 | 0.034 |
| wrist height vs nose error signed | 0.006 | 0.081 |
| elbow height error | 0.044 | 0.086 |
| handshape error | 0.141 | 0.34 |

Highest wrist point (y, shoulder widths): source -0.081, avatar -0.082, difference 0.001.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
