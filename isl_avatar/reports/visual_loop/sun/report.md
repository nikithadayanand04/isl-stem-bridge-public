# Visual loop check: sun

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: PASS

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| right wrist error median | 0.1 | ≤ 0.15 | pass |
| right wrist error p90 | 0.146 | ≤ 0.3 | pass |
| right elbow height error median | 0.065 | ≤ 0.2 | pass |
| right peak height error | 0.118 | ≤ 0.2 | pass |
| right handshape error median | 0.256 | ≤ 0.3 | pass |

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.1 | 0.146 |
| wrist height error signed | -0.084 | 0.141 |
| wrist sideways error signed | -0.009 | 0.031 |
| wrist height vs nose error signed | -0.068 | 0.093 |
| elbow height error | 0.065 | 0.085 |
| handshape error | 0.256 | 0.554 |

Highest wrist point (y, shoulder widths): source -1.079, avatar -1.196, difference 0.118.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
