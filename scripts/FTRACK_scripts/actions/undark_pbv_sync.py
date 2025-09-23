# 1 needs to be included in the action server runner script (run_actions.py)
# 2 credentials for the UNDARK instance need to be added to the .env file
# 3 revision of name matching logic might be needed depending on your naming conventions
# 4 CURRENTLY it uses the code of the project not the NAME (FIX THIS)

import os
import logging
from dotenv import load_dotenv
import ftrack_api
import functools

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# --- Load environment variables ---
load_dotenv()

# --- FTRACK API credentials for both instances ---
PBV_FTRACK_API_KEY = os.getenv('FTRACK_API_KEY')
PBV_FTRACK_API_USER = os.getenv('FTRACK_API_USER')
PBV_FTRACK_API_URL = os.getenv('FTRACK_SERVER')

UNDARK_FTRACK_API_KEY = os.getenv('UNDARK_FTRACK_API_KEY')
UNDARK_FTRACK_API_USER = os.getenv('UNDARK_FTRACK_API_USER')
UNDARK_FTRACK_API_URL = os.getenv('UNDARK_FTRACK_API_URL')

def get_ftrack_session(api_key, api_user, api_url):
    return ftrack_api.Session(
        api_key=api_key,
        api_user=api_user,
        server_url=api_url,
        auto_connect_event_hub=True
    )

def sync_3d_task(session_pbv, session_undark, event):
    logger.info(f"Event received: {event}")
    entities = event['data'].get('entities', [])
    for entity in entities:
        logger.info(f"Inspecting entity: {entity.get('entity_type')} with action: {entity.get('action')}")
        if entity.get('action') == 'add' and entity.get('entity_type', '').lower() == 'task':
            task_id = entity.get('entityId')
            if not task_id:
                logger.warning("No task_id found in entity. Skipping.")
                continue
            task = session_pbv.query(f'Task where id is "{task_id}"').one()
            task_name = task['name']
            logger.info(f"Task created: {task_name}")

            if 'asset-request' in task_name.lower():
                project = task['project']
                project_name = project['name']
                logger.info(f"Detected 'asset-request' in task name. Project: {project_name}")

                # List all projects in session_undark
                projects_undark = session_undark.query('select name, id from Project').all()
                project_names_undark = [p['name'] for p in projects_undark]
                logger.info(f"Projects in target instance: {project_names_undark}")
                logger.info(f"Searching for project: {project_name}")

                target_project = next((p for p in projects_undark if p['name'] == project_name), None)
                if target_project:
                    logger.info(f"Found target project: {target_project['name']} ({target_project['id']})")
                    # Check for duplicate task
                    existing_task = session_undark.query(
                        f'Task where name is "{task_name}" and parent.id is "{target_project["id"]}"'
                    ).first()
                    if existing_task:
                        logger.info(f"Task '{task_name}' already exists in project '{project_name}' on target instance. Skipping creation.")
                    else:
                        new_task = session_undark.create('Task', {
                            'name': task_name,
                            'parent': target_project
                        })
                        session_undark.commit()
                        logger.info(f"Created task '{task_name}' in project '{project_name}' on target instance.")
                else:
                    logger.warning(f"Project '{project_name}' not found in target instance.")

def register(session_pbv):
    logger.info("Registering Undark PBV Sync listener...")
    logger.info(f"Undark Ftrack server URL: {UNDARK_FTRACK_API_URL}")
    session_undark = get_ftrack_session(UNDARK_FTRACK_API_KEY, UNDARK_FTRACK_API_USER, UNDARK_FTRACK_API_URL)
    callback = functools.partial(sync_3d_task, session_pbv, session_undark)

    session_pbv.event_hub.subscribe(
        'topic=ftrack.update', 
        callback
    )
    
    logger.info("Undark PBV Sync listener registered.")

if __name__ == '__main__':
    logger.info("Starting Undark PBV Sync as standalone process...")
    session_pbv = get_ftrack_session(PBV_FTRACK_API_KEY, PBV_FTRACK_API_USER, PBV_FTRACK_API_URL)
    register(session_pbv)
    logger.info("Waiting for task creation events...")
    session_pbv.event_hub.wait()