import rageborn
import core.state as state
import utilities.constants as constant
import time

def reset_state():
    state.STOP_EVENT.clear()
    state.CRASH_EVENT.clear()
    state.SCAN_VOTE_EVENT.clear()
    state.SCAN_LOBBY_MESSAGE_EVENT.clear()
    state.INGAME_STATE.setCurrentMap(constant.MAP_FOC)
    #state.INGAME_STATE.setCurrentTeam(constant.TEAM_LEGION)

def test_ingame():
    print("[TEST] CURRENT STATE")
    time.sleep(5)
    #reset_state()

    try:
        from utilities.config import load_config
        # Load Config at startup
        load_config()
        # state.AUTO_START_ENDLESS 
        # state.AUTO_EMAIL_VERIFICATION
        # state.AUTO_MOBILE_VERIFICATION
        # state.AUTO_RESTART_DNS
        # state.SLOWER_PC_MODE
        # state.AUTO_UPDATE 
        # ---- Strings ----
        print(f"gamepath: {state.GAME_EXECUTABLE}")
        print(f"email_domain: {state.ACCOUNT_EMAIL_DOMAIN}")
        print(f"account password: {state.ACCOUNT_PASSWORD}")
        print(f"firstname: {state.ACCOUNT_FIRSTNAME}")
        print(f"lastname: {state.ACCOUNT_LASTNAME}")
        print(f"prefix: {state.USERNAME_PREFIX}")
        print(f"postfix: {state.USERNAME_POSTFIX}")
        
    except KeyboardInterrupt:
        print("[TEST] Interrupted by user")
    finally:
        state.STOP_EVENT.set()
        print("[TEST] Test finished")

if __name__ == "__main__":
    test_ingame()