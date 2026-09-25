# ESP32 soil moisture and servo valve — Rev A

An engineer-reviewable, low-voltage irrigation prototype: a capacitive soil probe, ESP32 controller, servo-operated valve interface, three panel LEDs, printable enclosure, and a local web dashboard with moisture history and threshold notifications.

**Release status:** design prototype. Electronic connectivity, CAD geometry, firmware compilation, and software behavior can be checked without hardware. Valve torque, actual closure, water flow, electrical transients, moisture calibration, and printed-part fit require the acceptance tests below. This package is not a validated unattended watering product.

## Start here

| Deliverable | File |
|---|---|
| Electronic schematic, readable without KiCad | [Schematic PDF](electronics/soil_valve.pdf) |
| Editable schematic and project | [KiCad project](electronics/soil_valve.kicad_pro), [schematic](electronics/soil_valve.kicad_sch) |
| Component list and exact connectivity | [BOM](electronics/bom.csv), [net map](electronics/connectivity.json), [KiCad-exported netlist](electronics/soil_valve.net.xml) |
| Editable parametric CAD | [CadQuery model](mechanical/enclosure.py) |
| Assembled enclosure CAD | [STEP assembly](mechanical/exports/enclosure_assembly.step) |
| Individual STEP and print-ready STL files | [CAD exports](mechanical/exports/) |
| ESP32 application and control logic | [main.cpp](firmware/src/main.cpp), [control.h](firmware/include/control.h) |
| Dashboard | [Interactive offline demo](docs/dashboard-demo.html), [HTML source](firmware/web/index.html), [demo screenshot](docs/dashboard-demo.png) |
| Engineering rationale, wiring and procurement | [Electrical design](docs/electrical-design.md) |
| Mechanical dimensions and assembly | [Mechanical design](docs/mechanical-design.md) |
| Failure analysis and bench sign-off | [Audit and acceptance plan](docs/audit-and-acceptance.md) |
| Automated verification evidence | [Verification report](docs/verification.md) |
| Manufacturer references | [Sources](docs/sources.md) |

To preview the dashboard without a device, open `docs/dashboard-demo.html` in a browser. Alternatively, open `firmware/web/index.html` and append `?demo=1` to its address. The demo explicitly labels its simulated data and disables hardware controls. The dashboard needs no CDN, JavaScript framework, cloud service, or internet connection.

## Design assumptions

- One indoor/sheltered plant zone, externally supplied regulated **5.0 V / 3 A** power.
- Genuine **Espressif ESP32-DevKitC V4 with ESP32-WROOM-32E**, using the documented 38-pin headers. Other ESP32 boards need pin and power-path review.
- **DFRobot SEN0193** capacitive probe supplied at 3.3 V; only its sensing section enters soil. Do not immerse its electronics.
- **Hitec HS-311** positional servo, externally mounted above the water path. A small low-pressure valve must have measured torque and compatible linkage travel. The servo bracket and slotted linkage plate are supplied, but the valve-specific attachment dimensions are not known.
- A gravity reservoir is the intended first test source; use a spill tray and limit available water. No pressure-bearing printed plumbing parts are supplied.
- Measurement is **relative moisture percent**, not volumetric water content (VWC). Actual VWC requires soil-specific reference measurements and a different calibration model.

No valve, supply, or existing parts were specified. These assumptions make the design concrete; substitutions and the actual valve are audit inputs rather than proven equivalents.

## Operation

At power-on the firmware commands the servo to its configured closed position, leaves automatic watering disarmed, starts measurements, and creates a password-protected Wi-Fi access point. Calibration survives restart; arming, faults, watering reservations, graph history, and events do not. The boot event makes this reset visible.

The probe is sampled at 4 Hz, averaging 16 calibrated ADC millivolt readings per sample and applying an exponential filter with coefficient 0.25. Five consecutive plausible samples establish readiness. The initial example calibration is **not authorized for watering** until you save measured endpoints.

After arming, moisture below the low threshold sets watering demand. Demand remains set through the middle band and clears at the high threshold. Defaults are 30% and 55%; these are example settings, not crop recommendations. Each opening command lasts nominally 5 seconds, followed by at least 60 seconds closed for soaking. The 20 ms control task imposes small scheduling tolerance; verify actual pulse duration on hardware.

Each pulse reserves its full five seconds in a 30-second budget, even when stopped early. Reservations clear only after one complete hour with **no new pulse starts**, a conservative rule that avoids bursts at fixed clock boundaries. A seventh requested pulse latches a budget fault. After the quiet hour, reset the fault and explicitly re-arm. Manual pulses share the same calibration, fault, soak, and budget restrictions and require automatic mode to be disarmed.

