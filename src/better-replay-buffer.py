import obspython as obs
from pathlib import Path
from utils import *

replay_stopped_by_script = False

def script_description() -> str:
    return "A Python script that improves the quality of OBS' replay buffer.\n- Automatically clear the replay buffer when saved.\n- Save replay files to folders based on the process name.\n- System notification for when a replay is saved and where to.",

def obs_start_replay_buffer() -> None:
    '''Start the replay buffer if it is not started already.'''

    active = obs.obs_frontend_replay_buffer_active()
    if (not active):
        obs.obs_frontend_replay_buffer_start()

    obs.remove_current_callback()

def obs_get_saved_replay_path() -> str:
    '''
    Get the path for the file that the replay buffer was saved to.
    https://github.com/redraskal/obs-replay-folders/blob/main/OBSReplayFolders.lua#L30-L39
    '''

    replay_buffer = obs.obs_frontend_get_replay_buffer_output()
    calldata = obs.calldata_create()
    handler = obs.obs_output_get_proc_handler(replay_buffer)
    
    obs.proc_handler_call(handler, "get_last_replay", calldata)

    path = obs.calldata_string(calldata, "path")

    obs.calldata_destroy(calldata)
    obs.obs_output_release(replay_buffer)

    return path

def obs_frontend_callback(event: str) -> None:
    global replay_stopped_by_script

    # Save the file to a location based on the folder name and stop the buffer.
    # The buffer will restart after 500ms.
    if (event == obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED):
        replay_stopped_by_script = True

        process_name = get_folder_name(get_forground_process_name())
        saved_file = Path(obs_get_saved_replay_path())
        new_location = Path(saved_file.parent).joinpath(process_name, saved_file.name)

        if (not new_location.is_file()):
            move_file(saved_file, new_location)

        obs.obs_frontend_replay_buffer_stop()

        push_tray_notification(
            "OBS Replay Buffer",
            "Replay Buffer Saved",
            f"The replay buffer has been successfully saved to the folder \"{process_name}\" in your OBS videos folder."
        )

        return
    
    # Restart the buffer if it was stopped by the script.
    if (event == obs.OBS_FRONTEND_EVENT_REPLAY_BUFFER_STOPPED):
        if (not replay_stopped_by_script): return
        replay_stopped_by_script = False

        obs.timer_add(obs_start_replay_buffer, 500)
        return

def script_load(__settings__) -> None:
    obs.obs_frontend_add_event_callback(obs_frontend_callback)

def script_unload() -> None:
    obs.obs_frontend_remove_event_callback(obs_frontend_callback)