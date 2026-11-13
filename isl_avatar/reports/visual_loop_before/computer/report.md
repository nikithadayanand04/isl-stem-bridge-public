# Visual loop check: computer

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.189 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.267 | ≤ 0.3 | pass |
| left elbow height error median | 0.057 | ≤ 0.2 | pass |
| left peak height error | 0.208 | ≤ 0.2 | FAIL |
| left handshape error median | 0.37 | ≤ 0.3 | FAIL |
| right wrist error median | 0.211 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.299 | ≤ 0.3 | pass |
| right elbow height error median | 0.123 | ≤ 0.2 | pass |
| right peak height error | 0.298 | ≤ 0.2 | FAIL |
| right handshape error median | 0.392 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.189 | 0.267 |
| wrist height error signed | 0.17 | 0.243 |
| wrist sideways error signed | 0.086 | 0.147 |
| wrist height vs nose error signed | 0.123 | 0.214 |
| elbow height error | 0.057 | 0.11 |
| handshape error | 0.37 | 1.341 |

Highest wrist point (y, shoulder widths): source -0.152, avatar 0.056, difference 0.208.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.211 | 0.299 |
| wrist height error signed | 0.195 | 0.277 |
| wrist sideways error signed | -0.07 | 0.1 |
| wrist height vs nose error signed | 0.145 | 0.286 |
| elbow height error | 0.123 | 0.158 |
| handshape error | 0.392 | 1.211 |

Highest wrist point (y, shoulder widths): source -0.088, avatar 0.21, difference 0.298.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
