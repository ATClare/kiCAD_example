# Mechanical design and assembly

## Model authority and coordinate system

`mechanical/enclosure.py` is the editable CadQuery source, with dimensions in millimetres. STEP files contain exact boundary-representation solids; STL files are tessellated printing derivatives. A positive solid-volume and validity report is exported with each generation. The assembled STEP contains the base, lid, and a carrier reference plate. The external servo bracket and linkage plate are separate parts.

For the enclosure, X is the long direction, Y the short direction, and Z points out of the base. The enclosure is centred at X=Y=0; its external floor is Z=0. The front cable-entry wall is Y=−50. Installed lid surfaces are Z=55 to 58; its locating rails extend down to Z=52.

## Critical dimensions

| Feature | Geometry / coordinates |
|---|---|
| Base external size | 140 × 100 × 55 |
| Walls / floor | 3 / 3 |
| Base internal nominal space | 134 × 94 × 52, before posts and rails |
| External vertical corner radius | 4 |
| Lid plate | 140 × 100 × 3 |
| Lid locating rails | 2 thick, 3 deep; interrupted around screw posts |
| Rail-to-wall nominal clearance | 0.3 per side |
| Lid fastener centres | (±61, ±41) |
| Base corner posts | Ø10; Ø2.5 pilot, depth 16 from top |
| Lid through / counterbore | Ø3.4 through; Ø6.4 × 1.5 deep |
| Carrier board outline | 100 × 60 × 1.6 |
| Carrier mounting centres | (±45, ±25) |
| Carrier support top | Z=11; pilot Ø2.5 |
| Cable gland holes | Ø12.2; X=−38, 0, 38; Y=−50; Z=24 |
| LED holder holes | Ø6.5; X=−18, 0, 18; Y=20 |
| STOP panel hole | Ø22.2; X=35; Y=−15 |
| Power switch hole | Ø12.2; X=−35; Y=−15 |

The CAD carrier is a drilling and fit reference. Fabricate the real carrier from suitable electrically insulating material or use perfboard trimmed and drilled to these dimensions. Do not interpret the STL carrier as a designed electrical PCB. Secure the DevKit in sockets on the carrier and mount the discrete interface components nearby. Keep the RF antenna end free of copper and metal per the module guidance. Reserve space above the carrier for wiring and panel control bodies.

The CAD validates base/lid interference only; exact purchased board, terminal, gland-nut, switch, and cable envelopes are not modelled. Select a STOP assembly with total intrusion below the lid of at most 30 mm. Even then, check it against component height on the carrier. Keep tall electronics away from the two control centres and route wiring clear of screw posts. The right and left gland centres are offset from carrier mounting posts, but gland locknuts and lead bend radii still require inspection.

## Printing

Initial settings: PETG, 0.2 mm layers, four perimeters, at least five top/bottom layers, and 30–40% infill. These are starting fabrication parameters requiring qualification on the actual printer. Avoid assuming a PLA part will maintain stiffness in sun or a warm enclosure.

STLs are translated onto Z=0. The base prints open side upward. The lid STL is inverted, placing its outer face on the bed and its locating rails upward; preserve the visible labels when choosing a build surface. The servo bracket is translated onto its feet and needs support beneath its elevated cross plate. Print a hole/clearance coupon before committing to all parts. Ream or drill holes to nominal size as needed, and tap M3 pilots carefully; repeated service may justify redesigning for threaded inserts.

The source does not include a gasket groove. The lid, LED holes, control bushings, and printed layer structure are not sealed or IP-rated. A gasket, selected sealed panel components, and validated glands would require a revised stack-up and ingress testing. Keep Rev A sheltered and dry, with cable drip loops.

## Enclosure assembly

1. Deburr the parts and confirm the lid rails seat without force. Do not use the screws to pull a warped lid flat.
2. Fit the three M12 glands from the front. Place their locknuts inside and ensure they do not touch the carrier or crush wires.
3. Install the power toggle and latching NC STOP control. Fit green, amber, and red LEDs under READY, WATER, and FAULT, using the specified panel holders.
4. Mount the 100 × 60 carrier on the four internal posts with M3 × 8 screws. The board bottom is at Z=11. Prevent solder-side protrusions from contacting conductive hardware.
5. Install the ESP32 and interface circuitry. Retain slack for lid removal, strain-relieve panel harnesses, and mark the RUN jumper. Verify the lid closes without pushing any component or lead.
6. Fit the lid with M3 × 16 screws. The counterbore is sized for a pan head no larger than Ø6.4; different heads require a model change. Limit torque according to the printed-thread qualification, not a generic steel-thread torque.

USB access is through the removed lid. This deliberately keeps the outside face simple and permits direct verification that SW1 is off and JP1 removed before connecting a computer.

## Servo bracket and linkage

The external bracket has a 76 × 44 × 4 top plate, a 40.8 × 20.8 servo-body aperture, and adjustable 7 × 3.4 flange slots centred at X=±24.5, Y=±5. The bracket feet enlarge the overall envelope to 96 × 44 × 44. Four 9 × 4.5 mounting slots at X=±43, Y=±13 attach it to a rigid base. The HS-311 published body envelope is 40 × 20 × 36.5; mounting flange and cable clearances must be checked on the purchased part before printing. The slot range is an allowance, not a verified fit report.

Use the manufacturer's 24-tooth horn. The generic 55 × 12 × 4 linkage plate contains an Ø3.2 hole at X=−18 and a 25 × 3.4 slot centred at X=8. Drill/fasten an appropriate horn attachment on the actual mechanism; do not depend on one screw's friction alone to transfer valve torque. The model intentionally does not invent a printed servo spline or a valve-shaft interface.

Mount the valve and servo on a common rigid plate so that reaction loads are not carried by soft tubing. Arrange linkage axes to avoid over-centre binding. A nominal 90-degree servo motion is only a starting point; adjust pulse endpoints and linkage geometry to reach both valve positions without servo stall. Keep servo electronics and connectors dry; the servo is not treated as a waterproof actuator.

Published servo stall torque at 4.8 V is approximately 3 kgf·cm = 0.294 N·m, but stall torque is not a continuous operating rating. As a conservative initial selection criterion, choose a valve whose measured worst-case breakaway/running torque is no more than **0.05 N·m** at the servo shaft after linkage ratios and losses. This also lies below the published peak-efficiency torque (~0.059 N·m at 4.8 V). Verify under the intended pressure, temperature, deposits, and hose loading. A larger valve may require a different servo, bracket, power supply, and fuse.

The current design does not guarantee closure without electrical power. An added spring alone may not back-drive a geared hobby servo; a fail-closed redesign must prove the entire power-loss behavior, not simply add a spring to the drawing.
