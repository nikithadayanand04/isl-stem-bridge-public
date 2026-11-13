# Visual loop check: food

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| right wrist error median | 0.161 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.25 | ≤ 0.3 | pass |
| right elbow height error median | 0.129 | ≤ 0.2 | pass |
| right peak height error | 0.147 | ≤ 0.2 | pass |
| right handshape error median | 0.245 | ≤ 0.3 | pass |

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.161 | 0.25 |
| wrist height error signed | -0.131 | 0.224 |
| wrist sideways error signed | 0.067 | 0.076 |
| wrist height vs nose error signed | -0.073 | 0.326 |
| elbow height error | 0.129 | 0.148 |
| handshape error | 0.245 | 0.462 |

Highest wrist point (y, shoulder widths): source 0.027, avatar -0.119, difference 0.147.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
