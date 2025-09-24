# Tasks Document

## Analysis Output Format Requirements

**Each analysis task must produce a structured output with clear deletion markings:**

- **KEEP**: Files that must never be deleted (critical files)
- **DELETE**: Files confirmed safe to delete with justification
- **REVIEW**: Files requiring manual review before deletion
- **UNKNOWN**: Files that need further analysis

**Subdirectory Requirements:** For directories containing subdirectories, analysis must drill down to each subdirectory level.

**File-by-File Analysis:** .spec-workflow/specs/file-cleanup-analysis/analysis-results must be generated for each file in the directory, including subdirectories.

**Git Commit Requirements:** After completing each task and marking it as [x], commit all changes to git with message format: "完成任务 [task-number] - [task-description]"

## Phase 1: Directory-by-Directory Analysis

- [x] 1.1. Analyze root directory files

  - Files: main.py, pyproject.toml, requirements.txt, README.md, LICENSE, etc.
  - Purpose: Identify entry points and critical configuration files
  - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and reasoning
  - _Leverage: Project configuration patterns_
  - _Requirements: 1.1_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer with expertise in Python project structure | Task: Analyze all files in the root directory to identify entry points, configuration files, and documentation that must never be deleted | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with detailed reasoning | Restrictions: Mark all configuration, entry point, and legal files as KEEP, handle missing files gracefully | Success: Every root file has clear deletion marking with justification | Instructions: Mark task in-progress, analyze root directory, mark complete when all files are categorized_
- [x] 1.2. Analyze /config directory

  - Files: logging.toml, logging_docker.toml, README.md
  - Purpose: Identify configuration files and their usage
  - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and reference evidence
  - _Leverage: Configuration file analysis patterns_
  - _Requirements: 1.1_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Configuration Management Specialist | Task: Analyze all files in /config directory to identify which configuration files are referenced by the application | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with reference evidence from code/docs | Restrictions: Check references in Python code and documentation, mark all config files as KEEP unless proven unused | Success: Every config file has clear deletion marking with reference evidence | Instructions: Mark in-progress, analyze config directory, mark complete when all files are categorized_
- [ ] 1.3. Analyze /tradingagents package (main source code)

  - **Subdirectory Analysis Required**: Break down into separate tasks for each subdirectory
  - Purpose: Map all Python module dependencies and imports
  - _Leverage: Python AST parsing, import analysis_
  - _Requirements: 1.2_

  - [x] 1.3.1. Analyze /tradingagents/agents/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and import dependencies
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Python Package Analyst | Task: Analyze tradingagents/agents directory to map module dependencies and identify unused agent modules | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with import/usage evidence | Success: Every agent module has clear deletion marking | Instructions: Mark in-progress, analyze agents directory, mark complete when all files are categorized_

  - [x] 1.3.2. Analyze /tradingagents/api/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and API endpoint usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: API Analyst | Task: Analyze tradingagents/api directory to identify active API endpoints and unused API modules | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with endpoint usage evidence | Success: Every API module has clear deletion marking | Instructions: Mark in-progress, analyze api directory, mark complete when all files are categorized_

  - [x] 1.3.3. Analyze /tradingagents/config/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and configuration references
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Configuration Analyst | Task: Analyze tradingagents/config directory to identify configuration modules and their usage | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with configuration usage evidence | Success: Every config module has clear deletion marking | Instructions: Mark in-progress, analyze config directory, mark complete when all files are categorized_

  - [x] 1.3.4. Analyze /tradingagents/dataflows/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and data flow dependencies
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Data Pipeline Analyst | Task: Analyze tradingagents/dataflows directory to map data processing dependencies | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with data flow usage evidence | Success: Every dataflow module has clear deletion marking | Instructions: Mark in-progress, analyze dataflows directory, mark complete when all files are categorized_

  - [x] 1.3.5. Analyze /tradingagents/graph/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and graph dependencies
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Graph Analysis Specialist | Task: Analyze tradingagents/graph directory to identify graph processing modules and dependencies | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with graph usage evidence | Success: Every graph module has clear deletion marking | Instructions: Mark in-progress, analyze graph directory, mark complete when all files are categorized_

  - [x] 1.3.6. Analyze /tradingagents/llm/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and LLM integration usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: LLM Integration Specialist | Task: Analyze tradingagents/llm directory to identify LLM integration modules and their usage | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with LLM usage evidence | Success: Every LLM module has clear deletion marking | Instructions: Mark in-progress, analyze llm directory, mark complete when all files are categorized_

  - [x] 1.3.7. Analyze /tradingagents/llm_adapters/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and adapter usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: LLM Adapter Specialist | Task: Analyze tradingagents/llm_adapters directory to identify adapter modules and their usage | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with adapter usage evidence | Success: Every adapter module has clear deletion marking | Instructions: Mark in-progress, analyze llm_adapters directory, mark complete when all files are categorized_

  - [x] 1.3.8. Analyze /tradingagents/tools/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and tool usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Tools Analysis Specialist | Task: Analyze tradingagents/tools directory to identify tool modules and their usage by agents | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with tool usage evidence | Success: Every tool module has clear deletion marking | Instructions: Mark in-progress, analyze tools directory, mark complete when all files are categorized_

  - [x] 1.3.9. Analyze /tradingagents/utils/ subdirectory
    - **Output Format**: List each .py file with KEEP/DELETE/REVIEW/UNKNOWN tag and utility function usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Utility Analysis Specialist | Task: Analyze tradingagents/utils directory to identify utility modules and their usage across the codebase | Output: For each .py file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with utility usage evidence | Success: Every utility module has clear deletion marking | Instructions: Mark in-progress, analyze utils directory, mark complete when all files are categorized_
