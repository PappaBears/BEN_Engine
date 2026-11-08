(* =====================================================================================================
   BEN Engine — BEN Controller (Pro) — interlock program for PLCnext AXC F 2152 (Schreiber AI)
   IEC 61131-3 Structured Text, PLCnext Engineer 2024.x. Cyclic task "BenInterlocks" at 100 ms.

   This file is a transcription of the executable reference software/ben_engine/interlocks.py.
   The unit tests in tests/test_interlocks.py are the acceptance for THIS logic too: any change here
   is first made in the Python class, tested, then mirrored. Rules (CONTROLS_SPEC.md §1):
     - life safety (fire, EPO) is hardwired; this program only READS aux contacts (bEpoLoopOk, bFire*);
     - the edge computer only ADVISES: it writes EDGE_WATCHDOG, SUPPLY_TRIM_x10, TEST_REQUEST; all three are
       clamped/ignored when stale; nothing the edge sends can open a valve or stop a cooling unit directly;
     - every output has a defined state when inputs are lost (failsafe table in README.md).
   STATUS: written, NOT compiled (no PLCnext Engineer here). Syntax follows IEC 61131-3 3rd ed. as PLCnext
   Engineer accepts it; array bounds and I/O names come from the Axioline configuration in the project.
   ===================================================================================================== *)

(* ------------------------------------------------------------------ global constants (tunable per unit) *)
VAR_GLOBAL CONSTANT
    N_COOL_MAX          : INT  := 8;           (* array size; actual count in GVL_Plant.nCooling *)
    N_ZONE_MAX          : INT  := 8;
    N_DOOR_MAX          : INT  := 4;
    T_START_FEEDBACK    : TIME := T#90s;       (* unit must report RUN within this time after CMD *)
    T_FAULT_RETRY       : TIME := T#10m;       (* faulted unit retried once after 10 min *)
    T_ROTATE            : TIME := T#168h;      (* weekly lead rotation *)
    T_MIN_RUN           : TIME := T#5m;        (* anti-short-cycle *)
    T_VALVE_TRAVEL      : TIME := T#30s;
    T_DOOR_ALARM        : TIME := T#5m;
    T_EDGE_WATCHDOG     : TIME := T#30s;
    T_GEN_START_FAIL    : TIME := T#60s;
    TRIM_LIMIT_x10      : INT  := 20;          (* ±2.0 K *)
    KW_PER_UNIT_MARGIN  : REAL := 0.85;
END_VAR

(* ------------------------------------------------------------------ plant configuration (set at commissioning) *)
VAR_GLOBAL
    GVL_Plant : STRUCT
        nCooling     : INT  := 3;
        rUnitKw      : REAL := 30.0;
        nZones       : INT  := 2;
        nDoors       : INT  := 2;
        iRedundancy  : INT  := 1;              (* 0 = N, 1 = N+1, 2 = 2N *)
        rSetpointC   : REAL := 20.0;
        wProjectCrc  : WORD := 16#0000;        (* written by the build script; edge compares (attested) *)
    END_STRUCT;
END_VAR

(* ------------------------------------------------------------------ field I/O image (Axioline F, mapped in PLCnext Engineer) *)
VAR_GLOBAL
    (* inputs *)
    abCoolRunFb     : ARRAY[1..N_COOL_MAX] OF BOOL;     (* AXL F DI16/1 *)
    abCoolFaultIn   : ARRAY[1..N_COOL_MAX] OF BOOL;
    abLeakZone      : ARRAY[1..N_ZONE_MAX] OF BOOL;     (* RLE SeaHawk zone relays *)
    abValveClosedLs : ARRAY[1..N_ZONE_MAX] OF BOOL;
    abDoorOpen      : ARRAY[1..N_DOOR_MAX] OF BOOL;
    bEpoLoopOk      : BOOL;                             (* releasing panel / EPO aux — MONITOR ONLY *)
    bFireAlarm, bFireTrouble, bFireReleased, bFireSupervisory : BOOL;   (* MONITOR ONLY *)
    bUtilityOk, bAtsOnGenerator, bGenRunning, bGenFault, bUpsOnBattery, bPsuRedundancyOk : BOOL;
    bHmiManual, bHmiOff : BOOL;                         (* panel selector *)
    bHmiResetLatched, bHmiResetLeak : BOOL;             (* momentary reset buttons — NOT writable by the edge *)
    rItKw, rSupplyC, rReturnC, rOutdoorC, rAisleDp, rRh : REAL;   (* scaled from AXL F AI4 I / RTD4 *)
    (* outputs *)
    abCoolCmd       : ARRAY[1..N_COOL_MAX] OF BOOL;     (* AXL F DOR LC/1 relay outputs -> unit remote enable *)
    abValveClose    : ARRAY[1..N_ZONE_MAX] OF BOOL;
    bCduPumpStop    : BOOL;
    bCoolingEnable  : BOOL;                             (* hardware enable chain relay; FALSE = units on local control *)
    bBeacon         : BOOL;
