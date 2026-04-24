# Development Guidelines

## Environment

These are custom Odoo 19.0 modules developed and deployed via **odoo.sh**.

The `odoo/` directory contains the Odoo Community source code and must not be modified. The Odoo Enterprise source modules have also been extracted into `odoo/addons/` and are available for reference, but must not be modified.

The `odoo_19.0+e.*.tar.gz` archive in the repository root is the upstream source distribution. Do not use it to inspect Community code; rely on the `odoo/` symlink or your knowledge of the framework. Only extract from the tar file when you need to inspect Enterprise addons that are not available through the symlink.

## Branching

All changes must be implemented on `feature/` or `fix/` branches. Never commit directly to `production`.

## Module Structure

Modules follow standard Odoo module layout:

- `__manifest__.py` — module metadata, version, and dependencies
- `models/` — Python model definitions
- `views/` — XML view definitions
- `security/` — access control rules (`ir.model.access.csv`)

## Testing

There is no local test runner. Testing requires a **commit and push** to the branch, which triggers an odoo.sh build. The build installs/upgrades the changed modules and runs them on a staging environment.

## Version Bumps

Every commit that modifies a module **must** bump the version number in that module's `__manifest__.py`. odoo.sh uses the version number to detect which modules need upgrading. If the version is not bumped, the changes will not be applied.
Always commit and push after bumping the version.

## Commit & Push

Only commit changes that belong to custom modules in the repository root.  
**Never commit anything inside the `odoo/` directory.** The `odoo/` path is a symlink to the upstream Odoo source (Community + Enterprise) and must remain untouched.

When ready to push:
1. Ensure you are on a `feature/` or `fix/` branch.
2. Stage only the files you have modified or created in the project root (e.g. `git add my_module/ AGENTS.md`).
3. Avoid running `git add odoo/` or `git commit -a` if changes exist inside `odoo/`.
4. Write a concise commit message, including the module name and a short description.
5. Push the branch to `origin` to trigger the odoo.sh build:
   ```bash
   git push origin feature/my-branch-name
   ```