Opening the normally closed STOP loop commands closure, disarms, and latches a fault. Three implausible sensor samples latch a sensor fault; even the first implausible sample inhibits or terminates watering. Stale samples also latch a fault. Fault reset does not re-arm. Loss of a browser connection does not stop armed automation; the physical STOP remains the local control.

**A servo command does not establish actual valve position.** There is no flow sensor or valve feedback. A stalled servo, broken linkage, controller failure, or loss of power can leave the valve open. STOP is a firmware interlock, not a hardwired safety function. Where flooding matters, the engineering release must add independently verified fail-closed actuation or a separate normally closed shutoff.

## Wiring summary

Use the schematic and [electrical design notes](docs/electrical-design.md) as the wiring authority. Local net labels of the same name are electrically connected. `U1.J2` and `U1.J3` refer to the development board's own headers; standalone `J2` and `J3` are project probe and servo connectors.

| Function | ESP32 GPIO | DevKit header |
|---|---:|---|
| Probe divider output | 34, ADC1 | J2 pin 5 |
| Servo PWM, through 5 V buffer | 18 | J3 pin 9 |
| Green LED | 25 | J2 pin 9 |
| Amber LED | 26 | J2 pin 10 |
| Red LED | 32 | J2 pin 7 |
| Normally closed STOP loop input | 27 | J2 pin 11 |
| 3.3 V probe supply | — | J2 pin 1 |
| 5 V board power through RUN link | — | J2 pin 19 |
| Common ground | — | J2 pin 14; J3 pins 1, 7 |

Green flashes while disarmed and is steady while armed. Amber means **OPEN commanded**. Red indicates a latched fault, missing calibration, or configuration-save failure. Green is a firmware heartbeat/mode indicator, not proof of network access or sensor accuracy.

Connect the servo supply and return directly to the fused supply distribution point. Do not feed servo current through the ESP32 board, its regulator, USB cable, or a solderless breadboard. Inspect connector polarity before energizing; the input is fused but has no reverse-polarity protection.

## Build and flash

The build is pinned to PlatformIO `espressif32@6.9.0`, which selects Arduino-ESP32 2.0.17. The firmware uses that version's LEDC API; upgrading to Arduino 3.x requires migration and retesting. Python 3.12 was used for tooling.

```powershell
python -m pip install platformio==6.2.0
Copy-Item firmware/include/secrets.example.h firmware/include/secrets.h
# Edit secrets.h: two different, unique passwords of at least 12 characters.
python -m platformio run -d firmware
```

This workspace contains a generated, ignored `firmware/include/secrets.h` with random credentials for the verified local build. Read that file locally to obtain them, or replace them and rebuild. The template must remain free of actual credentials. The firmware refuses to start networking with short or placeholder passwords.

On Windows, if the compiler reports a process-launch error from a long project path, run `powershell -ExecutionPolicy Bypass -File tools/build_firmware.ps1`. This temporarily maps the workspace to a short drive path and removes that mapping on completion. Add `-Upload -Port COM5` to build and flash through the same workaround. The portable ZIP excludes the local credentials, so create `secrets.h` from the template after extracting it elsewhere.

Before connecting the board's USB port: turn **SW1 OFF**, remove **JP1**, and disconnect the servo during initial commissioning. Espressif specifies mutually exclusive supply methods; never power the DevKit from its 5 V header and USB simultaneously. The lid is removed for USB access.

```powershell
python -m platformio run -d firmware -t upload --upload-port COM5
python -m platformio device monitor -d firmware --port COM5
```

Replace `COM5` with the actual port. Close the serial monitor before another upload. The dashboard is embedded in flash by `embed_ui.py`; a separate filesystem upload is unnecessary. After programming, disconnect USB before replacing JP1 and switching on external power.

Join `SoilValve-<device identifier>`, use `AP_PASSWORD`, then open `http://192.168.4.1`. Authenticate as `admin` with `ADMIN_PASSWORD`. A phone may need to remain connected to a network with no internet access. There is no captive portal.

## Commissioning and calibration

