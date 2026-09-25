# Rev A verification record

Date: 2026-09-25. These results concern generated files and software tests. No physical circuit, valve, probe, printed case, or water supply was connected during this work.

| Check | Result | Evidence |
|---|---|---|
| Native KiCad load and PDF/SVG export | Passed | `electronics/soil_valve.pdf`, `electronics/rendered/soil_valve.svg` |
| KiCad electrical rule check | **0 errors, 0 warnings** | [ERC report](../electronics/erc.rpt) |
| Exported connectivity | All 19 intended named nets matched | `tests/check_netlist.py`, XML netlist; 27 external schematic components |
| CAD solids | Five valid, single-solid parts | [Geometry report](../mechanical/exports/geometry_report.json) |
| Enclosure base/lid collision | 0 mm³ intersecting solid volume | Same geometry report; 0.3 mm nominal rail clearance |
| ESP32 firmware build | **Succeeded** | [Build log](firmware-build.log) |
| Firmware flash use | 825,757 / 1,310,720 bytes (63.0%) | PlatformIO size output |
| Firmware static RAM | 80,896 / 327,680 bytes (24.7%) | Excludes runtime heap and stack usage; hardware load test pending |
| Host C++ control tests | Passed | [Control test log](control-test.log) and `tests/control_test.cpp` |
| Browser integration | Passed with mocked device responses | [Browser log](browser-test.log) and `tests/browser_test.py` |
| Visual review | Schematic, exploded CAD and dashboard reviewed | Preview PNGs and SVGs in package |
| Hardware / hydraulic / environmental tests | **Not performed** | Execute [acceptance plan](audit-and-acceptance.md) |

## Versions and build details

- Windows PowerShell, Python 3.12.
- KiCad CLI 10.0.6; self-contained project symbol library.
- CadQuery 2.8.0; OpenCascade-backed kernel, STEP and STL exports.
- PlatformIO Core 6.2.0; Espressif32 platform 6.9.0.
- Arduino-ESP32 framework package `3.20017.241212+sha.dcc1105b` (Arduino 2.0.17).
- Xtensa compiler package `8.4.0+2021r2-patch5`, esptool 4.5.1.
- Zig 0.16.0 C++ frontend for host tests; Playwright 1.63.0 with installed Google Chrome for browser checks.

The first Windows firmware build hit a compiler process-launch error with the long workspace path. A temporary `R:` mapping of the same workspace resolved it; the final build completed in approximately 30 seconds and the mapping was removed. `tools/build_firmware.ps1` reproduces that workaround using a free drive letter and cleans it up afterward. No firmware source workaround was needed for this environment issue.

The initial host compiler generated warnings while building its bundled C++ standard library. The final incremental host build and application test run passed; these were tool-library diagnostics, not suppressed controller assertions. KiCad's sandboxed CLI also reported inability to write a per-user registry key, but schematic export and ERC completed with the report above.

## What the software checks establish

Control tests execute the actual portable `control.h` logic. Cases cover uncalibrated inhibition, five-second pulse termination, 60-second soak, demand hysteresis, STOP latch/reset, invalid sensor rejection, stale samples, six-pulse budget exhaustion and quiet-hour recovery, millisecond rollover, invalid configuration, and close/disarm. They do not emulate GPIO, PWM hardware, task scheduling, NVS flash failure, or valve motion.

Browser tests exercise the actual HTML/JavaScript. They check demo labeling and disabled controls, live status rendering, a threshold alert, arm/close request content and token header, mobile width, CSV gaps, and offline control inhibition; no JavaScript page errors were observed. Device responses are mocked. This establishes client behavior, not live ESP32 network performance or physical actuation.

CAD verification checks B-rep validity, one solid per part, positive volumes, and installed base/lid non-interference. It does not establish printed dimensions, fastener pullout strength, servo-flange fit, panel-component clearance, sealing, thermal performance, or lifetime.

ERC checks the external module circuit using explicitly declared source rails. It is not a simulation and cannot verify wire gauge, fuse behavior, analog accuracy, EMI, or the circuitry inside purchased modules. The report's listed ignored checks are the tool's baseline settings (e.g. SPICE-model issues), not exclusions added to hide this design's electrical errors.

## Artifact integrity

`docs/manifest-sha256.json` records hashes of all packaged source and deliverable files except itself. `tools/make_release.py` creates the manifest and ZIP and checks relative Markdown links and ZIP integrity. Private credentials, local compiler caches, and firmware binaries are excluded from the shared ZIP. A locally built firmware binary is available under `firmware/.pio/build/esp32dev/` and contains the local credentials; rebuild with deployment-specific secrets rather than distributing it indiscriminately.

The final audit must identify the exact flashed binary and physical hardware, not just the package revision. Record those hashes and component serial/lot identifiers alongside the bench results.
