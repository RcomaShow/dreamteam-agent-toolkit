# Publishing

The GitHub connector used to generate this package could access existing repositories but could not create a new repository.

Create an empty repository named:

```text
RcomaShow/dreamteam-agent-toolkit
```

Then publish:

```bash
git init
git add .
git commit -m "Initial DreamTeam toolkit"
git branch -M main
git remote add origin https://github.com/RcomaShow/dreamteam-agent-toolkit.git
git push -u origin main
```

After publication, users can add the Claude Code marketplace from `RcomaShow/dreamteam-agent-toolkit`.

Before pushing, run the local validator and, when installed, the official Claude Code plugin validator.
