# Audit, failure analysis, and acceptance plan

## Requirements traceability

| Requested capability | Implementation | Audit evidence / limitation |
|---|---|---|
| ESP32 soil moisture sensor | SEN0193 → divider/filter → GPIO34 | Schematic and ADC code; soil-specific bench calibration required |
| Full electronics schematic | Native KiCad module-level circuit and PDF | ERC and exported connectivity test; purchased modules retain manufacturer internals |
| Casing CAD | Parametric enclosure, lid, STEP assembly, STLs | Solid validity and base/lid collision check; print and actual component fits pending |
| Servo opens valve | 50 Hz PWM, AHCT buffer, external servo bracket | Firmware compile and state-machine tests; actual valve selection and linkage commissioning pending |
| Panel status LEDs | Green/amber/red outputs with current limiting | Schematic, firmware mapping, lid openings |
| Moisture history graph | Embedded canvas UI, 1,440 samples, CSV | Desktop/mobile browser checks with mocked data; device heap/load testing pending |
| Threshold notifications on same UI | Low/high crossings, fault/event list, status banner | Browser checks; no external notification service |
| Professional audit documentation | README, source links, calculations, test plan | Rev A handoff, not engineering certification |

## Failure review

| Failure / trigger | Detection and designed response | Residual risk / required action |
|---|---|---|
| Probe disconnected or output near ground | ADC divider pulls low; first bad sample inhibits opening and commands closure; three bad samples latch fault | Verify discharge/read latency; a plausible stuck value is not detected |
| Probe ADC too high | Above 2150 mV is rejected | Wrong wiring may damage GPIO before software acts; inspect wiring before power |
| Sensor drifts/sticks dry | No comprehensive detection; 5-second pulses, soak, conservative budget | Limited water can still be unwanted; use independent flow/volume controls for consequential installations |
| STOP cable open | Pullup reads high; close command, disarm, latched fault | GPIO/firmware failure or shorted loop can defeat it; no safety claim |
| Browser closes / Wi-Fi fails | Local automation continues; browser indicates stale connection when detectable | Operator must use physical STOP; notifications are unavailable while disconnected |
| Slow/malicious HTTP client | Control task runs separately; network writes are outside the mutex | FreeRTOS scheduling, heap exhaustion, and watchdog behavior require device stress tests |
| Servo jam or linkage detached | No direct feedback; command still reports CLOSED/OPEN | Valve may remain open indefinitely; add position/flow sensing or independent shutoff |
| Servo shorts | Input fuse and supply limiting may operate | Verify fuse/wire coordination; a normal-current stalled servo does not blow F1 |
| Power loss / brownout | PWM may stop; restart commands close and disarms | A mechanical valve may remain open during outage; software cannot guarantee closure |
| Controller task hangs | Approximately 3-second task watchdog requests reset | This is secondary recovery, not an independent hard deadline or fail-close mechanism |
| Configuration out of bounds | Rejected, no save or activation | Incorrect but in-range calibration is operator error; record actual endpoints |
| NVS write failure | Return error, flag storage failure, reject new watering commands | Commission storage; power-loss behavior during save must be tested |
| Restart bypasses RAM budget | Always disarmed after restart | A deliberate operator can re-arm and reset reservations; this is not a persistent water meter |
| Water/condensation reaches electronics | No moisture-in-enclosure detection | Rev A is unsealed; dry sheltered use, or redesign and test sealing |
| Incorrect polarity / simultaneous USB power | No reverse-polarity circuit; documented isolation procedure | Hardware damage possible; verify polarity and supply exclusivity |

## Hardware acceptance procedure

All items below are **pending physical tests**. Record measured values, test equipment, calibration dates, photographs, firmware hash, component versions, and pass/fail. Stop and revise the design if any criterion fails.

