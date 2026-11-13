# Visual loop check: magnet

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.163 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.218 | ≤ 0.3 | pass |
| left elbow height error median | 0.04 | ≤ 0.2 | pass |
| left peak height error | 0.176 | ≤ 0.2 | pass |
| left handshape error median | 0.414 | ≤ 0.3 | FAIL |
| right wrist error median | 0.271 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.347 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.027 | ≤ 0.2 | pass |
| right peak height error | 0.195 | ≤ 0.2 | pass |
| right handshape error median | 0.198 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.163 | 0.218 |
| wrist height error signed | 0.158 | 0.211 |
| wrist sideways error signed | 0.009 | 0.057 |
| wrist height vs nose error signed | 0.185 | 0.229 |
| elbow height error | 0.04 | 0.097 |
| handshape error | 0.414 | 0.856 |

Highest wrist point (y, shoulder widths): source 0.015, avatar 0.191, difference 0.176.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.271 | 0.347 |
| wrist height error signed | 0.249 | 0.293 |
| wrist sideways error signed | 0.088 | 0.187 |
| wrist height vs nose error signed | 0.26 | 0.321 |
| elbow height error | 0.027 | 0.113 |
| handshape error | 0.198 | 0.498 |

Highest wrist point (y, shoulder widths): source -0.431, avatar -0.236, difference 0.195.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
