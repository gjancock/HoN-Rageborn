import rageborn
import core.state as state
import utilities.constants as constant

def reset_state():
    state.STOP_EVENT.clear()
    state.SCAN_VOTE_EVENT.clear()
    state.SCAN_LOBBY_MESSAGE_EVENT.clear()
    state.INGAME_STATE.setCurrentMap(constant.MAP_FOC)
    state.INGAME_STATE.setCurrentTeam(constant.TEAM_LEGION)

def test_ingame():
    print("[TEST] Starting ingame() test only")
    reset_state()

    try:
        rageborn.ingame()
    except KeyboardInterrupt:
        print("[TEST] Interrupted by user")
    finally:
        state.STOP_EVENT.set()
        print("[TEST] Test finished")

if __name__ == "__main__":
    test_ingame()