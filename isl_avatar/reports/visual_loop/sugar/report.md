# Visual loop check: sugar

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.143 | ≤ 0.15 | pass |
| left wrist error p90 | 0.158 | ≤ 0.3 | pass |
| left elbow height error median | 0.068 | ≤ 0.2 | pass |
| left peak height error | 0.082 | ≤ 0.2 | pass |
| right wrist error median | 0.096 | ≤ 0.15 | pass |
| right wrist error p90 | 0.129 | ≤ 0.3 | pass |
| right elbow height error median | 0.025 | ≤ 0.2 | pass |
| right peak height error | 0.055 | ≤ 0.2 | pass |
| right handshape error median | 0.474 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.143 | 0.158 |
| wrist height error signed | -0.106 | -0.035 |
| wrist sideways error signed | 0.088 | 0.117 |
| wrist height vs nose error signed | -0.056 | -0.054 |
| elbow height error | 0.068 | 0.136 |

Highest wrist point (y, shoulder widths): source 1.527, avatar 1.445, difference 0.082.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.096 | 0.129 |
| wrist height error signed | 0.08 | 0.124 |
| wrist sideways error signed | -0.037 | -0.0 |
| wrist height vs nose error signed | 0.066 | 0.155 |
| elbow height error | 0.025 | 0.071 |
| handshape error | 0.474 | 0.685 |

Highest wrist point (y, shoulder widths): source -0.12, avatar -0.065, difference 0.055.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
