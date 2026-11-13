# Visual loop check: magnet

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.108 | ≤ 0.15 | pass |
| left wrist error p90 | 0.212 | ≤ 0.3 | pass |
| left elbow height error median | 0.067 | ≤ 0.2 | pass |
| left peak height error | 0.026 | ≤ 0.2 | pass |
| left handshape error median | 0.34 | ≤ 0.3 | FAIL |
| right wrist error median | 0.103 | ≤ 0.15 | pass |
| right wrist error p90 | 0.162 | ≤ 0.3 | pass |
| right elbow height error median | 0.021 | ≤ 0.2 | pass |
| right peak height error | 0.146 | ≤ 0.2 | pass |
| right handshape error median | 0.198 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.108 | 0.212 |
| wrist height error signed | 0.069 | 0.157 |
| wrist sideways error signed | 0.008 | 0.092 |
| wrist height vs nose error signed | 0.095 | 0.16 |
| elbow height error | 0.067 | 0.188 |
| handshape error | 0.34 | 0.69 |

Highest wrist point (y, shoulder widths): source 0.015, avatar 0.041, difference 0.026.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.103 | 0.162 |
| wrist height error signed | 0.075 | 0.14 |
| wrist sideways error signed | 0.01 | 0.083 |
| wrist height vs nose error signed | 0.091 | 0.179 |
| elbow height error | 0.021 | 0.141 |
| handshape error | 0.198 | 0.362 |

Highest wrist point (y, shoulder widths): source -0.431, avatar -0.576, difference 0.146.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
