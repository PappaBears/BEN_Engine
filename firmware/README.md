# BEN Engine firmware and controls software — build, test, flash, provision, secure

Industrial platform per `docs/CONTROLS_HARDWARE_DECISION.md`. Three parts live here:

| Directory | What it is | Build state on 2026-11-08 |
| --- | --- | --- |
| `ben-pod/` | **BEN Pod v1** firmware: Silicon Labs **MGM240P** (EFR32MG24, Secure Vault High) on our PCB, Thread/IPv6, MQTT over mutual TLS. Pod E (24 VDC/PoE, Ethernet + RS-485, 2 relays) and Pod W (Thread only, battery or 24 VDC). Implements `spec/PROTOCOL.md` v1.1. | **Core compiled and unit-tested on the host (37/37 pass). EFR32 cross-build NOT performed** — no Simplicity SDK / arm-none-eabi toolchain on the build host (see "What was compiled here"). |
| `ben-edge/` | Edge computer package for the **BEN Controller** data half: OnLogic Karbon 400 (Pro) or RevPi Connect 4 (`lite/`, Lite). Mosquitto mTLS, OTBR, chrony, `ben_engine.api`, PLC bridge, nftables, TPM/LUKS, backup. Not firmware. | Implemented, `bash -n` clean, **unverified on hardware**. See its README. |
| `ben-plc/` | **PLCnext AXC F 2152** project skeleton (Pro): interlock program in IEC 61131-3 ST, Modbus register map, program structure. On Lite the same logic runs as `software/ben_engine/interlocks.py` (16 host tests pass). | ST written, **not compiled** (no PLCnext Engineer here). Python reference tested. |

History: this directory replaced the hobby-grade targets on 2026-11-08. The earlier ESP32 HAL (`hal_esp32.*`,
Olimex carrier) and the Raspberry Pi gateway package were **replaced** by `hal_efr32.*` and `ben-edge/`; no
file here targets them any more. This paragraph is the only place the old names appear.

## Architecture of the Pod firmware

```
src/main.cpp            EFR32 branch (#ifdef BEN_TARGET_EFR32): Thread join/attach, SNTP over Thread, sensors (SHT45, SDP810,
                        ADS124S08 Pt1000 ADC), attestation intercept, LEDs, 4-bit DIP
                        native branch: 10 s simulation using the mock HAL (what `make sim` builds)
lib/benhal/hal.h        abstract HAL: Clock, Gpio, I2cBus, OneWireBus, Nvs, Net, System  (unchanged)
lib/benhal/hal_efr32.*  Simplicity SDK + OpenThread implementation: sl_sleeptimer, em_gpio via a logical pin table,
                        sl_i2cspm, NVM3, MQTT 3.1.1 over mbedTLS/PSA over otTcp, Gecko Bootloader OTA, PSA attestation
lib/benhal/hal_mock.h   in-memory implementation for tests  (unchanged)
lib/bencore/            platform independent, zero external dependencies — UNCHANGED (comments only):
  channels.*            channel map, gain/offset calibration applied in the Pod, cal_id, NVS load/save
  telemetry.*           telemetry + status JSON exactly as PROTOCOL.md; topic builder
  commands.*            cmd parser (set_output/get_cal/set_cal/tare/identify/reboot/ota) + ack JSON
  ringbuf.*             1 h @ 1 Hz ring buffer of 44-byte packed records (158 400 B, static)
  outputs.*             relay outputs; failsafe rule (60 s without broker -> failsafe relays drop, others hold)
  alarms.*              local ASHRAE A1 thresholds with hold times (edge stays the alarm system of record)
  timesync.*            SNTP anchor + monotonic millis; ts=0 and clock_valid=false until synced
  node_app.*            orchestration: 1 Hz telemetry, 10 s retained status, buffering, ordered replay, cmd->ack
  json_mini.h           fixed-buffer JSON writer and flat-object reader (same bytes on target and host)
test/test_core/         Unity tests (37)  (unchanged)
test/support/unity.h    Unity-compatible shim used only by the Makefile fallback
Makefile                host build: make test / make sim
platformio.ini          env `native` (host) and `mgm240p` (cross-compile against a Simplicity SDK checkout; limited PlatformIO support)
gecko/ben_pod.slcp      Simplicity Studio 5 / SLC project (the supported target build)
gecko/CMakeLists.txt    Silicon Labs CMake flow on top of `slc generate -o cmake`
```

