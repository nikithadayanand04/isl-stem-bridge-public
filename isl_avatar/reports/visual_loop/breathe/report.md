# Visual loop check: breathe

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: PASS

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.084 | ≤ 0.15 | pass |
| left wrist error p90 | 0.122 | ≤ 0.3 | pass |
| left elbow height error median | 0.021 | ≤ 0.2 | pass |
| left peak height error | 0.006 | ≤ 0.2 | pass |
| right wrist error median | 0.082 | ≤ 0.15 | pass |
| right wrist error p90 | 0.121 | ≤ 0.3 | pass |
| right elbow height error median | 0.015 | ≤ 0.2 | pass |
| right peak height error | 0.039 | ≤ 0.2 | pass |
| right handshape error median | 0.165 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.084 | 0.122 |
| wrist height error signed | -0.026 | 0.078 |
| wrist sideways error signed | 0.027 | 0.119 |
| wrist height vs nose error signed | -0.045 | 0.029 |
| elbow height error | 0.021 | 0.049 |

Highest wrist point (y, shoulder widths): source 1.432, avatar 1.438, difference 0.006.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.082 | 0.121 |
| wrist height error signed | 0.072 | 0.094 |
| wrist sideways error signed | -0.033 | -0.004 |
| wrist height vs nose error signed | 0.053 | 0.098 |
| elbow height error | 0.015 | 0.05 |
| handshape error | 0.165 | 0.322 |

Highest wrist point (y, shoulder widths): source -0.197, avatar -0.158, difference 0.039.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
