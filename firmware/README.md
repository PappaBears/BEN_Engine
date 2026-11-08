# BEN Engine firmware — build, test, flash, provision, secure

Two parts live here:

| Directory | What it is | Build state on 2026-11-07 |
| --- | --- | --- |
| `ben-node/` | BEN Node v1 firmware: ESP32 on an **Olimex ESP32-POE-ISO** carrier, PlatformIO, Arduino framework. Implements `spec/PROTOCOL.md` exactly. | **Core compiled and unit-tested on the host (37/37 pass). ESP32 cross-build NOT performed** — the `espressif32` platform download is blocked on the build host (see "What was compiled here"). |
| `ben-gateway/` | Raspberry Pi 5 gateway package (Mosquitto, chrony, `ben_engine.api` service, firewall, backup). Not ESP code. | Implemented, syntax-checked, **unverified on hardware**. See its own README. |

## Architecture of the node firmware

```
src/main.cpp            ESP32 only (guarded #ifdef ARDUINO): sensor drivers, pin map, MQTT/Ethernet, serial provisioning
                        native branch: 10 s simulation using the mock HAL (what `pio run -e native` / `make sim` builds)
lib/benhal/hal.h        abstract HAL: Clock, Gpio, I2cBus, OneWireBus, Nvs, Net, System
lib/benhal/hal_esp32.*  Arduino/ESP-IDF implementation (ETH + PubSubClient + Preferences + Update + SNTP)
lib/benhal/hal_mock.h   in-memory implementation for tests
lib/bencore/            platform independent, zero external dependencies:
  channels.*            channel map (T_in_1..4, T_out_1..4, T_ref, RH, dP_aisle, leak, door, ai0..3_mA, relay1..4, pulse_kwh),
                        gain/offset calibration applied in the node, cal_id, NVS load/save
  telemetry.*           telemetry + status JSON exactly as PROTOCOL.md; topic builder
  commands.*            cmd parser (set_output/get_cal/set_cal/tare/identify/reboot/ota) + ack JSON; rejects malformed input
  ringbuf.*             1 h @ 1 Hz ring buffer of 44-byte packed records (3600 x 44 B = 158 400 B, static)
  outputs.*             relay outputs; failsafe rule (60 s without gateway -> failsafe relays drop, others hold)
  alarms.*              local ASHRAE A1 thresholds with hold times (gateway stays the alarm system of record)
  timesync.*            SNTP anchor + monotonic millis; ts=0 and clock_valid=false until synced; step counter
  node_app.*            orchestration: 1 Hz telemetry, 10 s retained status, buffering, ordered replay, cmd->ack
  json_mini.h           fixed-buffer JSON writer and flat-object reader (same bytes on ESP32 and host)
test/test_core/         Unity tests (37)
test/support/unity.h    Unity-compatible shim used only by the Makefile fallback
Makefile                host fallback build when the PlatformIO `native` platform cannot be downloaded
```

Why no ArduinoJson in the core: the protocol needs flat objects and one level of nesting; an in-house
writer/reader keeps `lib/bencore` dependency-free so the identical bytes are tested on the host. ArduinoJson
stays in `platformio.ini` for anything main.cpp may need later (none today).

