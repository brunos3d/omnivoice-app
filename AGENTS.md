@docs/.agents/README.md
@docs/.agents/CONSTITUTION.md

---

## Superpowers Integration Rules

This Project uses Superpowers workflows:

- Brainstorming
- Specification
- Design
- Tasks
- Validation
- Subagent Execution
- TDD

However, This Project overrides the default Superpowers filesystem layout.

Agents must NEVER create:

docs/superpowers/specs/
docs/superpowers/plans/
docs/superpowers/tasks/

Instead, use:

Specifications

docs/.agents/SPECS/FEATURES/<feature-name>/

Files:

SPEC.md
DESIGN.md
TASKS.md
VALIDATION.md
STATUS.md

---

Implementation Plans

docs/.agents/IMPLEMENTATION/PLANS/

Examples:

peakvox-phase-1-foundations.md
peakvox-phase-2-model-registry.md

---

Execution Tasks

docs/.agents/IMPLEMENTATION/TASKS/

Examples:

task-voice-source-assets.md
task-provider-validation.md

---

Validation Reports

docs/.agents/VALIDATION/

Examples:

provider-validations/
retrospectives/
audits/

---

Current Superpowers Session

docs/.agents/SDD/

CURRENT_SPEC.md
CURRENT_DESIGN.md
CURRENT_TASKS.md
CURRENT_VALIDATION.md

---

# MANDATORY RULE

When using any Superpowers skill:

- brainstorm
- specification
- design
- planning
- task generation
- validation
- subagent execution

the generated artifacts must be written into the This Project documentation architecture.

Never use the default Superpowers folders.

The This Project documentation architecture supersedes the default Superpowers layout.

---

# SPEC GENERATION RULE

Whenever a new feature is created, the agent must generate:

docs/.agents/SPECS/FEATURES/<feature-name>/

SPEC.md
DESIGN.md
TASKS.md
VALIDATION.md
STATUS.md

before implementation begins.

Implementation without a SPEC is prohibited.

---

# IMPLEMENTATION RULE

Every implementation task must reference:

- Related ADRs
- Related Architecture Documents
- Related Spec

before coding begins.

---

# VALIDATION RULE

Every completed feature must generate:

VALIDATION.md

inside the feature folder.

Validation is considered part of implementation.

---

# STATUS RULE

Every feature folder must contain:

STATUS.md

Allowed statuses:

NOT_STARTED
PLANNED
APPROVED
IN_PROGRESS
PARTIAL
IMPLEMENTED
VALIDATED
SUPERSEDED
ARCHIVED

This becomes the feature-level implementation state.
