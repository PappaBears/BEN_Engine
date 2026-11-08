# BEN Controls Lite — RevPi install variant

**For BEN 5 (standard) and BEN 30 (option).** Controller = **KUNBUS Revolution Pi RevPi Connect 4**
(Connect S for the smallest panels): industrial DIN-rail, UL/CE, Compute Module based, −25…+55 °C, 24 VDC,
2 × Ethernet, with **RevPi DIO** (16 DI / 16 DO, 24 V) and **RevPi AIO** (4 AI 4–20 mA, 2 RTD, 2 AO) modules on
PiBridge. It runs the same `ben_engine` edge software as the Karbon 400 (broker, API, twin, history, OTBR,
PLC bridge) **plus** the interlock state machine in software (`ben-interlocks.service`), guarded by a
**hardware watchdog relay**. There is no PLC. Same BEN Pods on the same BEN Mesh.

Status: written against the KUNBUS RevPi Debian 12 image and `revpimodio2`/`pymodbus`; syntax-checked;
**unverified on hardware**.

| File | Purpose |
| --- | --- |
| `install.sh` | Lite installer (same env vars as `../install.sh`); reuses the Pro broker/ACL/chrony/nftables/systemd files, adds the interlock service, native `otbr-agent`, watchdog relay notes |
| `ben_interlocks_service.py` | 10 Hz loop: piControl I/O → `ben_engine.interlocks.Interlocks` → piControl outputs; Modbus TCP server with the PROTOCOL.md register map (bit 8 of `PLC_MODE` = LITE); pets `/dev/watchdog` and systemd `WatchdogSec` |
| `systemd/ben-interlocks.service` | real-time priority, `Conflicts=watchdog.service`, `Type=notify`, restarts always |
| `revpi_io_map.json` | PiCtory I/O names → roles (edit at panel build) |

## Watchdog relay (the Lite substitute for a PLC's hardware determinism)

RevPi DIO **O_14 → relay KW1** (24 VDC) whose NO contact sits **in series in the cooling-enable chain** — the
same chain the Pro PLC's enable output closes. `ben-interlocks.service` is the only process allowed to set
O_14 and the only one petting the RevPi hardware watchdog (60 s). If the loop stalls: systemd restarts the
service within 10 s (`WatchdogSec`); if the kernel is gone the hardware watchdog reboots the RevPi within
60 s and piControl zeroes every output during reboot → KW1 opens → every cooling unit runs on its own
controller (CONTROLS_SPEC.md failsafe table "controller dead"). KW1's NC contact lights the panel beacon.

Acceptance (same list as CONTROLS_SPEC.md §8 plus): `systemctl stop ben-interlocks` → O_14 drops within 1 s;
`kill -STOP <pid>` → service restarted within 10 s; `echo c > /proc/sysrq-trigger` → RevPi reboots within 60 s
and the units kept running on local control throughout.

## Differences from Pro on the wire

None. Same topics, same JSON, same register addresses (`ben-plc-bridge` polls `127.0.0.1:502`), same Pod join
procedure. `PLC_MODE` carries bit 8 so a commissioning report records which tier ran.
