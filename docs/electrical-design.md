# Electrical design and build notes

## Architecture and interfaces

The native KiCad schematic is one A3 sheet divided into power, probe interface, servo interface, full DevKit header mapping, panel LEDs, and STOP input. The project includes its own symbol library and library tables; open the `.kicad_pro` for correct library resolution. The custom module symbol numbers its pins `J2.1` through `J3.19` to preserve Espressif's physical header identities. Unused module header pins have explicit no-connect markers. No GPIO boot-strapping pins are used by the application.

The schematic describes a complete external circuit around purchased modules. Espressif's original DevKit schematic remains the authority for its regulator, USB bridge, boot circuit, and RF module. The project does not reproduce proprietary probe or servo internals.

## Supply path

J1 pin 1 → F1 2 A fuse → SW1 → `+5V`. This rail powers J3 servo pin 2 and U2 pin 5. JP1 connects this rail to `MCU_5V` and U1.J2.19. J1 pin 2 is the star ground. Connect U1's exposed ground header pins to that ground; keep the servo's return conductor separate until the star point.

Specify an enclosed regulated 5.0 V, 3 A supply with a low-voltage isolated output. Operate electronics in a sheltered dry location. There is no battery charger, mains circuitry, surge-rated outdoor interface, or reverse-polarity protection. Use a keyed supply connector and verify polarity. F1 protects wiring against sustained excessive current; it does not detect a stalled servo at its normal stall current.

Allow approximately 0.8 A servo stall current, 0.5 A as a conservative ESP32 board transient allocation, and 0.05 A auxiliary allocation: 1.35 A design load. This is a budget, not measured consumption. The 3 A supply provides margin but does not remove the need to measure droop and inrush. Target 4.8–5.2 V at the servo and U2 during operation; AHCT buffer recommended supply range is 4.5–5.5 V, while the servo minimum is 4.8 V.

Use short 22 AWG or larger power distribution conductors, appropriately rated connectors, and insulated solder joints. C1 is a polarized 1000 µF, ≥10 V electrolytic close to J3, positive at pin 1. At 0.8 A for 1 ms, an ideal 1000 µF capacitor alone would droop 0.8 V (`I × dt / C`), so it cannot substitute for an adequate supply. C2 provides local MCU input bulk; C5 is within 5 mm of U2 supply pins. Test fuse survival on repeated cold starts and check capacitor polarity before power-up.

## Sensor conditioning

J2 project harness: pin 1 = 3V3, pin 2 = GND, pin 3 = PROBE_OUT. Build an adapter to the purchased sensor's connector; do not assume that project pin numbering equals DFRobot's plug order or clone cable colors.

R1 = 10 kΩ and R2 = 20 kΩ, both 1%, divide the probe output to GPIO34/ADC1. Nominal division is 2/3. A 3.0 V sensor output becomes 2.0 V; a supply-limited 3.3 V becomes 2.2 V. With 1% worst-case divider tolerance, the ratio is approximately 0.662–0.671. ADC1 avoids the original ESP32 ADC2/Wi-Fi resource conflict. Firmware uses `analogReadMilliVolts()` and 11 dB attenuation.

The divider presents a 30 kΩ load to the probe. Validate output behavior under that load; no output-drive accuracy is assumed. The Thevenin resistance is 6.67 kΩ and C3 = 100 nF gives a nominal 0.667 ms time constant (~239 Hz cutoff). Software filtering handles slower noise. Route PROBE_OUT and GND together, separate them from servo leads, and keep the analog node physically short. This is a short-cable indoor interface, without certified ESD/lightning protection.

The divider pulls ADC voltage to ground after sensor disconnection. Firmware treats values below 100 mV or above 2150 mV as implausible. Values inside that window can still be wrong: a stuck sensor, ground offset, or partially shorted cable cannot always be detected from one analog channel. Calibration and the bounded watering policy reduce consequences but do not provide fault coverage for all sensor failures.

Never connect 5 V directly to the ADC. The divider is dimensioned for the specified 3.3 V-powered probe; it is not a general-purpose protected industrial analog input.

## Servo signal

GPIO18 → U2 pin 2 (A), with R3 = 100 kΩ to GND. U2 pin 1 (/OE) and pin 3 go to ground; pin 5 goes to +5V. U2 pin 4 (Y) → R4 = 220 Ω → J3 pin 3. The AHCT input recognizes 3.3 V logic while providing a 5 V servo signal. Use **SN74AHCT1G125DBVR**, not HC logic with a higher input threshold. Verify the SOT-23-5 breakout's numbering against the TI package drawing.

