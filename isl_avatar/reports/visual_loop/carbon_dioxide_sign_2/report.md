# Visual loop check: carbon_dioxide_sign_2

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.227 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.308 | ≤ 0.3 | FAIL |
| left elbow height error median | 0.04 | ≤ 0.2 | pass |
| left peak height error | 0.015 | ≤ 0.2 | pass |
| left handshape error median | 0.496 | ≤ 0.3 | FAIL |
| right wrist error median | 0.17 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.426 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.018 | ≤ 0.2 | pass |
| right peak height error | 0.017 | ≤ 0.2 | pass |
| right handshape error median | 0.268 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.227 | 0.308 |
| wrist height error signed | 0.216 | 0.29 |
| wrist sideways error signed | 0.072 | 0.118 |
| wrist height vs nose error signed | 0.252 | 0.357 |
| elbow height error | 0.04 | 0.067 |
| handshape error | 0.496 | 1.648 |

Highest wrist point (y, shoulder widths): source 0.646, avatar 0.661, difference 0.015.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.17 | 0.426 |
| wrist height error signed | 0.156 | 0.423 |
| wrist sideways error signed | -0.012 | 0.094 |
| wrist height vs nose error signed | 0.207 | 0.436 |
| elbow height error | 0.018 | 0.063 |
| handshape error | 0.268 | 0.477 |

Highest wrist point (y, shoulder widths): source -0.256, avatar -0.272, difference 0.017.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
