# Visual loop check: photosynthesis

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: FAIL

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.218 | ≤ 0.15 | FAIL |
| left wrist error p90 | 0.42 | ≤ 0.3 | FAIL |
| left elbow height error median | 0.065 | ≤ 0.2 | pass |
| left peak height error | 0.254 | ≤ 0.2 | FAIL |
| left handshape error median | 0.829 | ≤ 0.3 | FAIL |
| right wrist error median | 0.305 | ≤ 0.15 | FAIL |
| right wrist error p90 | 0.584 | ≤ 0.3 | FAIL |
| right elbow height error median | 0.085 | ≤ 0.2 | pass |
| right peak height error | 0.204 | ≤ 0.2 | FAIL |
| right handshape error median | 0.519 | ≤ 0.3 | FAIL |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.218 | 0.42 |
| wrist height error signed | 0.15 | 0.393 |
| wrist sideways error signed | 0.081 | 0.195 |
| wrist height vs nose error signed | 0.219 | 0.452 |
| elbow height error | 0.065 | 0.146 |
| handshape error | 0.829 | 2.544 |

Highest wrist point (y, shoulder widths): source -0.243, avatar 0.012, difference 0.254.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.305 | 0.584 |
| wrist height error signed | 0.263 | 0.461 |
| wrist sideways error signed | 0.062 | 0.28 |
| wrist height vs nose error signed | 0.347 | 0.517 |
| elbow height error | 0.085 | 0.214 |
| handshape error | 0.519 | 1.17 |

Highest wrist point (y, shoulder widths): source -0.711, avatar -0.507, difference 0.204.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