The PROTOCOL.md v1.1 status fields (`cert_id`, `attested`, `parent`, `lqi`, `path`) and the `attest` op are
produced in `main.cpp`/`hal_efr32.cpp`, **outside** `bencore`, so the core and its 37 tests did not change.
`bencore` still names the outputs `relay1..4` with logical pins 32/33/14/15; `hal_efr32.cpp` maps 32/33 to
the two Pod E relay drivers and leaves 14/15 unconnected. `relay1` is no longer "cooling enable" in the
system (that is a PLC output now); on a Pod it is a general-purpose failsafe relay (beacon/fan boost).

Memory note: MGM240P = 1.5 MB flash / 256 kB RAM. Ring buffer 155 kB + OpenThread FTD ≈ 40 kB + mbedTLS
≈ 20 kB + app leaves ≈ 30 kB (**estimate, not measured**). Use `BEN_RING_SECONDS=1800` if the first link
map says otherwise; the sleepy Pod W build (MTD) is ~15 kB smaller.

## Build

```bash
cd firmware/ben-pod
make test                                   # host: 37 unit tests (what ran here)
make sim                                    # host: 10 s simulation of the core
# target (needs Simplicity SDK 2024.6 + arm-none-eabi-gcc 12 + Simplicity Commander):
slc generate -p gecko/ben_pod.slcp -d gecko/build/gen -o cmake --with mgm240pb32vna
cmake -S gecko -B gecko/build -G Ninja -DCMAKE_TOOLCHAIN_FILE=$BEN_SISDK/cmake/toolchain.cmake -DBEN_SISDK=$BEN_SISDK
cmake --build gecko/build                   # -> gecko/build/ben_pod.s37
commander gbl create ben_pod.gbl --app gecko/build/ben_pod.s37 --sign ben-pod-signing-key.pem   # signed OTA image
commander flash --device EFR32MG24B310F1536IM48 gecko/build/ben_pod.s37                        # J-Link / WSTK
pio run -e mgm240p                          # alternative cross-compile (BEN_SISDK set; after slc generate)
```

## Test

```bash
cd firmware/ben-pod && make test            # host g++ + test/support/unity.h shim
pio test -e native                          # same tests with real Unity when the native platform is available
cd ../.. && python3 -m pytest tests/test_interlocks.py   # interlock reference (16)
```

### What was compiled here (honest record)

Host: Linux x86-64, `g++` (GCC) `-std=c++17 -Wall -Wextra`, Python 3 + pytest. No Silicon Labs toolchain,
no PlatformIO platforms (network-restricted), no PLCnext Engineer.

```
$ cd firmware/ben-pod && make clean && make test
  ... 37 test lines ...:PASS
  -----------------------
  37 Tests 0 Failures 0 Ignored
  OK
$ make sim
  BEN Pod 1.0.0 native simulation: 5 s online, 3 s offline, 2 s online
  ... 13 messages (10 telemetry incl. 4 with "replay":true, 2 status, 1 ack) ...
  published: 10 telemetry, 2 status, 1 ack; buffered now: 0; replayed: 4; seq=10
$ python3 -m pytest tests/test_interlocks.py -q
  16 passed
$ bash -n firmware/ben-edge/install.sh firmware/ben-edge/lite/install.sh …    (all clean)
```

So: `lib/bencore` + `lib/benhal/hal_mock.h` + `src/main.cpp` (native branch) compiled with zero warnings and
all 37 unit tests pass. **`lib/benhal/hal_efr32.cpp`, the EFR32 branch of `src/main.cpp`, `gecko/ben_pod.slcp`,
`gecko/CMakeLists.txt` and the `mgm240p` PlatformIO env have never been compiled.** They are written against
Simplicity SDK 2024.6 / OpenThread 2024-Q2 APIs (`otTcp*`, `otSntpClientQuery`, `otJoinerStart`, `nvm3_*`,
`sl_sleeptimer_*`, `I2CSPM_Transfer`, `SPIDRV_M*`, `bootloader_*`, `psa_sign_message`,
`mbedtls_pk_setup_opaque`) and the first build in Simplicity Studio will need signature fixes and a real
`ota_coap.c` (CoAP block-wise fetch, stubbed to return false). `BenInterlocks.st` has never been compiled either.

