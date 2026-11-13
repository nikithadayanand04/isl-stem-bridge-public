# Visual loop check: electricity

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.067 | ≤ 0.15 | pass |
| left wrist error p90 | 0.067 | ≤ 0.3 | pass |
| left elbow height error median | 0.018 | ≤ 0.2 | pass |
| left peak height error | 0.072 | ≤ 0.2 | pass |
| right wrist error median | 0.255 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.338 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.043 | ≤ 0.2 | pass |
| right peak height error | 0.169 | ≤ 0.2 | pass |
| right handshape error median | 0.288 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.067 | 0.067 |
| wrist height error signed | 0.035 | 0.035 |
| wrist sideways error signed | 0.026 | 0.026 |
| wrist height vs nose error signed | -0.0 | -0.0 |
| elbow height error | 0.018 | 0.042 |

Highest wrist point (y, shoulder widths): source 1.427, avatar 1.356, difference 0.072.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.255 | 0.338 |
| wrist height error signed | 0.248 | 0.337 |
| wrist sideways error signed | 0.041 | 0.082 |
| wrist height vs nose error signed | 0.188 | 0.304 |
| elbow height error | 0.043 | 0.165 |
| handshape error | 0.288 | 0.898 |

Highest wrist point (y, shoulder widths): source -0.889, avatar -0.72, difference 0.169.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
