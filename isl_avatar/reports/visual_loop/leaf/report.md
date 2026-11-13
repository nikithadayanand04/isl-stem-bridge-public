# Visual loop check: leaf

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: PASS

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.138 | ≤ 0.15 | pass |
| left wrist error p90 | 0.148 | ≤ 0.3 | pass |
| left elbow height error median | 0.044 | ≤ 0.2 | pass |
| left peak height error | 0.07 | ≤ 0.2 | pass |
| right wrist error median | 0.073 | ≤ 0.15 | pass |
| right wrist error p90 | 0.102 | ≤ 0.3 | pass |
| right elbow height error median | 0.043 | ≤ 0.2 | pass |
| right peak height error | 0.043 | ≤ 0.2 | pass |
| right handshape error median | 0.287 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.138 | 0.148 |
| wrist height error signed | -0.084 | -0.062 |
| wrist sideways error signed | -0.087 | 0.019 |
| wrist height vs nose error signed | -0.088 | -0.048 |
| elbow height error | 0.044 | 0.071 |

Highest wrist point (y, shoulder widths): source 1.525, avatar 1.455, difference 0.07.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.073 | 0.102 |
| wrist height error signed | 0.058 | 0.084 |
| wrist sideways error signed | -0.012 | 0.026 |
| wrist height vs nose error signed | 0.064 | 0.093 |
| elbow height error | 0.043 | 0.123 |
| handshape error | 0.287 | 0.537 |

Highest wrist point (y, shoulder widths): source -0.14, avatar -0.097, difference 0.043.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
