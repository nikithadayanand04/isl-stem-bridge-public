# Visual loop check: photosynthesis

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.135 | ≤ 0.15 | pass |
| left wrist error p90 | 0.183 | ≤ 0.3 | pass |
| left elbow height error median | 0.041 | ≤ 0.2 | pass |
| left peak height error | 0.087 | ≤ 0.2 | pass |
| left handshape error median | 0.524 | ≤ 0.3 | FAIL |
| right wrist error median | 0.09 | ≤ 0.15 | pass |
| right wrist error p90 | 0.178 | ≤ 0.3 | pass |
| right elbow height error median | 0.041 | ≤ 0.2 | pass |
| right peak height error | 0.075 | ≤ 0.2 | pass |
| right handshape error median | 0.205 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.135 | 0.183 |
| wrist height error signed | 0.1 | 0.156 |
| wrist sideways error signed | 0.059 | 0.137 |
| wrist height vs nose error signed | 0.15 | 0.222 |
| elbow height error | 0.041 | 0.093 |
| handshape error | 0.524 | 2.151 |

Highest wrist point (y, shoulder widths): source -0.243, avatar -0.156, difference 0.087.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.09 | 0.178 |
| wrist height error signed | 0.055 | 0.131 |
| wrist sideways error signed | 0.023 | 0.146 |
| wrist height vs nose error signed | 0.115 | 0.201 |
| elbow height error | 0.041 | 0.119 |
| handshape error | 0.205 | 0.638 |

Highest wrist point (y, shoulder widths): source -0.711, avatar -0.786, difference 0.075.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