1. Keep water disconnected and the servo horn detached. Verify power polarity, fuse, common ground, and the ADC divider with a meter. Check the STOP input changes state when its loop opens.
2. Power the system; confirm disarmed status, red calibration indication, and a closed-position PWM signal. Verify the servo supply stays at or above 4.8 V while the servo moves.
3. Adjust `CLOSED_US` and `OPEN_US` in `main.cpp` for the actual mechanism. Defaults are 1050 and 1950 microseconds at 50 Hz, within the HS-311's documented nominal 900–2100 microsecond range. Rebuild if changed. Never force the servo against a hard stop.
4. Measure ADC millivolts in representative dry soil at the intended insertion depth and packing. Allow readings to stabilize. Repeat in representative wet soil. Record soil type, temperature, preparation, supply voltage, depth, and each endpoint's variation.
5. Save both endpoints and thresholds. Required range: `100 <= wet < dry <= 2150 mV`, dry–wet separation at least 200 mV, thresholds between 5 and 95%, with at least five percentage points of separation. Reverse response or insufficient span needs investigation, not inverted wiring guesses.
6. Confirm the same samples map to approximately 0 and 100%, and use intermediate gravimetric samples if assessing accuracy. Display clamping to 0–100% does not imply physical accuracy. Tune thresholds for the actual soil and plant under observation.
7. Attach the horn and linkage only after verifying the close direction. Test travel without water, including STOP, reset, and power interruption. Measure valve torque throughout travel.
8. Use a small reservoir and catch vessel. After the initial 60-second inhibit, issue a manual pulse; measure volume, closing leakage, and time to wet the probe. Complete [the acceptance plan](docs/audit-and-acceptance.md) before arming automatic mode.

The readout uses `100 × (dry_mV − measured_mV) / (dry_mV − wet_mV)`, clamped to 0–100. Calibration is specific to this probe, divider, board, soil, and installation. Values from a tutorial or a different probe must not be reused as measured endpoints.

## Dashboard and data contract

The chart retains 1,440 one-minute samples in ESP32 RAM (up to 24 hours). Timestamps are elapsed seconds since boot, not wall-clock time; there is no RTC or NTP. Invalid samples are JSON `null` and produce gaps. CSV export downloads the current history, including ADC millivolts and valve command state. Short pulses can fall between history samples, so the event log is the appropriate record of valve command transitions.

The latest 32 events contain low/high threshold crossings, commands, faults, and mode changes. These in-page notifications are retained on the controller even if the browser is closed, until overwritten or rebooted. They are not email, phone push notifications, or a durable audit log. Recalibration clears graph history and leaves the controller disarmed.

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Embedded dashboard |
| `/api/status` | GET | Current status, calibration, events, boot ID, control token |
| `/api/history` | GET | Chronological sample array |
| `/api/config` | POST | URL-encoded `dryMv`, `wetMv`, `low`, `high`; saves validated calibration |
| `/api/command` | POST | URL-encoded `action=arm`, `pulse`, `close`, or `reset` |

All useful routes require HTTP Basic authentication. Mutations also require the per-boot `X-Control-Token` obtained from authenticated status. The access point is password protected, but HTTP is not TLS. Use only a trusted local connection; this design has no internet exposure, remote update service, or remote credential provisioning. Protect the device and source secrets physically. A reboot produces a new boot identifier and token.

## Reproduce the design checks

```powershell
python -m pip install -r tools/requirements.txt
python tools/generate_schematic.py
kicad-cli sch erc -o electronics/erc.rpt electronics/soil_valve.kicad_sch
kicad-cli sch export pdf -o electronics/soil_valve.pdf electronics/soil_valve.kicad_sch
kicad-cli sch export netlist --format kicadxml -o electronics/soil_valve.net.xml electronics/soil_valve.kicad_sch
python tests/check_netlist.py
python mechanical/enclosure.py
g++ -std=c++17 tests/control_test.cpp -o tests/control_test.exe
./tests/control_test.exe
python tests/browser_test.py
python -m platformio run -d firmware
```

`kicad-cli` must be on PATH, or use its installed absolute path. Browser tests currently point to the Windows Chrome installation; change `executable_path` in the test for another installation. Any C++17 compiler can run the host control tests; the local verification used Zig's C++ frontend. The CAD source is authoritative for geometry; generated files may be overwritten. Schematic regeneration assigns new UUIDs, so review regenerated schematic diffs with the netlist.

## Engineering handoff

The schematic specifies a wired module/perfboard assembly, including all external passives and panel wiring. The purchased DevKit, sensor, and servo contain their own manufacturer circuitry. A routed carrier PCB, Gerbers, production harness drawing, waterproof certification, and a valve-specific adapter are not part of Rev A. The carrier CAD is a mechanical drill template, not a PCB layout.

An engineer should review the source references, electrical calculations, pin mapping, firmware state machine, mechanical stack-up, and failure table; then record the actual parts and execute the hardware acceptance plan. Do not interpret a clean ERC, successful compilation, or valid CAD solid as proof of physical operation.
