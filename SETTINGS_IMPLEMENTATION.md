# Agent Settings Implementation

This document describes the implementation of the new `AGENT SETTINGS` system command for the OpenHands CLI.

## Overview

The new settings system provides a modern, form-based interface for configuring agent settings, replacing the previous prompt-based approach. The settings screen overlays the entire UI and provides an intuitive way to configure:

- LLM Provider and Model selection
- API Key management
- Advanced settings (Custom Model, Base URL)
- Memory Condensation toggle

## Implementation Details

### Files Created/Modified

1. **`openhands_cli/refactor/settings_screen.py`** (NEW)
   - Main settings screen implementation using Textual's `ModalScreen`
   - Form-based UI with Select, Input, Checkbox, and Button widgets
   - Integration with existing `AgentStore` for persistence
   - Support for both Basic and Advanced configuration modes

2. **`openhands_cli/refactor/textual_app.py`** (MODIFIED)
   - Added `AGENT SETTINGS` system command
   - Added `action_open_settings()` method with conversation running check
   - Added import for `SettingsScreen`

### Key Features

#### 1. System Command Integration
- Added "AGENT SETTINGS" to the system commands palette (Ctrl+P)
- Accessible from anywhere in the application

#### 2. Conversation Running Check
- Settings screen is blocked when a conversation is running
- Shows user-friendly notification with warning severity
- Prevents configuration changes during active agent operations

#### 3. Modal Overlay Design
- Settings screen overlays the entire UI with semi-transparent background
- Centered modal container with proper styling
- Consistent with OpenHands theme colors

#### 4. Form-Based Configuration
The settings form adapts based on the selected mode:

**Basic Mode:**
- **Settings Mode**: Toggle between Basic and Advanced modes
- **LLM Provider**: Dropdown with 108+ verified and unverified providers (type-to-search enabled)
- **LLM Model**: Dynamic dropdown populated based on selected provider (type-to-search enabled)
- **API Key**: Secure password input with masked display
- **Memory Condensation**: Dropdown to enable/disable conversation summarization

