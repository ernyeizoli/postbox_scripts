import ftrack_api
import os
import logging
from dotenv import load_dotenv
import functools # Required to pass the session correctly
import time 

# --- Configuration ---
# Loads credentials from your .env file
load_dotenv()

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tasks_for_new_shot(session, event):
    """
    Listens for ftrack.update events and creates default tasks
    when a new 'Shot' type is created.
    """
    logger.info("--- Event received, processing entities... ---")
    
    # We iterate through all entities in the event payload
    for entity in event['data'].get('entities', []):
        
        logger.info(f"Inspecting entity: {entity.get('entity_type')} with action: {entity.get('action')}")

        # This logic is based on the event data we discovered:
        # We look for a new entity ('action': 'add') that is a Shot.
        if (entity.get('action') == 'add' and 
            entity.get('entity_type') == 'Shot'):

            shot_id = entity.get('entityId')
            if not shot_id:
                logger.warning("Found a new Shot entity but it had no ID. Skipping.")
                continue

            logger.info(f"MATCH! New Shot detected with ID: {shot_id}. Fetching details...")
            
            shot_object = None
            # Retry logic to handle potential database commit delays
            for i in range(5): # Try up to 5 times
                # We query for 'Task' as confirmed by the event payload
                shot_object = session.get('Shot', shot_id)
                if shot_object:
                    logger.info(f"Successfully fetched ftrack object on attempt {i+1}. Object Name: '{shot_object['name']}'")
                    break  # Exit the loop if we found the object
                
                logger.warning(f"Attempt {i+1}: Shot object not found yet. Retrying in 1 second...")
                time.sleep(1) # Wait for 1 second before trying again

            if not shot_object:
                logger.error(f"Failed to fetch details for shot {shot_id} after multiple attempts. Aborting for this entity.")
                continue # Move to the next entity in the event

            try:
                project = shot_object['project']
                logger.info(f"Found parent project: '{project['full_name']}'")
                
                # --- Define your task template here ---
                task_names = ['Animation', 'Lighting', 'Compositing']
                
                # NEW: Get the specific Status and Priority objects once
                status = session.query('Status where name is "Not Started"').first()
                priority = session.query('Priority where name is "None"').first()

                if not status:
                    logger.warning("Could not find Status 'Not Started'. Tasks will be created with the default status.")
                if not priority:
                    logger.warning("Could not find Priority 'None'. Tasks will be created with the default priority.")

                logger.info(f"--- Starting Task Creation for Shot: '{shot_object['name']}' (ID: {shot_id}) ---")
                for task_name in task_names:
                    
                    # NEW: Find the Task Type that matches the task_name for each task
                    task_type = session.query(f'Type where name is "{task_name}"').first()

                    if not task_type:
                        logger.warning(f"Could not find a Task Type named '{task_name}'. Skipping creation of this task.")
                        continue # Skip to the next task name

                    logger.info(f"Attempting to create Task '{task_name}' with Type '{task_type['name']}'...")
                    
                    task = session.create('Task', {
                        'name': task_name,
                        'parent': shot_object,
                        'type': task_type,      # NEW: Set the specific type
                        'status': status,       # NEW: Set the status
                        'priority': priority    # NEW: Set the priority
                    })

                    session.commit()
                    logger.info(f"Created Task '{task['name']}' with Type '{task_type['name']}'")
                    logger.info(f"  -> SUCCESS! Created Task '{task['name']}' at Path: '{shot_object}'")
                
                logger.info("--- Finished Task Creation ---")

            except Exception as e:
                logger.exception(f"CRITICAL: An error occurred while processing shot ID {shot_id}. Error: {e}")


def register_event_listener(session):
    """Registers the event listener with the ftrack session."""
    
    callback_with_session = functools.partial(create_tasks_for_new_shot, session)
    
    session.event_hub.subscribe(
        'topic=ftrack.update', 
        callback_with_session
    )
    
    logger.info("Event listener registered. Waiting for new Shots via ftrack.update...")
    session.event_hub.wait()



def register(session):
    """Register the shot creation automation."""
    logger.info("Registering Shot Creation Automation...")
    callback_with_session = functools.partial(create_tasks_for_new_shot, session)
    session.event_hub.subscribe(
        'topic=ftrack.update',
        callback_with_session
    )
    logger.info("Shot Creation Automation registered.")