- [ ] 1.4. Analyze /web directory (Streamlit web interface)

  - **Subdirectory Analysis Required**: Break down into separate tasks for each subdirectory
  - Purpose: Identify web-specific files and their usage patterns
  - _Leverage: Streamlit patterns, web framework analysis_
  - _Requirements: 1.2_

  - [x] 1.4.1. Analyze /web/components/ subdirectory
    - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and component usage evidence
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Streamlit Component Developer | Task: Analyze web/components directory to identify Streamlit components and their usage | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with component usage evidence | Success: Every component has clear deletion marking | Instructions: Mark in-progress, analyze components directory, mark complete when all files are categorized_

  - [-] 1.4.2. Analyze /web/config/ subdirectory
    - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and web config usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Web Configuration Specialist | Task: Analyze web/config directory to identify web configuration files and their usage | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with config usage evidence | Success: Every web config has clear deletion marking | Instructions: Mark in-progress, analyze web config directory, mark complete when all files are categorized_

  - [ ] 1.4.3. Analyze /web/data/ subdirectory
    - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and data file usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Web Data Analyst | Task: Analyze web/data directory to identify web data files and their usage | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with data usage evidence | Success: Every web data file has clear deletion marking | Instructions: Mark in-progress, analyze web data directory, mark complete when all files are categorized_

  - [ ] 1.4.4. Analyze /web/modules/ subdirectory
    - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and module usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Web Module Analyst | Task: Analyze web/modules directory to identify web modules and their usage | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with module usage evidence | Success: Every web module has clear deletion marking | Instructions: Mark in-progress, analyze web modules directory, mark complete when all files are categorized_

  - [ ] 1.4.5. Analyze /web/utils/ subdirectory
    - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and utility usage
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Web Utility Analyst | Task: Analyze web/utils directory to identify web utilities and their usage | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with utility usage evidence | Success: Every web utility has clear deletion marking | Instructions: Mark in-progress, analyze web utils directory, mark complete when all files are categorized_
- [x] 1.5. Analyze /tests directory

  - **Subdirectory Analysis Required**: Break down by version directories and individual test files
  - Purpose: Identify test files and match them to source code
  - **Output Format**: List each test file/directory with KEEP/DELETE/REVIEW/UNKNOWN tag and source mapping
  - _Leverage: Test naming patterns, source-test matching_
  - _Requirements: 1.2_

  - [x] 1.5.1. Analyze version-specific test directories (e.g., /tests/0.1.14/)
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Test Version Manager | Task: Analyze version-specific test directories to identify outdated test suites | Output: For each version directory, provide KEEP/DELETE/REVIEW/UNKNOWN tag with version relevance analysis | Success: Every version test directory has clear deletion marking | Instructions: Mark in-progress, analyze version test directories, mark complete when all are categorized_

  - [x] 1.5.2. Analyze /tests/integration/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Specialist | Task: Analyze integration test directory to identify active integration tests and their coverage | Output: For each test file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with integration coverage evidence | Success: Every integration test has clear deletion marking | Instructions: Mark in-progress, analyze integration tests, mark complete when all files are categorized_

  - [x] 1.5.3. Analyze individual test files in /tests/ root
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Unit Test Analyst | Task: Analyze individual test files to match them with corresponding source code modules | Output: For each test file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with source mapping evidence | Success: Every test file has clear deletion marking with source mapping | Instructions: Mark in-progress, analyze individual tests, mark complete when all files are categorized_
- [-] 1.6. Analyze /scripts directory

  - **Subdirectory Analysis Required**: Break down into separate tasks for each script category
  - Purpose: Identify utility scripts and their usage contexts
  - **Output Format**: List each script with KEEP/DELETE/REVIEW/UNKNOWN tag and usage evidence
  - _Leverage: Script analysis, dependency checking_
  - _Requirements: 1.2_

  - [x] 1.6.1. Analyze /scripts/deployment/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Deployment Specialist | Task: Analyze deployment scripts to identify active deployment processes and unused scripts | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with deployment usage evidence | Success: Every deployment script has clear deletion marking | Instructions: Mark in-progress, analyze deployment scripts, mark complete when all files are categorized_

  - [x] 1.6.2. Analyze /scripts/development/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Development Tools Specialist | Task: Analyze development scripts to identify active development utilities and unused tools | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with development usage evidence | Success: Every development script has clear deletion marking | Instructions: Mark in-progress, analyze development scripts, mark complete when all files are categorized_

  - [-] 1.6.3. Analyze /scripts/docker/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Docker Specialist | Task: Analyze Docker scripts to identify containerization utilities and unused Docker tools | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with Docker usage evidence | Success: Every Docker script has clear deletion marking | Instructions: Mark in-progress, analyze Docker scripts, mark complete when all files are categorized_

  - [ ] 1.6.4. Analyze /scripts/git/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Git Workflow Specialist | Task: Analyze Git scripts to identify version control utilities and unused Git tools | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with Git usage evidence | Success: Every Git script has clear deletion marking | Instructions: Mark in-progress, analyze Git scripts, mark complete when all files are categorized_

  - [ ] 1.6.5. Analyze /scripts/maintenance/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: System Maintenance Specialist | Task: Analyze maintenance scripts to identify system maintenance utilities and unused scripts | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with maintenance usage evidence | Success: Every maintenance script has clear deletion marking | Instructions: Mark in-progress, analyze maintenance scripts, mark complete when all files are categorized_

  - [ ] 1.6.6. Analyze /scripts/setup/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: System Setup Specialist | Task: Analyze setup scripts to identify installation and configuration utilities | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with setup usage evidence | Success: Every setup script has clear deletion marking | Instructions: Mark in-progress, analyze setup scripts, mark complete when all files are categorized_

  - [ ] 1.6.7. Analyze /scripts/validation/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Validation Specialist | Task: Analyze validation scripts to identify testing and validation utilities | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with validation usage evidence | Success: Every validation script has clear deletion marking | Instructions: Mark in-progress, analyze validation scripts, mark complete when all files are categorized_