Tests cover: calibration apply/reject/NVS round-trip, tare, telemetry JSON byte-exact against PROTOCOL.md,
status JSON, topic builder, JSON escaping, command parsing for every op and 19 malformed inputs, ack JSON,
ring buffer pack/unpack/wrap/1 h capacity, failsafe at exactly 60 s, link-down, `millis()` wrap, alarm hold
times, SNTP anchoring and step detection, and the app end to end (1 Hz publish, 90 s offline buffering,
ordered replay with original timestamps, cmd routing/ack, DIP provisioning, unsynced-clock status).

## Protocol behaviours worth knowing (beyond PROTOCOL.md's text)

- `ts` is 0 and status carries `"clock_valid":false` until the first SNTP fix from the edge (`fd00:ben::1`).
- Replayed records carry their original `ts`/`seq`, an empty `"raw":{}` and `"replay":true`.
- `status` is retained; the MQTT last-will publishes `"errors":["offline (last will)"]` if the TLS session dies.
- Failsafe: outputs marked `failsafe` drop 60 s after the last broker contact or at once on link loss; others hold.
- `set_cal` rejects gain outside 0.5–2.0 and persists to NVM3 immediately.
- `attest` is answered by `main.cpp` (not `bencore`): `{"ok":true,"result":{"sig":…,"fw_hash":…,"boot":"verified","cert_id":…}}`.

## Pin map (BEN Pod v1 PCB, MGM240P) — logical id → port/pin, table in `hal_efr32.cpp`

| Function | Logical | MGM240P pin | Notes |
| --- | --- | --- | --- |
| RELAY1 / RELAY2 (Pod E only) | 32 / 33 | PB0 / PB1 | coil drivers, 10 A relays; relay1 failsafe |
| LEAK comparator | 36 | PC0 | resistive rope, HIGH = wet |
| DOOR dry contact | 39 | PC1 | pull-up, HIGH = open |
| S0 PULSE (opto) | 34 | PC2 | falling edge |
| DI2 / EPO monitor | 35 | PC3 | **monitor only** |
| IDENT LED / LINK LED | 2 / 3 | PD2 / PD3 | IDENT: solid = identify, 1 Hz = broker lost, blip = normal |
| DIP 0..3 | 5..8 | PA5..PA8 | 4-bit node id override (bench); unit id always from provisioning |
| RTD ADC CS / DRDY | 40 / 41 | PA0 / PA4 | ADS124S08 on SPI (`spidrv_rtd`) |
| I²C SDA/SCL | — | PC4 / PC5 | `i2cspm_sensor`: SHT45 0x44, SDP810 0x25 |
| Pod E: LAN8742 nRST / RS-485 DE | 42 / 43 | PB2 / PB3 | W5500 SPI MAC+PHY (decided; EFR32MG24 has no MAC), RS-485 on USART1 |
| SWD / secure debug | — | PF0/PF1 | locked after provisioning (Secure Vault debug lock, unlock via signed challenge) |

## Secure provisioning cell (how a Pod gets its certificate)

Two accepted routes; the per-Pod record (serial, EUI-64, certificate serial = `cert_id`, PSKd, firmware hash,
operator, date) is written to the Schreiber AI device registry either way.

**Route A — Silicon Labs Custom Part Manufacturing Service (CPMS).** Silicon Labs programs each MGM240P at
their factory with: our Gecko Bootloader (signed, secure boot enabled, anti-rollback on), the public signing
key in the Secure Element's OTP, a **device identity key pair generated inside Secure Vault** and a device
certificate chained to a Silicon Labs-held intermediate that we cross-sign into the Schreiber AI Device CA,
secure debug lock enabled, tamper response configured. Modules arrive provisioned; our line only adds the
application image, the PSKd label and the registry entry. Preferred above ~2 000 units/yr.

**Route B — in-house provisioning over SWD with an HSM-held CA.** Fixture: bed-of-nails, Simplicity Commander
+ J-Link, an **HSM (YubiHSM 2 / Nitrokey HSM, or the cloud KMS at Schreiber AI)** that holds the Device CA
private key and the firmware signing key, air-gapped PC. Steps per Pod, scripted and logged:
1. `commander security genkey --type ecc-p256` on the device → device key pair generated **in the Secure Element**; the public key is read back; the private key never leaves the chip.
2. The PC builds a CSR (`CN=pod-<serial>`), the HSM signs it with the Device CA (5 y validity) → certificate written to NVM3 (`cert_pem`) with the Device CA chain (`ca_pem`) and `cert_id`.
3. `commander security writekey --sign ben-pod-signing-pubkey.pem` → signing public key into SE OTP; `commander security writeconfig --configfile secure_boot_antirollback.json` → secure boot + anti-rollback **ON (irreversible)**.
4. Flash Gecko Bootloader + signed application; `commander security lockdebug` with a device-specific unlock token escrowed in the HSM.
5. Derive PSKd = base32(HMAC(registry secret, serial))[:8]; print the label (serial, EUI-64, PSKd QR); `nvm3 set pskd`.
6. Power-cycle; verify `boot: verified`, read `cert_id`, run the self-test, record everything in the registry. Tamper: a Pod with `boot != verified` or an unknown `cert_id` is quarantined.

