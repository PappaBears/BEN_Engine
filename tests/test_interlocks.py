"""Interlock state machine — acceptance for both the Lite (Python) and Pro (structured text) controllers."""
from ben_engine import interlocks as il
from ben_engine.interlocks import Alarm, Inputs, Interlocks, Mode


def make(n=3, zones=2, doors=2, **kw):
    return Interlocks(n_cooling=n, unit_kw=30.0, n_leak_zones=zones, n_doors=doors, **kw)


def inputs(ctl: Interlocks, run_fb=None, **kw) -> Inputs:
    n = ctl.n
    x = Inputs(cooling_run_fb=run_fb if run_fb is not None else [False] * n,
               cooling_fault_in=[False] * n, leak_zone=[False] * ctl.n_zones,
               valve_closed_ls=[False] * ctl.n_zones, door_open=[False] * ctl.n_doors, **kw)
    return x


def run(ctl, x, seconds, dt=1.0, follow=True, wd=True):
    """Advance; by default units report RUN when commanded (ideal plant) and the edge watchdog ticks."""
    out = None
    for _ in range(int(seconds / dt)):
        if follow:
            x.cooling_run_fb = [c and not f for c, f in zip([u.cmd for u in ctl.units], x.cooling_fault_in)]
        if wd:
            x.edge_watchdog = (x.edge_watchdog + 1) & 0xFFFF
        out = ctl.step(x, dt)
    return out


def test_n_plus_1_sizing_from_load():
    ctl = make(n=3)
    assert ctl.units_required(0.0) == 2          # 1 + 1 standby
    assert ctl.units_required(40.0) == 3         # 40/(30*0.85)=1.57 -> 2 + 1
    assert ctl.units_required(100.0) == 3        # capped at installed units
    assert make(n=3, redundancy="N").units_required(40.0) == 2


def test_sequencer_commands_lead_first_and_rotates_weekly():
    ctl = make(n=3)
    x = inputs(ctl, it_kw=20.0)
    out = run(ctl, x, 5)
    assert out.cooling_cmd == [True, True, False]   # 1 required + 1 standby, lead = unit 1
    run(ctl, x, il.COOLING_ROTATE_S + 2, dt=3600)
    assert ctl.lead == 1
    assert ctl.last_outputs.cooling_cmd[1] is True


def test_failover_on_fault_contact_brings_standby_in():
    ctl = make(n=3)
    x = inputs(ctl, it_kw=20.0)
    run(ctl, x, il.COOLING_MIN_RUN_S + 5)
    assert ctl.last_outputs.cooling_cmd == [True, True, False]
    x.cooling_fault_in[0] = True
    out = run(ctl, x, 3)
    assert out.cooling_cmd == [False, True, True]
    assert ctl.failover_count == 1
    assert out.alarm(Alarm.COOLING_CAPACITY_LOST) is False   # still N+1 worth available? 2 of 3 healthy, need 2 -> ok
    assert out.cooling_enable_relay is True


def test_failover_on_missing_run_feedback():
    ctl = make(n=2)
    x = inputs(ctl, it_kw=10.0)
    # unit 1 never reports RUN
    for _ in range(int(il.COOLING_START_FEEDBACK_S) + 2):
        x.cooling_run_fb = [False, ctl.units[1].cmd]
        x.edge_watchdog += 1
        out = ctl.step(x, 1.0)
    assert ctl.units[0].faulted is True
    assert out.cooling_cmd == [False, True]
    assert out.alarm(Alarm.COOLING_CAPACITY_LOST) is True       # only 1 healthy, N+1 wants 2


def test_all_units_faulted_drops_enable_relay():
    ctl = make(n=2)
    x = inputs(ctl, it_kw=10.0)
    run(ctl, x, 5)
    x.cooling_fault_in = [True, True]
    out = run(ctl, x, 3)
    assert out.alarm(Alarm.ALL_UNITS_FAULTED)
    assert out.cooling_enable_relay is False                  # units revert to their own controllers
    assert out.cooling_cmd == [False, False]


def test_faulted_unit_retries_once_then_latches():
    ctl = make(n=2)
    x = inputs(ctl, it_kw=10.0)
    run(ctl, x, 5)
    x.cooling_fault_in[0] = True
    run(ctl, x, 3)
    x.cooling_fault_in[0] = False
    run(ctl, x, il.COOLING_FAULT_RETRY_S + 2)
    assert ctl.units[0].faulted is False and ctl.units[0].latched is True   # never ran >= MIN_RUN before fault -> latch
    ctl.reset_latched(0)
    assert ctl.units[0].latched is False


def test_leak_closes_zone_valve_and_latches_until_manual_reset():
    ctl = make(zones=2)
    x = inputs(ctl)
    x.leak_zone[1] = True
    out = run(ctl, x, 2)
    assert out.valve_close_cmd == [False, True]
    assert out.alarm(Alarm.LEAK_ISOLATION_ACTIVE)
    x.valve_closed_ls[1] = True
    x.leak_zone[1] = False
    out = run(ctl, x, 60)
    assert out.valve_close_cmd == [False, True]              # latched
    assert not out.alarm(Alarm.VALVE_FAULT)
    ctl.reset_leak(1)
    out = run(ctl, x, 1)
    assert out.valve_close_cmd == [False, False]


