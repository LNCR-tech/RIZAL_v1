# Repository Instructions

- For every backend code change under `backend/`, update the documentation in `docs/backend/`.
- Update any affected backend guide with the changed logic, routes, schemas, models, migrations, or configuration.
- If a backend change affects runtime behavior, document how to test it.
- Do not implement hardcoded answers or preset question-to-answer mappings for chat. Responses must be generated from model reasoning based on the user's prompt and available context.
- for every changes made do git add -A, git commit -m. you decide whatever commit message to say. then git push
- if a git push doesn't work, git pull --rebase and fix if there are any merge conflicts, ask the user which one to pick, then git push again
- When git merging, ensure that ONLY the `pilot` branch has the `seeder/` folder. It MUST NOT be present in `preproduction` or `production` branches.