**Advanced Mode:**
- **Settings Mode**: Toggle between Basic and Advanced modes
- **Custom Model**: Input for custom model names (e.g., gpt-4o-mini, claude-3-sonnet)
- **Base URL**: Input for custom API endpoints (e.g., https://api.openai.com/v1)
- **API Key**: Secure password input with masked display
- **Memory Condensation**: Dropdown to enable/disable conversation summarization

**Interface Benefits:**
- Clean, mode-specific interface showing only relevant fields
- Progressive field enabling based on dependency chain
- Type-to-search functionality in all dropdowns

#### 5. Data Persistence
- Integrates with existing `AgentStore` class
- Loads current settings on screen open
- Saves settings using the same persistence mechanism as the CLI
- Maintains compatibility with existing configuration files

#### 6. User Experience
- **Save Button**: Validates and saves settings, shows success message, auto-closes
- **Cancel Button**: Closes screen without saving changes
- **Escape Key**: Quick cancel using Escape key
- **Modal Screen Management**: Proper dismiss() handling prevents UI blocking
- **Settings Persistence**: Current values are displayed when screen is reopened
- **Agent Reload**: Main app automatically reloads agent after settings are saved
- **Success Notifications**: Clear feedback when settings are saved successfully
- **Real-time Validation**: Shows error messages for invalid inputs
- **Current Settings Display**: Shows masked API keys and current values
- **Dynamic UI**: Model options update based on provider selection
- **Field Dependencies**: Form fields are enabled/disabled based on prerequisite completion
- **Guided Setup**: Step-by-step form progression prevents incomplete configurations
- **Scrollable Interface**: Form content is fully scrollable when it exceeds screen height
- **Visual Scrollbar**: Styled scrollbar with hover effects for better visibility
- **Help Text**: Contextual help and explanations for configuration options

#### 7. Error Handling
- Graceful handling of missing or corrupted configuration files
- User-friendly error messages for validation failures
- Fallback to default settings when needed

## Usage

### Opening Settings
1. Press `Ctrl+P` to open the command palette
2. Type "AGENT SETTINGS" or select it from the list
3. Press Enter to open the settings screen

### Configuring Basic Settings
1. Select "Basic" mode (default)
2. Choose your LLM Provider from the dropdown (type to search through 108+ providers)
3. Select the desired Model (options update based on provider, type to search)
4. Enter your API Key
5. Toggle Memory Condensation if desired
6. Click "Save" to apply changes

#### Using Type-to-Search in Dropdowns
- Click or press Enter/Space/Arrow keys to open any dropdown
- Start typing the name of the option you want (e.g., "open" for OpenAI)
- The cursor will jump to the first matching option
- Continue typing to refine the search
- Press Enter to select the highlighted option

#### Field Dependency Chain
The form uses a guided setup approach where fields are enabled progressively:

**Basic Mode:**
1. **Settings Mode** → Always enabled (starting point)
2. **LLM Provider** → Enabled after mode selection
3. **LLM Model** → Enabled when provider is selected
4. **API Key** → Enabled when model is selected
5. **Memory Condensation** → Enabled when API key is provided

**Advanced Mode:**
1. **Settings Mode** → Always enabled (starting point)
2. **Custom Model** → Enabled in Advanced mode
3. **Base URL** → Enabled when custom model is entered
4. **API Key** → Enabled when custom model is entered
5. **Memory Condensation** → Enabled when API key is provided

This prevents incomplete configurations and guides users through the setup process step-by-step.

### Configuring Advanced Settings
1. Select "Advanced" mode
2. Enter a custom model name (e.g., "gpt-4o-mini")
3. Enter the base URL for your LLM provider
4. Enter your API Key
5. Toggle Memory Condensation if desired
6. Click "Save" to apply changes

### Canceling Changes
- Click "Cancel" or press `Escape` to close without saving

## Technical Architecture

### Screen Hierarchy
```
OpenHandsApp (main app)
├── Default Screen (main UI)
└── SettingsScreen (modal overlay)
    ├── Settings Form Container
    │   ├── Mode Selection
    │   ├── Provider/Model Selection (Basic)
    │   ├── Custom Model/Base URL (Advanced)
    │   ├── API Key Input
    │   └── Memory Condensation Toggle
    └── Button Container (Save/Cancel)
```

### Data Flow
1. User opens settings → `action_open_settings()` called
2. Check if conversation is running → Show notification if blocked
3. Create `SettingsScreen` instance → Load current settings from `AgentStore`
4. User modifies settings → Real-time validation and UI updates
5. User clicks Save → Validate inputs → Save to `AgentStore` → Close screen
6. User clicks Cancel → Close screen without saving

### Integration Points
- **AgentStore**: Existing settings persistence layer
- **LLM Models**: Uses SDK's `VERIFIED_MODELS` and `UNVERIFIED_MODELS_EXCLUDING_BEDROCK`
- **Theme**: Consistent with `OPENHANDS_THEME` colors and styling
- **Conversation Runner**: Checks `is_running` status before allowing access

## Benefits

1. **Modern UI**: Replaces command-line prompts with intuitive form interface
2. **Better UX**: Visual feedback, validation, error handling, and scrollable content
3. **Fast Search**: Type-to-search enabled for all dropdowns (108+ providers, models)
4. **Mode-Specific Interface**: Clean UI showing only relevant fields per mode
5. **Guided Setup**: Progressive field enabling prevents incomplete configurations
6. **Dropdown Controls**: Memory Condensation uses dropdown instead of checkbox for consistency
7. **Safety**: Prevents configuration changes during active conversations
8. **Accessibility**: Available from anywhere via system command palette, fully scrollable
9. **Consistency**: Matches existing UI patterns and theme
10. **Maintainability**: Reuses existing persistence and validation logic
11. **Responsive Design**: Adapts to different terminal sizes with proper scrolling

## Future Enhancements

Potential improvements that could be added:

1. **Settings Validation**: Real-time API key validation
2. **Provider Help**: Links to provider documentation
3. **Import/Export**: Configuration backup and restore
4. **Profiles**: Multiple configuration profiles
5. **Advanced Options**: Additional LLM parameters and settings

## Implementation Status ✅

**COMPLETED**: The AGENT SETTINGS system command has been successfully implemented with all requested features:

- ✅ **System Command**: `AGENT SETTINGS` opens settings screen overlay
- ✅ **Conversation Check**: Blocks access during running conversations with user notification
- ✅ **Modal Overlay**: Settings screen appears on top of current UI
- ✅ **Form Interface**: Mode-specific settings form with clean, adaptive UI
- ✅ **Type-to-Search**: All dropdowns support typing to quickly find options
- ✅ **Field Dependencies**: Progressive field enabling based on prerequisite completion
- ✅ **Mode-Specific Sections**: Basic and Advanced modes show only relevant fields
- ✅ **Dropdown Controls**: Memory Condensation uses dropdown for consistency
- ✅ **Save/Cancel**: Both actions automatically return to main UI and close settings screen
- ✅ **Screen Management**: Proper modal screen handling prevents UI blocking
- ✅ **Settings Persistence**: Current values displayed when screen is reopened
- ✅ **Agent Reload**: Main app reloads agent configuration after settings are saved
- ✅ **Keyboard Support**: Escape key for quick cancel, full keyboard navigation
- ✅ **Success Feedback**: Clear notifications when settings are saved
- ✅ **Scrolling Solution**: Fixed-size form elements with proper scrollable container
- ✅ **Integration**: Seamlessly works with existing AgentStore and settings infrastructure
- ✅ **Testing**: All components verified and working correctly

**UI ISSUES RESOLVED**: 
- **Scrolling**: Fixed vertical content overflow with proper container heights and scrollbar gutter
- **Screen Blocking**: Fixed modal screen management to prevent UI blocking after save/cancel
- **Settings Persistence**: Fixed settings not showing current values when screen is reopened
- **Memory Condensation**: Replaced checkbox with dropdown for consistency
- Form groups with minimum height to prevent shrinking
- All content accessible via scrolling regardless of terminal size