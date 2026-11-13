# Visual loop check: soil

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.154 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.192 | ≤ 0.3 | pass |
| left elbow height error median | 0.016 | ≤ 0.2 | pass |
| left peak height error | 0.071 | ≤ 0.2 | pass |
| left handshape error median | 0.907 | ≤ 0.3 | FAIL |
| right wrist error median | 0.113 | ≤ 0.15 | pass |
| right wrist error p90 | 0.199 | ≤ 0.3 | pass |
| right elbow height error median | 0.038 | ≤ 0.2 | pass |
| right peak height error | 0.079 | ≤ 0.2 | pass |
| right handshape error median | 0.361 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.154 | 0.192 |
| wrist height error signed | 0.153 | 0.182 |
| wrist sideways error signed | 0.02 | 0.101 |
| wrist height vs nose error signed | 0.14 | 0.206 |
| elbow height error | 0.016 | 0.087 |
| handshape error | 0.907 | 3.105 |

Highest wrist point (y, shoulder widths): source -0.038, avatar 0.033, difference 0.071.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.113 | 0.199 |
| wrist height error signed | 0.099 | 0.18 |
| wrist sideways error signed | -0.006 | 0.115 |
| wrist height vs nose error signed | 0.084 | 0.218 |
| elbow height error | 0.038 | 0.115 |
| handshape error | 0.361 | 2.279 |

Highest wrist point (y, shoulder widths): source -0.159, avatar -0.08, difference 0.079.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
