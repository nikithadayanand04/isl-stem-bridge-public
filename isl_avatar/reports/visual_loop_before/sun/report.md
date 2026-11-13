# Visual loop check: sun

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| right wrist error median | 0.259 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.384 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.155 | ≤ 0.2 | pass |
| right peak height error | 0.188 | ≤ 0.2 | pass |
| right handshape error median | 0.24 | ≤ 0.3 | pass |

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.259 | 0.384 |
| wrist height error signed | 0.214 | 0.379 |
| wrist sideways error signed | 0.126 | 0.171 |
| wrist height vs nose error signed | 0.202 | 0.342 |
| elbow height error | 0.155 | 0.191 |
| handshape error | 0.24 | 1.225 |

Highest wrist point (y, shoulder widths): source -1.079, avatar -0.891, difference 0.188.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