- [ ] 1.7. Analyze /docs directory

  - Purpose: Identify documentation structure and cross-references
  - **Output Format**: List each doc file/directory with KEEP/DELETE/REVIEW/UNKNOWN tag and reference analysis
  - **Note**: Due to many subdirectories, analyze by major categories (e.g., agents/, architecture/, blog/, configuration/, etc.)
  - _Leverage: Markdown parsing, documentation analysis_
  - _Requirements: 1.2_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Writer with documentation analysis skills | Task: Analyze docs directory to identify which documentation files reference code, images, or other files | Output: For each doc file/directory, provide KEEP/DELETE/REVIEW/UNKNOWN tag with reference evidence | Restrictions: Parse markdown files for internal links, code references, and image references, identify outdated version-specific docs | Success: Every doc file has clear deletion marking with reference mapping | Instructions: Mark in-progress, analyze docs directory, mark complete when all docs are categorized_
- [ ] 1.8. Analyze /data directory

  - **Subdirectory Analysis Required**: Break down by data categories
  - Purpose: Identify data files and their generation/usage patterns
  - **Output Format**: List each data file/directory with KEEP/DELETE/REVIEW/UNKNOWN tag and usage type
  - _Leverage: Data file pattern analysis_
  - _Requirements: 1.2_

  - [ ] 1.8.1. Analyze /data/analysis_results/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Data Analysis Specialist | Task: Analyze analysis results to identify generated outputs vs important results | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with generation/usage evidence | Success: Every analysis result has clear deletion marking | Instructions: Mark in-progress, analyze analysis results, mark complete when all files are categorized_

  - [ ] 1.8.2. Analyze /data/cache/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Cache Management Specialist | Task: Analyze cache directory to identify cache files that can be safely deleted | Output: For each cache file, provide KEEP/DELETE/REVIEW/UNKNOWN tag (most cache files should be DELETE) | Success: Every cache file has clear deletion marking | Instructions: Mark in-progress, analyze cache files, mark complete when all files are categorized_

  - [ ] 1.8.3. Analyze /data/reports/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Report Analysis Specialist | Task: Analyze report directory to identify important reports vs outdated/generated reports | Output: For each report file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with importance assessment | Success: Every report has clear deletion marking | Instructions: Mark in-progress, analyze reports, mark complete when all files are categorized_

  - [ ] 1.8.4. Analyze /data/scripts/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Data Script Analyst | Task: Analyze data processing scripts to identify active vs unused data scripts | Output: For each script, provide KEEP/DELETE/REVIEW/UNKNOWN tag with usage evidence | Success: Every data script has clear deletion marking | Instructions: Mark in-progress, analyze data scripts, mark complete when all files are categorized_
