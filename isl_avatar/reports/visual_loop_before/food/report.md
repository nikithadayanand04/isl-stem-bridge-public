# Visual loop check: food

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| right wrist error median | 0.325 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.354 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.022 | ≤ 0.2 | pass |
| right peak height error | 0.317 | ≤ 0.2 | FAIL |
| right handshape error median | 0.228 | ≤ 0.3 | pass |

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.325 | 0.354 |
| wrist height error signed | 0.324 | 0.353 |
| wrist sideways error signed | -0.004 | 0.022 |
| wrist height vs nose error signed | 0.399 | 0.43 |
| elbow height error | 0.022 | 0.087 |
| handshape error | 0.228 | 0.303 |

Highest wrist point (y, shoulder widths): source 0.027, avatar 0.344, difference 0.317.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