Memory note: the Olimex ESP32-POE-ISO carries a classic ESP32-WROOM (520 kB SRAM, no PSRAM); the 158 kB ring
buffer plus the Arduino Ethernet/MQTT stacks fit but leave roughly 100 kB of heap. If the v1.1 custom carrier
moves to ESP32-S3 with PSRAM (the brief's intent), raise `BEN_RING_SECONDS` freely. **The ESP32 heap figure is
an estimate, not measured.**

## Build

```bash
cd firmware/ben-node
pio run -e olimex_esp32_poe_iso                 # ESP32 image  -> .pio/build/olimex_esp32_poe_iso/firmware.bin
pio run -e olimex_esp32_poe_iso -t upload       # flash over USB (CH340/CP2102 on the Olimex board)
pio device monitor -b 115200                    # serial console
pio run -e native                               # host build of the simulation
make sim                                        # same, without PlatformIO platforms
```

## Test

```bash
cd firmware/ben-node
pio test -e native            # preferred: PlatformIO native + real Unity
make test                     # fallback: host g++ + test/support/unity.h shim (what ran here)
```

### What was compiled here (honest record)

Host: Linux, `g++` (GCC) with `-std=c++17 -Wall -Wextra`, PlatformIO Core 6.2.0, network-restricted.

```
$ pio pkg install -g -p espressif32                 -> Platform Manager: Installing espressif32 / HTTPClientError
$ pio pkg install -g -p "platformio/espressif32"    -> HTTPClientError
$ pio pkg install -g -p native                      -> HTTPClientError
$ pio test -e native                                -> Collected 1 tests / Platform Manager: Installing native / HTTPClientError
$ pio run -e native                                 -> Platform Manager: Installing native / HTTPClientError
$ make clean && make test
  ... 37 test lines ...:PASS
  -----------------------
  37 Tests 0 Failures 0 Ignored
  OK
$ make sim
  BEN Node 1.0.0 native simulation: 5 s online, 3 s offline, 2 s online
  ... 13 messages printed (10 telemetry incl. 4 with "replay":true, 2 status, 1 ack) ...
  published: 10 telemetry, 2 status, 1 ack; buffered now: 0; replayed: 4; seq=10
```

So: `lib/bencore` + `lib/benhal/hal_mock.h` + `src/main.cpp` (native branch) compiled with zero warnings and all
37 unit tests pass. **`lib/benhal/hal_esp32.cpp` and the ESP32 branch of `src/main.cpp` have never been compiled**:
they are written against the espressif32 Arduino core 2.x / ESP-IDF 4.4 APIs (`ETH.begin` LAN8720 signature,
`sntp_*`, `Update`, `Preferences`, Adafruit SHT4x/ADS1X15, Sensirion I2C SDP 0.1.x) and the first `pio run -e
olimex_esp32_poe_iso` on a connected machine will very likely need small signature fixes. Library version pins in
`platformio.ini` are the current majors; adjust if the registry resolves differently.

Tests cover: calibration apply/reject/NVS round-trip, tare (incl. gain interaction and non-tareable channels),
telemetry JSON byte-exact against the PROTOCOL.md example, status JSON, topic builder, JSON escaping, command parsing
for every op and 19 malformed inputs, ack JSON for every op (ok and error shapes), ring-buffer record size/pack/unpack/
wrap/1 h capacity, failsafe at exactly 60 s, link-down, `millis()` wrap, alarm hold times, SNTP anchoring and
step detection, and the app end to end (1 Hz publish with sequence numbers, 90 s offline buffering, ordered
replay with original timestamps, cmd routing/ack, DIP provisioning, unsynced-clock status).

## Protocol behaviours worth knowing (beyond PROTOCOL.md's text)

- `ts` is 0 and status carries `"clock_valid":false` until the first SNTP fix from the gateway (10.20.0.1).
- Replayed records (flushed after a gateway loss) carry their original `ts`/`seq`, an empty `"raw":{}` and
  `"replay":true`, because the compact ring record stores calibrated values only. Live records always include raw counts.
- While a backlog exists, new live samples are appended behind it, so `seq` is strictly increasing on the wire.
- `status` is retained; the MQTT last-will publishes a status with `"errors":["offline (last will)"]` if the TCP session dies.
- Failsafe: `relay1` (cooling enable) is `failsafe=true` and drops 60 s after the last gateway contact or at once on link
  loss; `relay2..4` hold. Commands received during the loss are remembered and applied on restore. Table in `CONTROLS_SPEC.md`.
- Acks for errors are `{"id":"…","ok":false,"error":"…"}`; a command with no `id` is acked with `"id":""`.
- `set_cal` rejects gain outside 0.5–2.0 (a real sensor never needs more) and persists to NVS immediately.
- Status also carries `buffered` (ring depth) and `clock_valid`; both are additive to PROTOCOL.md.

## Pin map (Olimex ESP32-POE-ISO)

Ethernet owns GPIO 0, 12, 17, 18, 19, 21, 22, 23, 25, 26, 27; UART0 owns 1, 3. Everything else is used:

| Function | GPIO | Notes |
| --- | --- | --- |
| DS18B20 1-Wire | 4 | one 4.7 kΩ pull-up to 3V3 at the terminal block; up to 8 sensors, 12-bit |
| I²C SDA / SCL | 13 / 16 | UEXT; SHT45 (0x44), SDP810 (0x25), ADS1115 (0x48) |
| relay1 cooling enable (failsafe) | 32 | relay module input, active high |
| relay2 lights | 33 | |
| relay3 fan boost | 14 | |
| relay4 spare | 15 | strapping pin: driver input has a pull-down |
| leak rope | 36 | input only; 100 k / 10 k divider from the rope's 3V3 excitation; HIGH = wet |
| door reed | 39 | input only; external 10 kΩ pull-up; HIGH = open |
| meter S0 pulse | 34 | input only, IRQ on falling edge; shares BUT1 (pressing it counts one pulse) |
| EPO / fire loop aux contact | 35 | **monitor only**; open the board's BAT_SENS jumper; reported as an error string |
| IDENT LED | 2 | solid = identify, 1 Hz blink = gateway lost, 50 ms blip every 2 s = normal |
| spare / 1-bit DIP | 5 | low at boot forces `node1` (the 4-bit DIP lives on the v1.1 custom carrier via PCF8574) |

## Provisioning (how a node gets its unit / node id)

Primary: **serial provisioning** over the USB console at 115200 8N1. The gateway installer prints one line per node;
paste it:

```
PROV unit=ben20-0007 node=node3 broker=10.20.0.1 user=node3 pass=Xk3…   -> "PROV OK, rebooting"
ID?                                                                     -> unit=… node=… broker=… fw=1.0.0
FACTORY                                                                 -> erases identity + cal_id, reboots
```

Identity, broker credentials, calibration and `tel_ms` live in NVS namespace `ben`. Secondary: a DIP switch.
On the Olimex carrier only GPIO 5 is free, so it is a single bit (`node1` override, useful on a bench). The
v1.1 custom carrier has a 4-position DIP read through a PCF8574 and `NodeApp::provision_from_dip(0..15)`
already supports it. DIP never sets the unit id; that always comes from `PROV`.

## OTA

The gateway publishes `{"op":"ota","url":"https://10.30.0.1:8000/fw/ben-node-1.0.1.bin","sha256":"…"}`. The node
streams the image into the inactive OTA partition while hashing it, aborts unless the SHA-256 matches, acks
`{"ota":"started"}` and restarts after the ack is on the wire. With Secure Boot v2 on, the bootloader additionally
refuses an unsigned image, so a correct hash of a wrong image still cannot run. Roll back by publishing the previous
image; the app marks the running image valid after its first successful telemetry publish (`esp_ota_mark_app_valid_cancel_rollback`
is the one call still to add in `hal_esp32.cpp` once the toolchain builds).

## Security: signed images and encrypted flash (documented procedure, not yet executed)

Controls layer rule set (CONTROLS_SPEC.md): no cloud dependency, signed firmware, local-first data.

1. **Generate the signing key once, offline, at Schreiber AI** — never on a build server:
   `espsecure.py generate_signing_key --version 2 ben-node-secure-boot-v2.pem` (RSA-3072). Store in the HSM/password manager; back up on paper.
2. **Sign every release:** `espsecure.py sign_data --version 2 --keyfile ben-node-secure-boot-v2.pem --output firmware-signed.bin firmware.bin`
   (PlatformIO can do this automatically with `board_build.secure_boot = true` and `CONFIG_SECURE_SIGNED_APPS_RSA_SCHEME` in `sdkconfig.defaults`).
3. **Burn the public key digest** into eFuse on each node during factory programming (irreversible):
   `espefuse.py --port … burn_key BLOCK2 ben-node-secure-boot-v2-pubdigest.bin SECURE_BOOT_DIGEST0` and `espefuse.py burn_efuse SECURE_BOOT_EN`.
   Also burn `DIS_USB_JTAG` / `DIS_PAD_JTAG` and set `JTAG_SEL_ENABLE=0` so the debug port is closed.
4. **Flash encryption (release mode):** `espefuse.py burn_efuse SPI_BOOT_CRYPT_CNT 7` and `DIS_DOWNLOAD_MANUAL_ENCRYPT`; let the
   chip generate its own key in eFuse (`BLOCK_KEY0`, purpose `XTS_AES_128_KEY`) so no key ever leaves the device. NVS (which holds broker
   credentials and calibration) then lives in encrypted flash; enable `nvs_encryption` in `sdkconfig.defaults`.
5. **Verify:** `espefuse.py summary` shows `SECURE_BOOT_EN = 1`, `SPI_BOOT_CRYPT_CNT = 7`; `esptool.py read_flash` of the app region returns ciphertext;
   an unsigned image fails to boot with `secure boot verification failed`.
6. **Process:** one eFuse-burn station in production, a checklist signed per serial number, and the public digest recorded in the unit's turnover package.

Classic ESP32 (the Olimex carrier) supports Secure Boot v2 only on chip revision 3 (ECO3) and later; check with
`esptool.py chip_id`. ESP32-S3 (v1.1 carrier) supports it on all revisions.

## Protocol conformance quick check (host)

```bash
cd firmware/ben-node && make sim | head -3
```
prints a telemetry message that can be diffed against the example in `spec/PROTOCOL.md` key for key.