def test_valve_fault_with_persistent_leak_stops_cdu_pumps():
    ctl = make(zones=1)
    x = inputs(ctl)
    x.leak_zone[0] = True                                     # valve never reaches its limit switch
    out = run(ctl, x, il.VALVE_TRAVEL_S + 2)
    assert out.alarm(Alarm.VALVE_FAULT)
    assert out.cdu_pump_stop is True


def test_edge_loss_is_advisory_only():
    ctl = make(n=2)
    x = inputs(ctl, it_kw=10.0, supply_trim_k=1.5)
    out = run(ctl, x, 5)
    assert out.supply_setpoint_c == 21.5 and not out.alarm(Alarm.EDGE_LOST)
    out = run(ctl, x, il.EDGE_WATCHDOG_S + 2, wd=False)       # edge counter frozen
    assert out.alarm(Alarm.EDGE_LOST)
    assert out.supply_setpoint_c == 20.0                      # trim ignored
    assert out.cooling_cmd == [True, True]                    # sequencing continues
    assert out.cooling_enable_relay is True                   # hardware chain stays closed
    assert out.beacon is False                                # edge loss alone is not a field alarm


def test_trim_is_clamped():
    ctl = make(n=1)
    x = inputs(ctl, supply_trim_k=9.0)
    out = run(ctl, x, 3)
    assert out.supply_setpoint_c == 20.0 + il.SUPPLY_TRIM_LIMIT_K


def test_door_and_epo_are_monitor_only():
    ctl = make(doors=1)
    x = inputs(ctl)
    x.door_open[0] = True
    out = run(ctl, x, il.DOOR_ALARM_S + 1)
    assert out.alarm(Alarm.DOOR_OPEN_LONG)
    x.epo_loop_ok = False
    x.fire_alarm = True
    out = run(ctl, x, 1)
    assert out.alarm(Alarm.EPO_LOOP_OPEN) and out.alarm(Alarm.FIRE_ALARM)
    # nothing in Outputs can act on the loop; cooling continues as commanded by the sequencer
    assert out.cooling_enable_relay is True
    assert not hasattr(out, "epo_trip") and not hasattr(out, "release")


def test_generator_start_failure_is_detected():
    ctl = make()
    x = inputs(ctl, utility_ok=False)
    out = run(ctl, x, 10)
    assert ctl.gen_state == il.GenState.STARTING and not out.alarm(Alarm.GENERATOR_FAULT)
    out = run(ctl, x, il.GEN_START_FAIL_S)
    assert ctl.gen_state == il.GenState.FAULT and out.alarm(Alarm.GENERATOR_FAULT)
    x.gen_running = True
    x.ats_on_generator = True
    out = run(ctl, x, 5)
    assert ctl.gen_state == il.GenState.RUNNING and out.alarm(Alarm.ATS_ON_GENERATOR)
    assert ctl.ats_source(x) == il.AtsSource.GENERATOR


def test_failover_sweep_request_only_in_auto_without_alarms():
    ctl = make(n=2)
    x = inputs(ctl, it_kw=10.0)
    run(ctl, x, il.COOLING_MIN_RUN_S + 5)
    x.test_request = 1
    run(ctl, x, 3)
    assert ctl.failover_count == 1                            # lead was stopped once by the test
    ctl2 = make(n=2)
    y = inputs(ctl2, it_kw=10.0, test_request=1, mode_request=Mode.MANUAL)
    run(ctl2, y, 3)
    assert ctl2.failover_count == 0                           # refused in MANUAL


def test_mode_off_drops_everything():
    ctl = make(n=2)
    x = inputs(ctl, it_kw=10.0)
    run(ctl, x, 5)
    x.mode_request = Mode.OFF
    out = run(ctl, x, 2)
    assert out.cooling_cmd == [False, False] and out.cooling_enable_relay is False


def test_register_image_matches_protocol_map():
    ctl = make(n=3, zones=2, doors=2, lite=True)
    x = inputs(ctl, it_kw=25.3, supply_c=20.4, return_c=31.2, outdoor_c=-3.5, supply_trim_k=-0.7)
    run(ctl, x, 5)
    r = ctl.registers(x, project_crc=0xBEEF)
    assert r[40002] == int(Mode.AUTO) | 0x100                 # Lite flag
    assert r[40003] == 0xBEEF
    assert r[40010] == 0b011 and r[40013] == 1 and r[40014] == 2
    assert r[40050] == 253 and r[40051] == 204 and r[40052] == 312
    assert r[40053] == (-35) & 0xFFFF and r[40006] == (-7) & 0xFFFF
    assert r[40120] == ctl.alarm_word
    for a in (40001, 40005, 40020, 40021, 40032, 40040, 40041, 40121):
        assert a in r


def test_failsafe_table_lists_every_output():
    names = {row[0] for row in il.FAILSAFE_TABLE}
    out = make().step(inputs(make()), 1.0)
    assert names == {k for k in vars(out) if k != "alarm_word"}
