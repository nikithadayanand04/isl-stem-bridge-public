# Visual loop check: sugar

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| right wrist error median | 0.355 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.414 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.045 | ≤ 0.2 | pass |
| right peak height error | 0.374 | ≤ 0.2 | FAIL |
| right handshape error median | 0.599 | ≤ 0.3 | FAIL |

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.355 | 0.414 |
| wrist height error signed | 0.34 | 0.387 |
| wrist sideways error signed | 0.103 | 0.15 |
| wrist height vs nose error signed | 0.312 | 0.394 |
| elbow height error | 0.045 | 0.091 |
| handshape error | 0.599 | 0.877 |

Highest wrist point (y, shoulder widths): source -0.12, avatar 0.254, difference 0.374.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
