# Visual loop check: leaf

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.137 | ≤ 0.15 | pass |
| left wrist error p90 | 0.244 | ≤ 0.3 | pass |
| left elbow height error median | 0.042 | ≤ 0.2 | pass |
| left peak height error | 0.12 | ≤ 0.2 | pass |
| right wrist error median | 0.389 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.435 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.045 | ≤ 0.2 | pass |
| right peak height error | 0.337 | ≤ 0.2 | FAIL |
| right handshape error median | 0.278 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.137 | 0.244 |
| wrist height error signed | -0.095 | -0.073 |
| wrist sideways error signed | -0.056 | -0.032 |
| wrist height vs nose error signed | -0.17 | -0.103 |
| elbow height error | 0.042 | 0.091 |

Highest wrist point (y, shoulder widths): source 1.525, avatar 1.406, difference 0.12.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.389 | 0.435 |
| wrist height error signed | 0.349 | 0.403 |
| wrist sideways error signed | 0.146 | 0.197 |
| wrist height vs nose error signed | 0.326 | 0.391 |
| elbow height error | 0.045 | 0.122 |
| handshape error | 0.278 | 0.754 |

Highest wrist point (y, shoulder widths): source -0.14, avatar 0.197, difference 0.337.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