1. **Unpowered inspection:** verify all 19 named nets against the wiring; check polarity, resistor values, connector identities, insulation, and no power-to-ground short. Confirm the STOP uses a normally closed maintained contact.
2. **Power integrity:** start with a current-limited supply and no servo. Verify 3.3 V rail within the board's requirements. Add servo unloaded, then representative mechanical load. Scope +5V at J3 and +3V3 at U1 during repeated motion and Wi-Fi traffic. Accept only if servo supply remains ≥4.8 V, U2 remains within 4.5–5.5 V, and ESP32 stays stable. Measure inrush and fuse/connector temperatures.
3. **PWM:** scope GPIO18 and J3 signal. Verify 50 Hz, configured pulse endpoints, logic levels, and polarity. With a known valid calibration and dry stimulus, measure a normal pulse at approximately 5.00 s; initial acceptance ceiling 5.10 s under sustained UI traffic. A tighter application limit needs a tighter measured timing budget or hardware cutoff.
4. **Startup / reset:** power-cycle with wet and dry stimuli, and restart during an open pulse. Verify no automatic watering resumes without explicit arming. Characterize any uncontrolled motion before the first valid PWM. Repeat USB/external power transitions using the prescribed sequence.
5. **Interlock:** while opening, disconnect J4 or operate STOP. Closure command must change within 100 ms in normal operation. Verify the fault remains latched after restoring the loop and that reset leaves the controller disarmed. Observe physical closure time separately; command latency is not valve latency.
6. **Probe faults:** disconnect each probe lead and short output to ground using a controlled fixture. Verify watering is inhibited, a running command closes promptly, and persistent implausible values latch a fault. Never inject a voltage exceeding the ADC pin rating. Record which cable faults remain plausible and undetected.
7. **Threshold and soak:** apply controlled analog voltages through an appropriate test fixture or calibrated soil samples. Verify below-low starts demand, intermediate values maintain demand after a low crossing, and above-high clears demand. Verify no new pulse begins before 60 seconds after closure, including manual requests and early STOP closure.
8. **Budget:** request six full pulses separated by soak time; verify the seventh request faults. Verify no reset bypass before one hour since the last accepted pulse start. Verify reset plus re-arm after that interval. Reboot behavior must match documented RAM reset and disarming.
9. **Persistence:** save measured calibration, reboot, compare exact fields, and verify disarmed mode. Interrupt power during an NVS save under controlled dry conditions; accept only a valid old or new configuration, or an uncalibrated inhibited startup. Test a full/failed storage scenario where possible.
10. **Web stress:** authenticated polling, CSV download, multiple tabs, slow clients, malformed values (`NaN`, missing fields, infinities, oversized numbers), missing/wrong token, and unauthenticated requests. Confirm rejected commands have no watering effect. Track free heap through a 24-hour run and verify normal pulse bounds remain satisfied.
11. **History:** log for over 24 hours, verify 1,440-point ring order, invalid-sample gaps, calibration clearing, boot-ID changes, and CSV values. Compare raw ADC against a calibrated meter at five or more voltages and record errors rather than assuming ESP32 ADC accuracy.
12. **Mechanics:** verify gland and panel control fit, carrier-to-lid clearance, antenna clearance, wire strain relief, lid screw retention, and print dimensional tolerances. Cycle the servo mechanism at least 100 times at representative valve load. Inspect loosening, wear, and servo heating. This screening count is not a lifetime qualification.
13. **Hydraulics:** use a small gravity reservoir in a catch tray. Measure opening volume for a five-second command, closure leakage, valve torque, and actual closure time. Repeat at minimum/maximum intended head and supply voltage. Confirm the reservoir's total volume is acceptable if the valve sticks open.
14. **Power-loss consequence:** remove power while the valve is open and observe actual flow. Rev A does not claim automatic closure. An unattended release must either demonstrate independently enforced closure or accept and mitigate the complete reservoir-spill consequence in a signed risk assessment.
15. **Soil validation:** characterize dry/wet endpoints and at least three intermediate reference conditions, repeatability, packing/depth changes, temperature response, and drift. If reporting VWC, establish a traceable gravimetric/volumetric calibration rather than relabeling the relative index.

## Release record

| Field | Engineer entry |
|---|---|
| Reviewer / date / revision | Pending |
| Exact board, sensor, servo, valve and supply | Pending |
| Source/firmware SHA-256 | See generated manifest; record flashed binary separately |
| Valve torque, head/pressure, pulse volume, leakage | Pending |
| Calibration data and uncertainty | Pending |
| Electrical and thermal measurements | Pending |
| Mechanical/ingress qualification | Pending |
| Deviations, mitigations, approvals | Pending |
| Intended environment and permitted operating mode | Pending |

Before manufacturing a PCB or releasing unattended operation, review the missing independent shutoff, feedback, outdoor cable protection, persistent water accounting, enclosure sealing, service access, harness procurement, and regulatory requirements for the actual deployment. These are engineering gates tied to this design's known limitations.
