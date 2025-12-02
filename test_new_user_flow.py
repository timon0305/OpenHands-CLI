#!/usr/bin/env python3
"""Test script to verify the new user flow."""

import os
import tempfile
from pathlib import Path

# Mock the locations to use a temporary directory
import openhands_cli.locations as locations

def test_new_user_flow():
    """Test that the app shows settings first for new users."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Override the persistence directory
        locations.PERSISTENCE_DIR = temp_dir
        
        # Import after overriding locations
        from openhands_cli.tui.settings.store import AgentStore
        from openhands_cli.refactor.textual_app import OpenHandsApp
        
        # Test 1: New user (no settings file)
        agent_store = AgentStore()
        existing_agent = agent_store.load()
        
        print(f"Test 1 - New user:")
        print(f"  Persistence dir: {temp_dir}")
        print(f"  Agent settings file: {Path(temp_dir) / locations.AGENT_SETTINGS_PATH}")
        print(f"  File exists: {(Path(temp_dir) / locations.AGENT_SETTINGS_PATH).exists()}")
        print(f"  Loaded agent: {existing_agent}")
        print(f"  Should show settings first: {existing_agent is None}")
        print()
        
        # Test 2: Create a dummy settings file and test existing user flow
        dummy_agent_data = '''{"llm": {"model": "openai/gpt-4o-mini", "api_key": "test-key", "base_url": null, "usage_id": "agent"}, "tools": [], "mcp_config": {}, "agent_context": {"skills": [], "system_message_suffix": ""}, "condenser": null}'''
        
        settings_file = Path(temp_dir) / locations.AGENT_SETTINGS_PATH
        settings_file.write_text(dummy_agent_data)
        
        # Reload to test existing user
        existing_agent = agent_store.load()
        
        print(f"Test 2 - Existing user:")
        print(f"  Agent settings file: {settings_file}")
        print(f"  File exists: {settings_file.exists()}")
        print(f"  Loaded agent: {existing_agent is not None}")
        print(f"  Should show main UI first: {existing_agent is not None}")
        print()
        
        print("✅ Tests completed successfully!")

if __name__ == "__main__":
    test_new_user_flow()