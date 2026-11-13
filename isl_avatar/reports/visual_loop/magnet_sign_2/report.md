# Visual loop check: magnet_sign_2

The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is
centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).
Nothing here uses the retargeting's own scaling.

## Result: PASS

| Check | Value | Limit | Result |
| --- | --- | --- | --- |
| left wrist error median | 0.117 | ≤ 0.15 | pass |
| left wrist error p90 | 0.206 | ≤ 0.3 | pass |
| left elbow height error median | 0.037 | ≤ 0.2 | pass |
| left peak height error | 0.062 | ≤ 0.2 | pass |
| left handshape error median | 0.287 | ≤ 0.3 | pass |
| right wrist error median | 0.143 | ≤ 0.15 | pass |
| right wrist error p90 | 0.189 | ≤ 0.3 | pass |
| right elbow height error median | 0.016 | ≤ 0.2 | pass |
| right peak height error | 0.076 | ≤ 0.2 | pass |
| right handshape error median | 0.298 | ≤ 0.3 | pass |

## Left hand (signer's left)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.117 | 0.206 |
| wrist height error signed | 0.104 | 0.189 |
| wrist sideways error signed | -0.013 | 0.071 |
| wrist height vs nose error signed | 0.142 | 0.28 |
| elbow height error | 0.037 | 0.083 |
| handshape error | 0.287 | 0.4 |

Highest wrist point (y, shoulder widths): source 0.435, avatar 0.497, difference 0.062.

## Right hand (signer's right)

| Measure | Median | p90 |
| --- | --- | --- |
| wrist error | 0.143 | 0.189 |
| wrist height error signed | 0.097 | 0.139 |
| wrist sideways error signed | 0.087 | 0.15 |
| wrist height vs nose error signed | 0.141 | 0.193 |
| elbow height error | 0.016 | 0.031 |
| handshape error | 0.298 | 0.547 |

Highest wrist point (y, shoulder widths): source 0.426, avatar 0.502, difference 0.076.

Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).