J3 is 1 GND, 2 +5V, 3 signal. Match the actual servo lead polarity before connecting. Firmware produces 50 Hz pulses, nominally 1050 µs closed and 1950 µs open. These are commissioning settings, not established valve angles. The external 100 kΩ pulldown suppresses floating input during reset but does not generate a closed-position servo pulse before firmware starts. Servo movement may occur during power sequencing; characterize it with the horn unloaded.

## LEDs and STOP

GPIO25/26/32 each drive a 680 Ω resistor followed by an LED anode; all cathodes return to ground. For a 2.0 V LED forward drop, nominal current is `(3.3 − 2.0) / 680 = 1.9 mA`. Select high-efficiency diffused LEDs visible at this current. White/blue substitutions may be dim due to higher forward voltage. The schematic labels LED pins A=2, K=1; match polarity by datasheet and flat/short lead, not a harness assumption.

J4 connects an external maintained normally closed STOP contact between STOP_SW and GND. R8 = 1 kΩ connects the loop to GPIO27; R9 = 10 kΩ pulls GPIO27 to 3.3 V; C6 = 100 nF filters interference. The firmware additionally enables its internal pullup. A healthy closed loop produces a logic low; opening the loop or disconnecting its cable produces a high. A short across the loop cannot be detected. Contact bounce may latch a conservative fault; release STOP and explicitly reset it.

This input is polled by the controller and has no independent hardware authority over power or valve closure. Mark it as STOP/interlock rather than claiming a safety-rated emergency-stop function.

## Procurement supplement

The electrical CSV contains references, values, descriptions, and the buffer footprint. Most components are intentionally through-hole or wired modules, with no PCB footprint assignment. This table supplies parts not fully described by a reference value.

| Item | Quantity | Procurement specification / acceptance |
|---|---:|---|
| U1 | 1 | Espressif ESP32-DevKitC V4, ESP32-WROOM-32E, 38-pin board |
| Probe | 1 | DFRobot SEN0193 with mating cable; verify supply and output |
| Servo | 1 | Hitec HS-311 with original 24T horn and mounting screws |
| U2 and adapter | 1 each | TI SN74AHCT1G125DBVR, SOT-23-5 breakout with short decoupling path |
| PSU | 1 | Regulated 5.0 V/3 A isolated enclosed supply, keyed low-voltage connector |
| F1 and holder | 1 each | 2 A fast fuse rated ≥32 VDC; validate inrush and wire coordination |
| SW1 | 1 | SPST maintained toggle, ≥3 A at ≥12 VDC; 12 mm panel bushing |
| STOP contact | 1 | Maintained/latching NC pushbutton, 22 mm panel hole; body depth ≤30 mm |
| JP1 | 1 | Two-pin removable shunt/header rated ≥1 A; label RUN/USB |
| J1–J4 harnesses | 4 | Keyed insulated connectors; J1/J3 rated ≥3 A; clearly label polarity |
| D1/D2/D3 | 1 each | Green/amber/red, 5 mm diffused high-efficiency LED, 6.5 mm-hole holders |
| Resistors | 9 | R1/R2 1%; all ≥0.125 W; values from schematic |
| Capacitors | 6 | C1 electrolytic 1000 µF/10 V; C2 10 µF/10 V ceramic; others 100 nF/≥10 V X7R |
| Carrier | 1 | 100 × 60 mm insulated/perfboard carrier with holes at ±45, ±25 mm |
| Cable glands | 3 | M12 gland bodies, hole requirement 12.2 mm, cable range suited to each lead |
| Enclosure screws | 4 | M3 × 16 pan head, head diameter ≤6.4 mm; tap or qualify printed pilot holes |
| Carrier screws | 4 | M3 × 8, insulating washers as needed |
| Valve and hoses | 1 set | Low-pressure, approximately quarter-turn valve; measured travel/torque required |
| Servo bracket hardware | 1 set | M3 servo fasteners and M4 base fasteners, washers, nuts, spacers as measured |

Part choices with dimensional envelopes are procurement requirements, not universal compatibility claims. Record exact manufacturers and lot numbers in the acceptance sheet before building.
