# Visual loop check: magnet_sign_2

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.247 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.295 | ≤ 0.3 | pass |
| left elbow height error median | 0.034 | ≤ 0.2 | pass |
| left peak height error | 0.21 | ≤ 0.2 | FAIL |
| left handshape error median | 0.267 | ≤ 0.3 | pass |
| right wrist error median | 0.316 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.36 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.026 | ≤ 0.2 | pass |
| right peak height error | 0.205 | ≤ 0.2 | FAIL |
| right handshape error median | 0.3 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.247 | 0.295 |
| wrist height error signed | 0.243 | 0.285 |
| wrist sideways error signed | 0.047 | 0.096 |
| wrist height vs nose error signed | 0.279 | 0.362 |
| elbow height error | 0.034 | 0.051 |
| handshape error | 0.267 | 0.754 |

Highest wrist point (y, shoulder widths): source 0.435, avatar 0.645, difference 0.21.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.316 | 0.36 |
| wrist height error signed | 0.304 | 0.356 |
| wrist sideways error signed | 0.04 | 0.117 |
| wrist height vs nose error signed | 0.331 | 0.405 |
| elbow height error | 0.026 | 0.054 |
| handshape error | 0.3 | 0.64 |

Highest wrist point (y, shoulder widths): source 0.426, avatar 0.631, difference 0.205.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
