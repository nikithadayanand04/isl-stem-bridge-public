# Visual loop check: oxygen_sign_2

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.286 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.343 | ≤ 0.3 | FAIL |
| left elbow height error median | 0.02 | ≤ 0.2 | pass |
| left peak height error | 0.298 | ≤ 0.2 | FAIL |
| left handshape error median | 0.76 | ≤ 0.3 | FAIL |
| right wrist error median | 0.301 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.411 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.074 | ≤ 0.2 | pass |
| right peak height error | 0.276 | ≤ 0.2 | FAIL |
| right handshape error median | 0.331 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.286 | 0.343 |
| wrist height error signed | 0.272 | 0.322 |
| wrist sideways error signed | 0.098 | 0.146 |
| wrist height vs nose error signed | 0.334 | 0.426 |
| elbow height error | 0.02 | 0.041 |
| handshape error | 0.76 | 1.574 |

Highest wrist point (y, shoulder widths): source 0.738, avatar 1.036, difference 0.298.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.301 | 0.411 |
| wrist height error signed | 0.29 | 0.399 |
| wrist sideways error signed | -0.049 | 0.084 |
| wrist height vs nose error signed | 0.363 | 0.478 |
| elbow height error | 0.074 | 0.126 |
| handshape error | 0.331 | 0.522 |

Highest wrist point (y, shoulder widths): source -0.201, avatar 0.075, difference 0.276.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