END_VAR

(* ------------------------------------------------------------------ Modbus TCP / OPC UA exchange image (spec/PROTOCOL.md) *)
VAR_GLOBAL
    MB : STRUCT
        wHeartbeat        : WORD;   (* 40001 *)
        wMode             : WORD;   (* 40002 *)
        wProjectCrc       : WORD;   (* 40003 *)
        wEdgeWatchdog     : WORD;   (* 40004 W *)
        wEdgeLost         : WORD;   (* 40005 *)
        iSupplyTrim_x10   : INT;    (* 40006 W *)
        wTestRequest      : WORD;   (* 40007 W *)
        wCoolCmd, wCoolRun, wCoolFault, wCoolLead, wCoolNReq, wFailoverCnt, wLastFailoverS : WORD;   (* 40010..40016 *)
        wLeakZone, wIsoValveCmd, wIsoValveClosed, wIsoValveFault, wCduPumpStop : WORD;             (* 40020..40024 *)
        wDoorState, wDoorOpenS, wEpoLoopOk, wFirePanel : WORD;                                     (* 40030..40033 *)
        wAtsSource, wGenState, wGenRunS, wUpsOnBattery, wUtilityOk : WORD;                         (* 40040..40044 *)
        wItKw_x10 : WORD; iSupplyC_x10, iReturnC_x10, iOutdoorC_x10, iAisleDp_x10 : INT; wRh_x10 : WORD;   (* 40050..40055 *)
        aiRtd_x100 : ARRAY[1..32] OF INT;      (* 40060..40091 *)
        awAi_uA    : ARRAY[1..16] OF WORD;     (* 40100..40115 *)
        wAlarmWord, wPsuRedundancyOk : WORD; iPanelTempC_x10 : INT;                                (* 40120..40122 *)
    END_STRUCT;
END_VAR

(* alarm bit positions = ALARM_WORD *)
VAR_GLOBAL CONSTANT
    ALM_COOL_CAPACITY_LOST : INT := 0;  ALM_ALL_UNITS_FAULTED : INT := 1;  ALM_LEAK_ISOLATION : INT := 2;
    ALM_VALVE_FAULT : INT := 3;         ALM_DOOR_OPEN_LONG : INT := 4;     ALM_EPO_LOOP_OPEN : INT := 5;
    ALM_FIRE_ALARM : INT := 6;          ALM_GEN_FAULT : INT := 7;          ALM_ATS_ON_GEN : INT := 8;
    ALM_EDGE_LOST : INT := 9;           ALM_PSU_REDUNDANCY : INT := 10;    ALM_UPS24_ON_BATTERY : INT := 11;
    MODE_OFF : INT := 0; MODE_AUTO : INT := 1; MODE_MANUAL : INT := 2; MODE_TEST : INT := 3; MODE_FAULT : INT := 4;
END_VAR

(* =====================================================================================================
   PROGRAM BenInterlocks — one scan = one call (100 ms task)
   ===================================================================================================== *)
PROGRAM BenInterlocks
VAR
    (* per-unit state (mirrors _UnitState in interlocks.py) *)
    abUnitFaulted, abUnitLatched : ARRAY[1..N_COOL_MAX] OF BOOL;
    atSinceCmd, atFaultSince, atRunTime : ARRAY[1..N_COOL_MAX] OF TIME;
    iLead : INT := 1;
    tRotate : TIME;
    wFailoverCount : WORD;
    tLastFailover : TIME := T#49d;             (* "long ago" *)
    (* leak *)
    abValveCmd, abValveFault : ARRAY[1..N_ZONE_MAX] OF BOOL;
    atValveSince : ARRAY[1..N_ZONE_MAX] OF TIME;
    (* doors *)
    atDoorOpen : ARRAY[1..N_DOOR_MAX] OF TIME;
    (* edge watchdog *)
    wEdgeWdLast : WORD; tEdgeWdAge : TIME; bEdgeLost : BOOL := TRUE; bEdgeSeen : BOOL := FALSE;
    (* generator *)
    iGenState : INT; tGenSince, tGenRun : TIME;
    (* mode / test *)
    iMode : INT := MODE_AUTO; iTestActive : INT; tTestSince : TIME;
    dwAlarm : DWORD;
    (* scan *)
    tCycle : TIME := T#100ms;
    i, k, iNReq, iNAvail, iChosen, iIdx : INT;
    bWant, bAnyIso, bPumpStop, bHealthy, bAnyAvail : BOOL;
    rN : REAL; iN, iExtra : INT;
    iTrim : INT;
    fbResetLatched, fbResetLeak : R_TRIG;
