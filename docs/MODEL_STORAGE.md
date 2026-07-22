# Model Storage

Model weights are **never** stored inside the `cobra-core` git repository.

## External root

Default on Windows:

```text
D:\cobra-models
```

Override:

```text
set COBRA_MODEL_HOME=D:\cobra-models
```

## Layout

```text
%COBRA_MODEL_HOME%\
└── qwen\
    └── qwen3-8b\
        └── <pinned-revision>\
            ├── artifacts\       # Hub snapshot files
            ├── provenance\      # inventory, acquisition logs/reports
            ├── hashes\          # SHA256SUMS
            ├── quarantine\      # failed acquisitions
            └── download-state\  # resumable/state markers
```

Path resolution is centralized in `cobra_core.storage.paths`.

## Git policy

`.gitignore` blocks weight extensions and external model homes. Before every commit, confirm no `*.safetensors` / model directories are staged.
