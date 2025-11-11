"""
UNDARK ↔ PBV Ftrack Sync Tool
----------------------------------
Synchronizes Tasks, Notes, and AssetVersions between two ftrack servers.
Enhanced with detailed logging and defensive error handling.
"""

import os
import threading
import logging
import functools
import time
from dotenv import load_dotenv
import ftrack_api


# --- Logging Configuration ---
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("undark_pbv_sync")


# --- Load Environment ---
load_dotenv()

PBV_FTRACK_API_KEY = os.getenv("FTRACK_API_KEY")
PBV_FTRACK_API_USER = os.getenv("FTRACK_API_USER")
PBV_FTRACK_API_URL = os.getenv("FTRACK_SERVER")

UNDARK_FTRACK_API_KEY = os.getenv("UNDARK_FTRACK_API_KEY")
UNDARK_FTRACK_API_USER = os.getenv("UNDARK_FTRACK_API_USER")
UNDARK_FTRACK_API_URL = os.getenv("UNDARK_FTRACK_API_URL")


# --- Helper Functions ---
def get_ftrack_session(api_key, api_user, api_url):
    logger.info("Connecting to ftrack server: %s as %s", api_url, api_user)
    try:
        session = ftrack_api.Session(
            api_key=api_key,
            api_user=api_user,
            server_url=api_url,
            auto_connect_event_hub=True,
        )
        logger.info("Connected successfully to %s", api_url)
        return session
    except Exception as e:
        logger.critical("Failed to connect to %s: %s", api_url, e)
        raise


def _escape(value):
    if isinstance(value, str):
        return value.replace('"', '\\"')
    return value


def _get(entity, key, default=None):
    try:
        if hasattr(entity, "get"):
            return entity.get(key, default)
        return entity[key]
    except Exception:
        return default


def _safe_str(value):
    try:
        return str(value)
    except Exception:
        return "<unprintable>"


def _resolve_entity_type(entity):
    return (entity.get("entity_type") or entity.get("entityType") or "").lower()


def _resolve_action(entity):
    return (entity.get("action") or entity.get("operation") or "").lower()


def _resolve_note_id(entity):
    return entity.get("entityId") or entity.get("id")


# --- Task Sync ---
def handle_task_creation(entity, session_pbv, session_undark):
    task_id = entity.get("entityId")
    if not task_id:
        return

    try:
        logger.info("[TASK SYNC] Checking for new task %s on PBV...", task_id)
        task = session_pbv.query(f'Task where id is "{task_id}"').first()
        if not task:
            logger.warning("[TASK SYNC] Task %s not found on PBV.", task_id)
            return

        name = task["name"]
        if "asset-request" not in name.lower():
            logger.debug("[TASK SYNC] Task %s is not an 'asset-request'; skipping.", name)
            return

        project_name = task["project"]["name"]
        logger.info("[TASK SYNC] Syncing '%s' in project '%s'...", name, project_name)

        target_project = session_undark.query(
            f'Project where name is "{_escape(project_name)}"'
        ).first()
        if not target_project:
            logger.warning("[TASK SYNC] Target project not found on UNDARK: %s", project_name)
            return

        existing = session_undark.query(
            f'Task where name is "{_escape(name)}" and parent.id is "{target_project["id"]}"'
        ).first()
        if existing:
            logger.info("[TASK SYNC] Task '%s' already exists on UNDARK.", name)
            return

        new_task = session_undark.create("Task", {"name": name, "parent": target_project})
        session_undark.commit()
        logger.info("[TASK SYNC] Created task '%s' (id=%s) on UNDARK.", name, new_task["id"])

    except Exception as e:
        logger.exception("[TASK SYNC] Error syncing task: %s", e)


# --- Note Sync ---
def handle_note_creation(entity, session_pbv, session_undark):
    note_id = _resolve_note_id(entity)
    action = _resolve_action(entity)
    logger.info("[NOTE SYNC] Event received: id=%s action=%s", note_id, action)

    if not note_id or action != "add":
        return

    try:
        # Determine which server has the note
        note_pbv = session_pbv.query(f'Note where id is "{note_id}"').first()
        note_undark = session_undark.query(f'Note where id is "{note_id}"').first()

        if note_pbv and note_undark:
            logger.info("[NOTE SYNC] Note already exists on both servers.")
            return

        source, target = (session_pbv, session_undark) if note_pbv else (session_undark, session_pbv)
        source_name, target_name = ("PBV", "UNDARK") if note_pbv else ("UNDARK", "PBV")
        source_note = note_pbv or note_undark
        logger.info("[NOTE SYNC] Source=%s Target=%s", source_name, target_name)

        # Populate parent
        source.populate(source_note, ["parent", "parent.project"])
        parent = _get(source_note, "parent")
        if not parent:
            logger.warning("[NOTE SYNC] No parent found for note %s; skipping.", note_id)
            return

        project_name = _get(parent["project"], "name")
        task_name = _get(parent, "name")

        logger.debug("[NOTE SYNC] Parent project=%s task=%s", project_name, task_name)

        # Find matching project/task on target
        target_project = target.query(f'Project where name is "{_escape(project_name)}"').first()
        if not target_project:
            logger.warning("[NOTE SYNC] Project not found on %s: %s", target_name, project_name)
            return

        target_task = target.query(
            f'Task where name is "{_escape(task_name)}" and project.id is "{target_project["id"]}"'
        ).first()
        if not target_task:
            logger.warning("[NOTE SYNC] Task not found on %s: %s", target_name, task_name)
            return

        # Build payload
        note_payload = {
            "parent": target_task,
            "content": _get(source_note, "content") or "",
            "subject": _get(source_note, "subject") or "",
            "metadata": {"synced_from": source_name},
        }

        # Author resolution
        author = _get(source_note, "user") or _get(source_note, "author")
        if author:
            username = _get(author, "username") or _get(author, "name")
            found = target.query(f'User where username is "{_escape(username)}"').first()
            if found:
                note_payload["author"] = found
                logger.debug("[NOTE SYNC] Author mapped to %s", username)
            else:
                logger.warning("[NOTE SYNC] Author %s not found on target.", username)

        # Avoid setting unsupported attributes like 'recipients'
        schema = target.types["Note"]
        if "recipients" in schema.keys():
            logger.debug("[NOTE SYNC] Recipients supported; adding fallback recipients.")
            note_payload["recipients"] = [note_payload.get("author")] if note_payload.get("author") else []

        logger.info("[NOTE SYNC] Creating note on %s: %s", target_name, note_payload)
        target.create("Note", note_payload)
        target.commit()
        logger.info("[NOTE SYNC] SUCCESS: Synced note '%s' to %s.", _safe_str(note_payload["content"])[:50], target_name)

    except Exception as e:
        logger.exception("[NOTE SYNC] Failed to sync note %s: %s", note_id, e)


