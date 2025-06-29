# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker-based Python monitoring application for server backup log checking. The application runs Python scripts as cron jobs to monitor backup logs across multiple servers and sends email notifications when issues are detected.

## Communication Rules

- Start every response with the 🤖 emoji
- Communicate in German language
- Always reference the PRD.md file for project requirements

## Architecture

The application follows a containerized architecture:

```
/app
├── config/          # Configuration files (YAML/JSON)
├── scripts/         # Python monitoring scripts
├── logs/           # Application logs
└── data/           # Mapped external directories
```

**Core Components:**
- **Cron Daemon**: Schedules and executes Python scripts
- **Python Scripts**: Log monitoring and analysis logic
- **SMTP Integration**: Email notification system
- **Volume Mapping**: Access to external log directories
- **Configuration Management**: Centralized YAML/JSON config

## Key Technical Requirements

- **Base Image**: python:3.11-slim for minimal footprint
- **Multi-stage Build**: Optimized Docker image size
- **Non-root User**: Security best practices
- **Signal Handling**: Proper container lifecycle management
- **Health Checks**: Container monitoring
- **Resource Efficiency**: Minimal CPU/memory usage

## Development Workflow

Follow the Code-Modifikations-Workflow from ClaudeRules.txt:

1. **Identify affected files**: Check project structure for relevant files
2. **Minimal intervention**: Plan only necessary changes
3. **Preservation principle**: Maintain existing functionality and interfaces
4. **Implementation**: Execute planned changes
5. **Verification**: Confirm changes don't break existing functions
6. **Documentation**: Update project documentation if needed

## Configuration Structure

The application uses centralized configuration for:
- Cron job definitions (schedules and Python scripts)
- SMTP settings (server, port, authentication)
- External directory paths
- Logging configuration

## Error Handling Requirements

- Robust error handling for mail sending failures
- Script execution error management
- Container restart resilience
- Comprehensive logging for troubleshooting

## Security Considerations

- Input validation for configuration files
- Secure SMTP authentication handling
- Non-root container execution
- Proper file permissions for mounted volumes

## Deliverables Structure

When implementing, ensure these components are created:
- Dockerfile with multi-stage build
- docker-compose.yml for deployment
- Configuration file templates
- Startup script for cron daemon and Python environment
- Example configurations for monitoring scenarios