- [ ] 1.9. Analyze /examples directory

  - Purpose: Identify example files and their educational value
  - **Output Format**: List each example file/directory with KEEP/DELETE/REVIEW/UNKNOWN tag and documentation references
  - _Leverage: Example code analysis, documentation references_
  - _Requirements: 1.2_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Developer Relations Engineer | Task: Analyze examples directory to identify which examples are referenced in documentation or still relevant | Output: For each example, provide KEEP/DELETE/REVIEW/UNKNOWN tag with documentation reference evidence | Restrictions: Check references in README, docs, and code comments, identify outdated examples | Success: Every example has clear deletion marking with reference tracking | Instructions: Mark in-progress, analyze examples directory, mark complete when all examples are categorized_
- [ ] 1.10. Analyze /assets directory

  - **Subdirectory Analysis Required**: Break down by asset categories
  - Purpose: Identify asset files and their usage in application
  - **Output Format**: List each asset with KEEP/DELETE/REVIEW/UNKNOWN tag and usage references
  - _Leverage: Asset reference analysis_
  - _Requirements: 1.2_

  - [ ] 1.10.1. Analyze /assets/cli/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: CLI Asset Specialist | Task: Analyze CLI assets to identify which assets are used by command-line interface | Output: For each asset, provide KEEP/DELETE/REVIEW/UNKNOWN tag with CLI usage evidence | Success: Every CLI asset has clear deletion marking | Instructions: Mark in-progress, analyze CLI assets, mark complete when all files are categorized_

  - [ ] 1.10.2. Analyze /assets/setup/ subdirectory
    - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Setup Asset Specialist | Task: Analyze setup assets to identify which assets are used in installation/setup processes | Output: For each asset, provide KEEP/DELETE/REVIEW/UNKNOWN tag with setup usage evidence | Success: Every setup asset has clear deletion marking | Instructions: Mark in-progress, analyze setup assets, mark complete when all files are categorized_
- [ ] 1.11. Analyze /images directory

  - Purpose: Identify image files referenced in documentation
  - **Output Format**: List each image with KEEP/DELETE/REVIEW/UNKNOWN tag and documentation references
  - _Leverage: Image reference analysis in markdown_
  - _Requirements: 1.2_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Writer specializing in documentation assets | Task: Analyze images directory to identify which images are referenced in README.md and documentation | Output: For each image, provide KEEP/DELETE/REVIEW/UNKNOWN tag with reference evidence | Restrictions: Parse all markdown files for image references, check for broken links, identify unused images | Success: Every image has clear deletion marking with reference tracking | Instructions: Mark in-progress, analyze images directory, mark complete when all images are categorized_
