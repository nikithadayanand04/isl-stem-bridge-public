# Visual loop check: oxygen_sign_2

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.251 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.281 | ≤ 0.3 | pass |
| left elbow height error median | 0.046 | ≤ 0.2 | pass |
| left peak height error | 0.152 | ≤ 0.2 | pass |
| left handshape error median | 0.665 | ≤ 0.3 | FAIL |
| right wrist error median | 0.106 | ≤ 0.15 | pass |
| right wrist error p90 | 0.204 | ≤ 0.3 | pass |
| right elbow height error median | 0.032 | ≤ 0.2 | pass |
| right peak height error | 0.058 | ≤ 0.2 | pass |
| right handshape error median | 0.313 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.251 | 0.281 |
| wrist height error signed | 0.239 | 0.271 |
| wrist sideways error signed | 0.066 | 0.085 |
| wrist height vs nose error signed | 0.339 | 0.37 |
| elbow height error | 0.046 | 0.062 |
| handshape error | 0.665 | 1.15 |

Highest wrist point (y, shoulder widths): source 0.738, avatar 0.891, difference 0.152.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.106 | 0.204 |
| wrist height error signed | -0.025 | 0.179 |
| wrist sideways error signed | -0.078 | 0.098 |
| wrist height vs nose error signed | 0.097 | 0.238 |
| elbow height error | 0.032 | 0.055 |
| handshape error | 0.313 | 0.416 |

Highest wrist point (y, shoulder widths): source -0.201, avatar -0.259, difference 0.058.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