# --- Version Sync ---
def handle_version_creation(entity, session_pbv, session_undark):
    version_id = entity.get("entityId")
    if not version_id:
        return

    logger.info("[VERSION SYNC] Version ID: %s", version_id)

    pbv_ver = session_pbv.query(f'AssetVersion where id is "{version_id}"').first()
    undark_ver = session_undark.query(f'AssetVersion where id is "{version_id}"').first()

    if not pbv_ver and not undark_ver:
        logger.warning("[VERSION SYNC] Version %s not found anywhere.", version_id)
        return

    source, target = (session_pbv, session_undark) if pbv_ver else (session_undark, session_pbv)
    src_name, tgt_name = ("PBV", "UNDARK") if pbv_ver else ("UNDARK", "PBV")
    version = pbv_ver or undark_ver

    asset = version["asset"]
    project_name = asset["project"]["name"]
    asset_name = asset["name"]
    version_name = version["name"]

    logger.info("[VERSION SYNC] %s → %s: %s / %s / %s", src_name, tgt_name, project_name, asset_name, version_name)

    tgt_project = target.query(f'Project where name is "{_escape(project_name)}"').first()
    if not tgt_project:
        logger.warning("[VERSION SYNC] Project not found on %s: %s", tgt_name, project_name)
        return

    tgt_asset = target.query(
        f'Asset where name is "{_escape(asset_name)}" and project.id is "{tgt_project["id"]}"'
    ).first()
    if not tgt_asset:
        logger.warning("[VERSION SYNC] Asset not found on %s: %s", tgt_name, asset_name)
        return

    exists = target.query(
        f'AssetVersion where name is "{_escape(version_name)}" and asset.id is "{tgt_asset["id"]}"'
    ).first()
    if exists:
        logger.info("[VERSION SYNC] Version already exists on %s: %s", tgt_name, version_name)
        return

    target.create("AssetVersion", {"name": version_name, "asset": tgt_asset})
    target.commit()
    logger.info("[VERSION SYNC] SUCCESS: Created %s on %s.", version_name, tgt_name)


# --- Event Dispatcher ---
def sync_event_handler(session_pbv, session_undark, event):
    logger.debug("[EVENT] Raw event data: %s", event)
    for entity in event["data"].get("entities", []):
        action = _resolve_action(entity)
        etype = _resolve_entity_type(entity)
        logger.debug("[EVENT] Entity=%s Action=%s", etype, action)

        if etype == "task" and action == "add":
            handle_task_creation(entity, session_pbv, session_undark)
        elif etype == "note" and action == "add":
            handle_note_creation(entity, session_pbv, session_undark)
        elif etype == "assetversion" and action == "add":
            handle_version_creation(entity, session_pbv, session_undark)


# --- Registration ---
def register(session_pbv):
    logger.info("Registering event listeners...")
    session_undark = get_ftrack_session(
        UNDARK_FTRACK_API_KEY, UNDARK_FTRACK_API_USER, UNDARK_FTRACK_API_URL
    )

    callback = functools.partial(sync_event_handler, session_pbv, session_undark)
    topics = ["ftrack.update", "ftrack.note"]

    for topic in topics:
        session_pbv.event_hub.subscribe(f"topic={topic}", callback)
        session_undark.event_hub.subscribe(f"topic={topic}", callback)
        logger.info("Subscribed to topic: %s", topic)

    # Background listener for UNDARK
    thread = threading.Thread(target=session_undark.event_hub.wait, daemon=True)
    thread.start()
    logger.info("UNDARK listener thread started.")


# --- Main ---
if __name__ == "__main__":
    logger.info("Starting UNDARK-PBV Sync Service...")
    pbv = get_ftrack_session(PBV_FTRACK_API_KEY, PBV_FTRACK_API_USER, PBV_FTRACK_API_URL)
    register(pbv)
    logger.info("Listening for PBV events...")
    pbv.event_hub.wait()
