# Visual loop check: water

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.065 | ≤ 0.15 | pass |
| left wrist error p90 | 0.065 | ≤ 0.3 | pass |
| left elbow height error median | 0.016 | ≤ 0.2 | pass |
| left peak height error | 0.001 | ≤ 0.2 | pass |
| right wrist error median | 0.383 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.445 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.112 | ≤ 0.2 | pass |
| right peak height error | 0.408 | ≤ 0.2 | FAIL |
| right handshape error median | 0.243 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.065 | 0.065 |
| wrist height error signed | 0.031 | 0.031 |
| wrist sideways error signed | -0.057 | -0.057 |
| wrist height vs nose error signed | -0.026 | -0.026 |
| elbow height error | 0.016 | 0.038 |

Highest wrist point (y, shoulder widths): source 1.411, avatar 1.412, difference 0.001.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.383 | 0.445 |
| wrist height error signed | 0.382 | 0.444 |
| wrist sideways error signed | -0.013 | 0.033 |
| wrist height vs nose error signed | 0.39 | 0.473 |
| elbow height error | 0.112 | 0.2 |
| handshape error | 0.243 | 0.647 |

Highest wrist point (y, shoulder widths): source -0.665, avatar -0.257, difference 0.408.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