END_VAR

(* ---------- helpers ---------- *)
(* SetAlarm: set/clear bit in dwAlarm *)
METHOD PRIVATE SetAlarm
VAR_INPUT iBit : INT; bOn : BOOL; END_VAR
    IF bOn THEN dwAlarm := dwAlarm OR SHL(DWORD#1, iBit); ELSE dwAlarm := dwAlarm AND NOT SHL(DWORD#1, iBit); END_IF;
END_METHOD

(* UnitsRequired: ceil(it_kw / (unit_kw*margin)) + redundancy, capped at installed *)
METHOD PRIVATE UnitsRequired : INT
VAR_INPUT rKw : REAL; END_VAR
    IF rKw > 0.0 THEN
        rN := rKw / (GVL_Plant.rUnitKw * KW_PER_UNIT_MARGIN);
        iN := REAL_TO_INT(rN); IF INT_TO_REAL(iN) < rN THEN iN := iN + 1; END_IF;
        IF iN < 1 THEN iN := 1; END_IF;
    ELSE iN := 1; END_IF;
    CASE GVL_Plant.iRedundancy OF 0: iExtra := 0; 2: iExtra := iN; ELSE iExtra := 1; END_CASE;
    UnitsRequired := MIN(GVL_Plant.nCooling, iN + iExtra);
END_METHOD

(* ============================== main body ============================== *)
MB.wHeartbeat := MB.wHeartbeat + 1;

(* ---- edge watchdog: advisory only. Loss changes nothing safety-relevant. *)
IF (NOT bEdgeSeen) OR (MB.wEdgeWatchdog <> wEdgeWdLast) THEN
    wEdgeWdLast := MB.wEdgeWatchdog; tEdgeWdAge := T#0s; bEdgeLost := NOT bEdgeSeen; bEdgeSeen := TRUE;
ELSE
    tEdgeWdAge := tEdgeWdAge + tCycle;
    IF tEdgeWdAge >= T_EDGE_WATCHDOG THEN bEdgeLost := TRUE; END_IF;
END_IF;
SetAlarm(ALM_EDGE_LOST, bEdgeLost);

(* ---- mode from the panel selector (the edge cannot change mode) *)
IF bHmiOff THEN iMode := MODE_OFF; ELSIF bHmiManual THEN iMode := MODE_MANUAL; ELSE iMode := MODE_AUTO; END_IF;

(* ---- life safety: MONITOR ONLY. No statement in this program writes anything toward the panel or the loop. *)
SetAlarm(ALM_EPO_LOOP_OPEN, NOT bEpoLoopOk);
SetAlarm(ALM_FIRE_ALARM, bFireAlarm);

(* ---- doors *)
FOR i := 1 TO GVL_Plant.nDoors DO
    IF abDoorOpen[i] THEN atDoorOpen[i] := atDoorOpen[i] + tCycle; ELSE atDoorOpen[i] := T#0s; END_IF;
END_FOR;
SetAlarm(ALM_DOOR_OPEN_LONG, FALSE);
FOR i := 1 TO GVL_Plant.nDoors DO IF atDoorOpen[i] >= T_DOOR_ALARM THEN SetAlarm(ALM_DOOR_OPEN_LONG, TRUE); END_IF; END_FOR;

(* ---- power supervision *)
SetAlarm(ALM_ATS_ON_GEN, bAtsOnGenerator);
SetAlarm(ALM_UPS24_ON_BATTERY, bUpsOnBattery);
SetAlarm(ALM_PSU_REDUNDANCY, NOT bPsuRedundancyOk);
(* generator: the ATS starts it; we only supervise. 0 off 1 starting 2 running 3 cooldown 4 fault *)
IF bGenFault THEN iGenState := 4;
ELSIF bGenRunning THEN iGenState := 2; tGenRun := tGenRun + tCycle; tGenSince := T#0s;
ELSIF NOT bUtilityOk THEN
    tGenSince := tGenSince + tCycle;
    IF tGenSince < T_GEN_START_FAIL THEN iGenState := 1; ELSE iGenState := 4; END_IF;
ELSE
    IF (tGenRun > T#0s) AND (tGenSince < T#5m) THEN iGenState := 3; ELSE iGenState := 0; tGenRun := T#0s; END_IF;
    tGenSince := tGenSince + tCycle;
END_IF;
SetAlarm(ALM_GEN_FAULT, iGenState = 4);

(* ---- leak isolation: HARDWIRED zones only (SeaHawk relays). A Pod 'leak' reading is advisory on the dashboard. *)
fbResetLeak(CLK := bHmiResetLeak);
bAnyIso := FALSE; bPumpStop := FALSE;
FOR i := 1 TO GVL_Plant.nZones DO
    IF fbResetLeak.Q THEN abValveCmd[i] := FALSE; abValveFault[i] := FALSE; END_IF;   (* manual, HMI only *)
    IF abLeakZone[i] AND NOT abValveCmd[i] THEN abValveCmd[i] := TRUE; atValveSince[i] := T#0s; END_IF;  (* latch *)
    IF abValveCmd[i] THEN
        bAnyIso := TRUE; atValveSince[i] := atValveSince[i] + tCycle;
        IF (NOT abValveClosedLs[i]) AND (atValveSince[i] >= T_VALVE_TRAVEL) THEN abValveFault[i] := TRUE; END_IF;
        IF abValveFault[i] AND abLeakZone[i] THEN bPumpStop := TRUE; END_IF;   (* valve failed, zone still wet *)
    END_IF;
    abValveClose[i] := abValveCmd[i];
END_FOR;
bCduPumpStop := bPumpStop;
SetAlarm(ALM_LEAK_ISOLATION, bAnyIso);
SetAlarm(ALM_VALVE_FAULT, FALSE);
FOR i := 1 TO GVL_Plant.nZones DO IF abValveFault[i] THEN SetAlarm(ALM_VALVE_FAULT, TRUE); END_IF; END_FOR;

(* ---- cooling N+1 sequencing and failover *)
fbResetLatched(CLK := bHmiResetLatched);
iNReq := UnitsRequired(rItKw);
FOR i := 1 TO GVL_Plant.nCooling DO
    IF fbResetLatched.Q THEN abUnitLatched[i] := FALSE; abUnitFaulted[i] := FALSE; END_IF;
    atSinceCmd[i] := atSinceCmd[i] + tCycle;
    IF abCoolCmd[i] AND abCoolRunFb[i] THEN atRunTime[i] := atRunTime[i] + tCycle; END_IF;
    (* fault: unit's own contact, or commanded with no run feedback inside the start window *)
    IF (abCoolFaultIn[i] OR (abCoolCmd[i] AND NOT abCoolRunFb[i] AND atSinceCmd[i] >= T_START_FEEDBACK))
       AND NOT abUnitFaulted[i] AND NOT abUnitLatched[i] THEN
        abUnitFaulted[i] := TRUE; atFaultSince[i] := T#0s;
        IF abCoolCmd[i] THEN wFailoverCount := wFailoverCount + 1; tLastFailover := T#0s; END_IF;
        abCoolCmd[i] := FALSE; atSinceCmd[i] := T#0s;
    ELSIF abUnitFaulted[i] THEN
        atFaultSince[i] := atFaultSince[i] + tCycle;
        IF (NOT abCoolFaultIn[i]) AND (atFaultSince[i] >= T_FAULT_RETRY) AND NOT abUnitLatched[i] THEN
            abUnitFaulted[i] := FALSE;
            abUnitLatched[i] := atRunTime[i] < T_MIN_RUN;    (* one retry; never ran properly -> latch until HMI reset *)
        END_IF;
    END_IF;
END_FOR;
IF tLastFailover < T#49d THEN tLastFailover := tLastFailover + tCycle; END_IF;

(* weekly lead rotation *)
tRotate := tRotate + tCycle;
IF tRotate >= T_ROTATE THEN tRotate := T#0s; iLead := iLead + 1; IF iLead > GVL_Plant.nCooling THEN iLead := 1; END_IF; END_IF;

(* choose units: lead first, round robin, skip faulted/latched *)
iNAvail := 0; FOR i := 1 TO GVL_Plant.nCooling DO IF NOT abUnitFaulted[i] AND NOT abUnitLatched[i] THEN iNAvail := iNAvail + 1; END_IF; END_FOR;
IF (iMode = MODE_AUTO) OR (iMode = MODE_TEST) THEN
    iChosen := 0;
    FOR k := 0 TO GVL_Plant.nCooling - 1 DO
        iIdx := ((iLead - 1 + k) MOD GVL_Plant.nCooling) + 1;
        bWant := (NOT abUnitFaulted[iIdx]) AND (NOT abUnitLatched[iIdx]) AND (iChosen < iNReq);
        IF bWant THEN iChosen := iChosen + 1; END_IF;
        IF bWant <> abCoolCmd[iIdx] THEN
            (* anti-short-cycle: don't stop a healthy unit that has run < T_MIN_RUN while capacity is satisfied *)
            IF (NOT bWant) AND (atRunTime[iIdx] < T_MIN_RUN) AND (atSinceCmd[iIdx] < T_MIN_RUN) AND (iChosen >= iNReq) THEN
                (* hold *)
            ELSE
                abCoolCmd[iIdx] := bWant; atSinceCmd[iIdx] := T#0s;
                IF bWant THEN atRunTime[iIdx] := T#0s; END_IF;
            END_IF;
        END_IF;
    END_FOR;
ELSIF iMode = MODE_OFF THEN
    FOR i := 1 TO GVL_Plant.nCooling DO abCoolCmd[i] := FALSE; END_FOR;
END_IF;   (* MANUAL: outputs frozen; the HMI drives them through forced variables *)
SetAlarm(ALM_COOL_CAPACITY_LOST, iNAvail < iNReq);
SetAlarm(ALM_ALL_UNITS_FAULTED, iNAvail = 0);

(* ---- edge setpoint trim: clamped, ignored when edge lost or not AUTO *)
iTrim := 0;
IF (NOT bEdgeLost) AND (iMode = MODE_AUTO) THEN iTrim := LIMIT(-TRIM_LIMIT_x10, MB.iSupplyTrim_x10, TRIM_LIMIT_x10); END_IF;
(* rSetpointOut := GVL_Plant.rSetpointC + INT_TO_REAL(iTrim)/10.0;  -> written to the lead unit over Modbus RTU in FB_CoolingModbus *)

(* ---- test requests from the edge: only AUTO, no alarm other than EDGE_LOST / ATS_ON_GEN, edge present *)
IF iTestActive <> 0 THEN
    tTestSince := tTestSince + tCycle;
    IF (iTestActive = 1) AND (tTestSince >= T#1s) THEN
        IF abCoolCmd[iLead] THEN abCoolCmd[iLead] := FALSE; atSinceCmd[iLead] := T#0s; wFailoverCount := wFailoverCount + 1; tLastFailover := T#0s; END_IF;
        iTestActive := 0;     (* the sequencer brings the standby in next scan *)
    ELSIF (iTestActive >= 2) AND (tTestSince >= T#1s) THEN
        iTestActive := 0;     (* UPS / generator tests are triggered on their own controllers (SNMP / ATS exerciser) *)
    END_IF;
ELSIF (MB.wTestRequest >= 1) AND (MB.wTestRequest <= 3) AND (iMode = MODE_AUTO) AND (NOT bEdgeLost)
      AND ((dwAlarm AND NOT (SHL(DWORD#1, ALM_EDGE_LOST) OR SHL(DWORD#1, ALM_ATS_ON_GEN))) = DWORD#0) THEN
    iTestActive := WORD_TO_INT(MB.wTestRequest); tTestSince := T#0s;
END_IF;
MB.wTestRequest := WORD#0;    (* consumed (or refused): always cleared *)

(* ---- hardware enable chain and beacon *)
bHealthy := ((iMode = MODE_AUTO) OR (iMode = MODE_TEST)) AND ((dwAlarm AND SHL(DWORD#1, ALM_ALL_UNITS_FAULTED)) = DWORD#0);
bCoolingEnable := bHealthy AND (iMode <> MODE_OFF) AND (iMode <> MODE_FAULT);
bBeacon := (dwAlarm AND NOT SHL(DWORD#1, ALM_EDGE_LOST)) <> DWORD#0;

(* ---- Modbus / OPC UA image (spec/PROTOCOL.md register map; same table as firmware/ben-plc/modbus_map.csv) *)
MB.wMode := INT_TO_WORD(iMode);                       (* Pro: bit 8 (LITE) is never set here *)
MB.wProjectCrc := GVL_Plant.wProjectCrc;
MB.wEdgeLost := BOOL_TO_WORD(bEdgeLost);
MB.wCoolCmd := WORD#0; MB.wCoolRun := WORD#0; MB.wCoolFault := WORD#0;
FOR i := 1 TO GVL_Plant.nCooling DO
    IF abCoolCmd[i] THEN MB.wCoolCmd := MB.wCoolCmd OR SHL(WORD#1, i - 1); END_IF;
    IF abCoolRunFb[i] THEN MB.wCoolRun := MB.wCoolRun OR SHL(WORD#1, i - 1); END_IF;
    IF abUnitFaulted[i] OR abUnitLatched[i] THEN MB.wCoolFault := MB.wCoolFault OR SHL(WORD#1, i - 1); END_IF;
END_FOR;
MB.wCoolLead := INT_TO_WORD(iLead); MB.wCoolNReq := INT_TO_WORD(iNReq); MB.wFailoverCnt := wFailoverCount;
MB.wLastFailoverS := INT_TO_WORD(MIN(65535, TIME_TO_INT(tLastFailover / 1000)));
MB.wLeakZone := WORD#0; MB.wIsoValveCmd := WORD#0; MB.wIsoValveClosed := WORD#0; MB.wIsoValveFault := WORD#0;
FOR i := 1 TO GVL_Plant.nZones DO
    IF abLeakZone[i] THEN MB.wLeakZone := MB.wLeakZone OR SHL(WORD#1, i - 1); END_IF;
    IF abValveCmd[i] THEN MB.wIsoValveCmd := MB.wIsoValveCmd OR SHL(WORD#1, i - 1); END_IF;
    IF abValveClosedLs[i] THEN MB.wIsoValveClosed := MB.wIsoValveClosed OR SHL(WORD#1, i - 1); END_IF;
    IF abValveFault[i] THEN MB.wIsoValveFault := MB.wIsoValveFault OR SHL(WORD#1, i - 1); END_IF;
END_FOR;
MB.wCduPumpStop := BOOL_TO_WORD(bCduPumpStop);
MB.wDoorState := WORD#0; MB.wDoorOpenS := WORD#0;
FOR i := 1 TO GVL_Plant.nDoors DO
    IF abDoorOpen[i] THEN MB.wDoorState := MB.wDoorState OR SHL(WORD#1, i - 1); END_IF;
    MB.wDoorOpenS := MAX(MB.wDoorOpenS, INT_TO_WORD(MIN(65535, TIME_TO_INT(atDoorOpen[i] / 1000))));
END_FOR;
MB.wEpoLoopOk := BOOL_TO_WORD(bEpoLoopOk);
MB.wFirePanel := BOOL_TO_WORD(bFireAlarm) OR SHL(BOOL_TO_WORD(bFireTrouble), 1) OR SHL(BOOL_TO_WORD(bFireReleased), 2) OR SHL(BOOL_TO_WORD(bFireSupervisory), 3);
IF bAtsOnGenerator THEN MB.wAtsSource := WORD#2; ELSIF bUtilityOk THEN MB.wAtsSource := WORD#1; ELSIF iGenState = 1 THEN MB.wAtsSource := WORD#3; ELSE MB.wAtsSource := WORD#0; END_IF;
MB.wGenState := INT_TO_WORD(iGenState); MB.wGenRunS := INT_TO_WORD(MIN(65535, TIME_TO_INT(tGenRun / 1000)));
MB.wUpsOnBattery := BOOL_TO_WORD(bUpsOnBattery); MB.wUtilityOk := BOOL_TO_WORD(bUtilityOk);
MB.wItKw_x10 := REAL_TO_WORD(rItKw * 10.0);
MB.iSupplyC_x10 := REAL_TO_INT(rSupplyC * 10.0); MB.iReturnC_x10 := REAL_TO_INT(rReturnC * 10.0);
MB.iOutdoorC_x10 := REAL_TO_INT(rOutdoorC * 10.0); MB.iAisleDp_x10 := REAL_TO_INT(rAisleDp * 10.0); MB.wRh_x10 := REAL_TO_WORD(rRh * 10.0);
(* MB.aiRtd_x100[] and MB.awAi_uA[] are filled by FB_AxiolineScale from the RTD4 / AI4 modules *)
MB.wAlarmWord := DWORD_TO_WORD(dwAlarm);
MB.wPsuRedundancyOk := BOOL_TO_WORD(bPsuRedundancyOk);
END_PROGRAM
