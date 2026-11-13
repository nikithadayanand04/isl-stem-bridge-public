# Visual loop check: carbon_dioxide_sign_2

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.284 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.322 | ≤ 0.3 | FAIL |
| left elbow height error median | 0.029 | ≤ 0.2 | pass |
| left peak height error | 0.305 | ≤ 0.2 | FAIL |
| left handshape error median | 0.506 | ≤ 0.3 | FAIL |
| right wrist error median | 0.357 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.441 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.067 | ≤ 0.2 | pass |
| right peak height error | 0.321 | ≤ 0.2 | FAIL |
| right handshape error median | 0.279 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.284 | 0.322 |
| wrist height error signed | 0.261 | 0.304 |
| wrist sideways error signed | 0.101 | 0.158 |
| wrist height vs nose error signed | 0.307 | 0.383 |
| elbow height error | 0.029 | 0.079 |
| handshape error | 0.506 | 1.019 |

Highest wrist point (y, shoulder widths): source 0.646, avatar 0.951, difference 0.305.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.357 | 0.441 |
| wrist height error signed | 0.354 | 0.436 |
| wrist sideways error signed | 0.012 | 0.095 |
| wrist height vs nose error signed | 0.42 | 0.482 |
| elbow height error | 0.067 | 0.181 |
| handshape error | 0.279 | 0.476 |

Highest wrist point (y, shoulder widths): source -0.256, avatar 0.065, difference 0.321.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
