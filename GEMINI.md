# Project Mandates

- **DO NOT** remove the `data/` folder or any subdirectories within it (e.g., `data/output/`) under any circumstances, even if they appear to contain temporary or generated data.
- **SANDBOX ALL TESTS**: Automated tests MUST NEVER read from or write to the production `data/` or `config/` directories. All test file operations must use temporary directories (e.g., `pytest` tmp_path or `tempfile`) to prevent accidental deletion or corruption of user data.
- **NO DESTRUCTIVE CLEANUP**: Test cleanup logic must only delete files within their own temporary sandbox. Never include `os.remove()` or `shutil.rmtree()` calls that target the workspace's default `data` or `config` paths.
- Always use the `git restore` or `git checkout` commands immediately if any tracked files are accidentally deleted.
- Prioritize preserving the integrity of the `data/` directory over automated cleanup operations.