## Signed firmware (Gecko Bootloader, ECDSA P-256, anti-rollback)

- The Gecko Bootloader is built with **secure boot enforced** (`BOOTLOADER_ENFORCE_SIGNED_UPGRADE`,
  `BOOTLOADER_ENFORCE_SECURE_BOOT`), ECDSA P-256 signature check over the application image and the GBL upgrade
  file, and **certificate-based anti-rollback**: every release carries a monotonically increasing version in
  `ApplicationProperties_t`; the bootloader refuses a lower one. The Secure Element's secure boot verifies the
  bootloader itself (root of trust in OTP).
- Signing key: generated once in the HSM; never on a build server; the build pipeline submits the hash and
  receives the signature (`commander gbl create --sign` against a PKCS#11 slot). Public key in SE OTP (step 3 above).
- Release manifest: `{version, sha256, signature, min_hw_rev, date}` signed by the release key; the edge
  computer verifies it before offering the image to Pods.

## OTA over Thread

1. The edge publishes `{"op":"ota","url":"coap://[fd00:ben::1]/fw/ben-pod-1.0.1.gbl","sha256":"…"}` on the Pod's `cmd` topic (Pod E on Ethernet may receive an `https://10.20.0.1:8443/…` URL instead).
2. The Pod fetches the GBL **CoAP block-wise (Block2, 1024 B)** over Thread into **bootloader storage slot 0** while hashing; sleepy Pods fetch at their poll rate (a 400 kB image takes ~10 min at 1 s polls — acceptable; the edge upgrades Pods one or two at a time so the mesh stays available).
3. Hash mismatch → slot erased, ack `ok:false`. Hash OK → `bootloader_verifyImage` checks the **ECDSA signature and the anti-rollback version**; a correct hash of a wrong or old image never runs.
4. Ack `{"ota":"started"}`, reboot; the bootloader swaps; the app marks itself good after its first successful telemetry publish (else the bootloader falls back to the previous image).
5. The edge waits for the new `status.fw` and `attested:true` before the next Pod. Rollback = publish the previous *higher-numbered* rollback build (anti-rollback forbids older versions; keep a "1.0.1-rollback → 1.0.2" release ready).

## Pod E wired path: PoE and RS-485

- **Power:** 802.3af PD (Si3402 class 0 controller, isolated flyback to 3.3 V/5 V) **or** 24 VDC terminal (reverse-protected, 1 A fuse). Either source; PoE preferred where the controls switch has PoE.
- **Ethernet:** the EFR32MG24 has no Ethernet MAC; Pod E uses a **W5500 SPI MAC+PHY** (10/100, hardware TCP/IP offload) — decided 2026-11-08 over KSZ8851 for its hardware TCP/IP offload and wide industrial use; the decision doc and Pod spec now say W5500. Firmware path: MQTT/TLS over the W5500 socket instead of otTcp; `Efr32Net::path()` reports `"eth"`.
- **RS-485 Modbus RTU** (USART1 + isolated transceiver, 120 Ω end termination jumper): the Pod is a Modbus **slave** to the PLC (Pro) or RevPi (Lite); registers 30001.. mirror the channel table (T_in ×100, RH ×10, dP ×10, leak, door, relays) so the PLC can use a Pod's readings in an interlock without the mesh. Thread stays the telemetry path to the edge; when Thread is down Pod E telemetry goes over Ethernet; when both are down the PLC still reads it over RS-485.
- Isolation: Ethernet/PoE 1.5 kV magnetics, RS-485 2.5 kV, relays 4 kV coil-contact.

## Protocol conformance quick check (host)

```bash
cd firmware/ben-pod && make sim | head -3
```
prints a telemetry message that can be diffed against the example in `spec/PROTOCOL.md` key for key.