- [ ] 1.12. Analyze miscellaneous files

  - Files: .env.example, .gitignore, .python-version, VERSION, Dockerfile, docker-compose.yml, etc.
  - Purpose: Identify configuration and deployment files
  - **Output Format**: List each file with KEEP/DELETE/REVIEW/UNKNOWN tag and file type justification
  - _Leverage: DevOps file pattern analysis_
  - _Requirements: 1.1_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer with containerization expertise | Task: Analyze miscellaneous configuration files to ensure all deployment and environment files are preserved | Output: For each file, provide KEEP/DELETE/REVIEW/UNKNOWN tag with file type and importance justification | Restrictions: Mark all DevOps, CI/CD, and environment files as KEEP, verify Docker and deployment configurations | Success: Every miscellaneous file has clear deletion marking with justification | Instructions: Mark in-progress, analyze misc files, mark complete when all files are categorized_

## Phase 2: Cross-Reference Analysis and Validation

- [ ] 2.1. Build comprehensive deletion list from all analyses

  - Combine all directory analysis results to create master deletion list
  - Purpose: Create unified view of all files marked for deletion with justifications
  - **Output Format**: Master list with all DELETE-tagged files and their analysis justifications
  - _Leverage: Results from all directory analyses_
  - _Requirements: 1.3, 2.1_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Data Engineer specializing in file analysis consolidation | Task: Combine all directory analysis results into comprehensive deletion list showing all files marked as DELETE with justifications | Output: Master deletion list with file paths, reasons, and analysis sources | Restrictions: Include only files explicitly marked as DELETE, maintain traceability to original analysis | Success: Complete deletion list with accurate file identification and justifications | Instructions: Mark in-progress, build deletion list, mark complete when list is validated_

- [ ] 2.2. Implement safety validation for deletion list

  - Cross-check all DELETE-marked files against critical file patterns
  - Purpose: Prevent accidental deletion of important files
  - **Validation Rules**: Never delete config files, entry points, package files, or files with KEEP/REVIEW tags
  - _Leverage: Deletion list data, safety rule patterns_
  - _Requirements: 2.2, 2.3_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: System Administrator with safety validation expertise | Task: Create safety validator that prevents deletion of any critical files by reviewing all DELETE-tagged files | Output: Validated deletion list with safety approval or rejections | Restrictions: Never approve deletion of entry points, configs, or package files, flag any suspicious deletions as REVIEW | Success: Robust safety validation with detailed reasoning for each deletion approval/rejection | Instructions: Mark in-progress, implement validator, mark complete when all DELETE files are safety-validated_

## Phase 3: Execution and Cleanup

- [ ] 3.1. Execute file cleanup using validated deletion list

  - Delete only safety-validated files from the master deletion list
  - Purpose: Systematically remove unused files while maintaining complete safety
  - **Execution Method**: Process deletion list in batches by directory for better organization
  - _Leverage: Safety-validated deletion list_
  - _Requirements: 2.1, 2.2, 3.3_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: System Administrator executing production cleanup | Task: Execute cleanup by processing safety-validated deletion list systematically with detailed logging | Output: Deletion execution log with success/failure status for each file | Restrictions: Only delete files from validated deletion list, skip any files that fail safety re-check, handle errors gracefully | Success: Clean removal of all validated files with comprehensive logging | Instructions: Mark in-progress, execute cleanup, mark complete when all validated files are processed_

- [ ] 3.2. Generate comprehensive cleanup report

  - Document all deleted files with reasoning, statistics, and space savings
  - Purpose: Provide complete record of cleanup actions with before/after analysis
  - **Report Sections**: Summary statistics, deleted files by category, space savings, safety validations performed
  - _Leverage: Deletion execution logs, original analysis results_
  - _Requirements: 3.3_
  - _Prompt: Implement the task for spec file-cleanup-analysis, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Documentation Specialist | Task: Generate comprehensive cleanup report documenting all deletions with reasoning and impact analysis | Output: Detailed report with deletion summary, category breakdowns, space savings, and safety validation records | Restrictions: Include file purposes, deletion reasoning, validation results, and quantified impact | Success: Detailed report showing complete cleanup audit trail | Instructions: Mark in-progress, generate report, mark complete when comprehensive documentation is finished_
