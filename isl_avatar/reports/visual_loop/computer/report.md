# Visual loop check: computer

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.102 | ≤ 0.15 | pass |
| left wrist error p90 | 0.15 | ≤ 0.3 | pass |
| left elbow height error median | 0.046 | ≤ 0.2 | pass |
| left peak height error | 0.027 | ≤ 0.2 | pass |
| left handshape error median | 0.306 | ≤ 0.3 | FAIL |
| right wrist error median | 0.105 | ≤ 0.15 | pass |
| right wrist error p90 | 0.175 | ≤ 0.3 | pass |
| right elbow height error median | 0.124 | ≤ 0.2 | pass |
| right peak height error | 0.059 | ≤ 0.2 | pass |
| right handshape error median | 0.336 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.102 | 0.15 |
| wrist height error signed | 0.077 | 0.116 |
| wrist sideways error signed | 0.052 | 0.091 |
| wrist height vs nose error signed | 0.044 | 0.084 |
| elbow height error | 0.046 | 0.097 |
| handshape error | 0.306 | 0.904 |

Highest wrist point (y, shoulder widths): source -0.152, avatar -0.179, difference 0.027.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.105 | 0.175 |
| wrist height error signed | 0.097 | 0.125 |
| wrist sideways error signed | -0.002 | 0.092 |
| wrist height vs nose error signed | 0.053 | 0.107 |
| elbow height error | 0.124 | 0.186 |
| handshape error | 0.336 | 1.798 |

Highest wrist point (y, shoulder widths): source -0.088, avatar -0.147, difference 0.059.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
