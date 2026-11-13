# Visual loop check: water

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: PASS

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.086 | ≤ 0.15 | pass |
| left wrist error p90 | 0.086 | ≤ 0.3 | pass |
| left elbow height error median | 0.024 | ≤ 0.2 | pass |
| left peak height error | 0.021 | ≤ 0.2 | pass |
| right wrist error median | 0.039 | ≤ 0.15 | pass |
| right wrist error p90 | 0.129 | ≤ 0.3 | pass |
| right elbow height error median | 0.098 | ≤ 0.2 | pass |
| right peak height error | 0.045 | ≤ 0.2 | pass |
| right handshape error median | 0.266 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.086 | 0.086 |
| wrist height error signed | 0.044 | 0.044 |
| wrist sideways error signed | 0.074 | 0.074 |
| wrist height vs nose error signed | -0.013 | -0.013 |
| elbow height error | 0.024 | 0.043 |

Highest wrist point (y, shoulder widths): source 1.411, avatar 1.433, difference 0.021.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.039 | 0.129 |
| wrist height error signed | 0.011 | 0.124 |
| wrist sideways error signed | 0.003 | 0.024 |
| wrist height vs nose error signed | 0.057 | 0.111 |
| elbow height error | 0.098 | 0.136 |
| handshape error | 0.266 | 0.387 |

Highest wrist point (y, shoulder widths): source -0.665, avatar -0.71, difference 0.045.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
