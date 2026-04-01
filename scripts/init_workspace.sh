#!/bin/bash

# Initialize NewClaw workspace

WORKSPACE="$HOME/.new_claw"

echo "Initializing NewClaw workspace at $WORKSPACE"

# Create directory structure
mkdir -p "$WORKSPACE"
mkdir -p "$WORKSPACE/config"
mkdir -p "$WORKSPACE/skills"
mkdir -p "$WORKSPACE/agents"
mkdir -p "$WORKSPACE/memory/private"
mkdir -p "$WORKSPACE/memory/shared"
mkdir -p "$WORKSPACE/vector_db"
mkdir -p "$WORKSPACE/uploads"
mkdir -p "$WORKSPACE/tools"
mkdir -p "$WORKSPACE/plugins"

# Create default config.json
if [ ! -f "$WORKSPACE/config.json" ]; then
    cat > "$WORKSPACE/config.json" << 'EOF'
{
  "system": {
    "workspace": "~/.new_claw/",
    "log_level": "info"
  },
  "models": {
    "dialog": {
      "default": "ollama",
      "providers": {
        "ollama": {
          "api_url": "http://localhost:11434",
          "model": "qwen3.5:9b"
        }
      }
    },
    "embedding": {
      "default": "ollama",
      "providers": {
        "ollama": {
          "api_url": "http://localhost:11434",
          "model": "nomic-embed-text"
        }
      }
    }
  },
  "memory": {
    "vector_db": "chroma",
    "storage_path": "~/.new_claw/vector_db/",
    "async_indexing": true,
    "batch_size": 100
  },
  "plugins": {
    "enabled": true,
    "path": "~/.new_claw/plugins/"
  },
  "directories": {
    "skills": "~/.new_claw/skills/",
    "agents": "~/.new_claw/agents/",
    "memory": "~/.new_claw/memory/",
    "uploads": "~/.new_claw/uploads/",
    "tools": "~/.new_claw/tools/"
  }
}
EOF
    echo "Created config.json"
fi

# Create default Agent files template
create_default_agent() {
    local agent_dir="$WORKSPACE/agents/default"
    mkdir -p "$agent_dir"

    cat > "$agent_dir/AGENTS.md" << 'EOF'
# Agent Configuration

## Basic Info
- Name: Default Dialog Agent
- Description: Default dialog agent with basic capabilities

## Model Configuration
- Dialog Model: ollama/qwen3.5:9b
- Embedding Model: ollama/nomic-embed-text
EOF

    cat > "$agent_dir/SOUL.md" << 'EOF'
# Agent Soul

## Role Definition
You are a helpful AI assistant.

## Personality
- Friendly and professional
- Clear and concise responses
- Helpful and knowledgeable

## Behavior Constraints
- Always prioritize user privacy
- Follow ethical guidelines
- Provide accurate information
EOF

    cat > "$agent_dir/USER.md" << 'EOF'
# User Information

## Current User
- Username: [To be filled]
- Preferences: [To be filled]
- History: [To be filled]
EOF

    cat > "$agent_dir/MEMORY.md" << 'EOF'
# Memory Configuration

## Memory Rules
[User defined memory configuration]

## Important Notes
- Remember user preferences
- Track conversation context
EOF

    cat > "$agent_dir/HEARTBEAT.md" << 'EOF'
EOF

    # Create default agents.json with enabled_tools and enabled_skills
    cat > "$WORKSPACE/config/agents.json" << 'EOF'
{
  "default": {
    "name": "Default Dialog Agent",
    "description": "Default dialog agent with basic capabilities",
    "status": "active",
    "dialog_model": {
      "provider": "ollama",
      "model_name": "qwen3.5:9b"
    },
    "embedding_model": {
      "provider": "ollama",
      "model_name": "nomic-embed-text"
    },
    "enabled_tools": ["file_read", "file_write", "web_search", "command_exec"],
    "enabled_skills": [],
    "created_at": "2026-03-29T00:00:00Z"
  }
}
EOF

    echo "Created default agent"
}

if [ ! -d "$WORKSPACE/agents/default" ]; then
    create_default_agent
fi

echo "Workspace initialization complete!"
echo ""
echo "Directory structure:"
ls -la "$WORKSPACE"
