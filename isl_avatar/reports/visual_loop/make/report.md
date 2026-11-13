# Visual loop check: make

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.114 | ≤ 0.15 | pass |
| left wrist error p90 | 0.159 | ≤ 0.3 | pass |
| left elbow height error median | 0.042 | ≤ 0.2 | pass |
| left peak height error | 0.004 | ≤ 0.2 | pass |
| left handshape error median | 0.569 | ≤ 0.3 | FAIL |
| right wrist error median | 0.14 | ≤ 0.15 | pass |
| right wrist error p90 | 0.247 | ≤ 0.3 | pass |
| right elbow height error median | 0.017 | ≤ 0.2 | pass |
| right peak height error | 0.062 | ≤ 0.2 | pass |
| right handshape error median | 0.293 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.114 | 0.159 |
| wrist height error signed | 0.103 | 0.125 |
| wrist sideways error signed | -0.017 | 0.028 |
| wrist height vs nose error signed | 0.077 | 0.12 |
| elbow height error | 0.042 | 0.08 |
| handshape error | 0.569 | 1.118 |

Highest wrist point (y, shoulder widths): source 0.542, avatar 0.537, difference 0.004.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.14 | 0.247 |
| wrist height error signed | 0.13 | 0.247 |
| wrist sideways error signed | -0.033 | 0.057 |
| wrist height vs nose error signed | 0.113 | 0.206 |
| elbow height error | 0.017 | 0.059 |
| handshape error | 0.293 | 0.537 |

Highest wrist point (y, shoulder widths): source 0.281, avatar 0.343, difference 0.062.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
