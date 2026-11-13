# Visual loop check: make

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.172 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.214 | ≤ 0.3 | pass |
| left elbow height error median | 0.041 | ≤ 0.2 | pass |
| left peak height error | 0.172 | ≤ 0.2 | pass |
| left handshape error median | 0.681 | ≤ 0.3 | FAIL |
| right wrist error median | 0.278 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.358 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.022 | ≤ 0.2 | pass |
| right peak height error | 0.315 | ≤ 0.2 | FAIL |
| right handshape error median | 0.282 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.172 | 0.214 |
| wrist height error signed | 0.157 | 0.206 |
| wrist sideways error signed | -0.001 | 0.084 |
| wrist height vs nose error signed | 0.114 | 0.188 |
| elbow height error | 0.041 | 0.133 |
| handshape error | 0.681 | 1.569 |

Highest wrist point (y, shoulder widths): source 0.542, avatar 0.713, difference 0.172.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.278 | 0.358 |
| wrist height error signed | 0.262 | 0.355 |
| wrist sideways error signed | -0.062 | 0.033 |
| wrist height vs nose error signed | 0.227 | 0.311 |
| elbow height error | 0.022 | 0.054 |
| handshape error | 0.282 | 0.53 |

Highest wrist point (y, shoulder widths): source 0.281, avatar 0.596, difference 0.315.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
