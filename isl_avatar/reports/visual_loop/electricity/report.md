# Visual loop check: electricity

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: PASS

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.121 | ≤ 0.15 | pass |
| left wrist error p90 | 0.121 | ≤ 0.3 | pass |
| left elbow height error median | 0.013 | ≤ 0.2 | pass |
| left peak height error | 0.007 | ≤ 0.2 | pass |
| right wrist error median | 0.073 | ≤ 0.15 | pass |
| right wrist error p90 | 0.163 | ≤ 0.3 | pass |
| right elbow height error median | 0.043 | ≤ 0.2 | pass |
| right peak height error | 0.069 | ≤ 0.2 | pass |
| right handshape error median | 0.265 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.121 | 0.121 |
| wrist height error signed | 0.07 | 0.07 |
| wrist sideways error signed | 0.098 | 0.098 |
| wrist height vs nose error signed | -0.014 | -0.014 |
| elbow height error | 0.013 | 0.037 |

Highest wrist point (y, shoulder widths): source 1.427, avatar 1.42, difference 0.007.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.073 | 0.163 |
| wrist height error signed | -0.024 | 0.145 |
| wrist sideways error signed | -0.011 | 0.022 |
| wrist height vs nose error signed | -0.05 | 0.089 |
| elbow height error | 0.043 | 0.075 |
| handshape error | 0.265 | 0.653 |

Highest wrist point (y, shoulder widths): source -0.889, avatar -0.958, difference 0.069.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
