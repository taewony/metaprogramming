# Cognitive Development Process – Reusable Skill

## Overview
This **SKILL** documents a repeatable procedure to:
1. Apply the `cognitive_dev_process` workflow to a repository.
2. Generate an interactive HTML dashboard (`cognitive_dev_process.html`) that visualises the stages:
   - **System Model → Implementation → Evaluation → Evidence → Insight → Decision → Next System Model**.
3. Make the entire setup portable so it can be copied into any other repository.

---

## Prerequisites
- **Node.js (>=18)** for the optional build step (for bundling CSS/JS). If you prefer a pure‑HTML file, you can skip the Node step.
- **Git** (optional, for committing the generated files).
- The repository must contain a **`cognitive_dev_process`** folder or any place where you keep the markdown artefacts that describe each stage.

---

## Step‑by‑Step Procedure
### 1️⃣ Prepare the Repository Structure
```text
repo_root/
├─ artifacts/                 # <-- place this SKILL.md here
├─ docs/                     # optional, for extra docs
├─ src/                      # your source code
└─ cognitive_dev_process/    # markdown files for each stage
    ├─ 01_system_model.md
    ├─ 02_implementation.md
    ├─ 03_evaluation.md
    ├─ 04_evidence.md
    ├─ 05_insight.md
    ├─ 06_decision.md
    └─ 07_next_system_model.md
```
- If the `cognitive_dev_process/` folder does not exist, create it and add a markdown file for each stage (the names above are conventional, but any naming works as long as the order is clear).

---

### 2️⃣ Create a Template for the Dashboard
Create `templates/dashboard_template.html` (any location you like; the script will copy it to the repo root as `cognitive_dev_process.html`). Below is a minimal template – you can extend it with your own branding:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cognitive Development Process</title>
  <style>
    body {font-family: 'Inter', sans-serif; margin:0; background:#f0f2f5; color:#333;}
    .stage {margin:2rem auto; max-width:800px; padding:1.5rem; background:#fff; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.1);}
    h2 {margin-top:0; color:#0066cc;}
  </style>
</head>
<body>
  <header style="background:#0066cc; color:#fff; padding:1rem; text-align:center;">
    <h1>Cognitive Development Process Dashboard</h1>
  </header>
  <main id="content"></main>
  <script>
    // Dynamically load each markdown file and render it as HTML.
    const stages = [
      "01_system_model.md",
      "02_implementation.md",
      "03_evaluation.md",
      "04_evidence.md",
      "05_insight.md",
      "06_decision.md",
      "07_next_system_model.md",
    ];
    const base = "cognitive_dev_process/";
    const container = document.getElementById("content");
    async function load() {
      for (const file of stages) {
        const resp = await fetch(base + file);
        const txt = await resp.text();
        const div = document.createElement("div");
        div.className = "stage";
        const title = file.replace(/_/g, " ").replace(/\.md$/, "");
        div.innerHTML = `<h2>${title}</h2><pre>${txt}</pre>`;
        container.appendChild(div);
      }
    }
    load();
  </script>
</body>
</html>
```
Save the file exactly as shown; the JavaScript simply fetches the markdown files in the same repo (served via a static web server or opened locally). For a richer UI you can replace the `<pre>` block with a markdown‑to‑HTML converter like **marked.js**.

---

### 3️⃣ Automation Script
Create a small Node script `scripts/generate_dashboard.js` (any location). This script copies the template, copies the markdown files into the repo root `cognitive_dev_process/` (if they aren’t already there), and optionally runs a minimal build.
```js
const fs = require('fs');
const path = require('path');

const repoRoot = process.cwd();
const templatePath = path.join(repoRoot, 'templates', 'dashboard_template.html');
const outPath = path.join(repoRoot, 'cognitive_dev_process.html');

// Copy template
fs.copyFileSync(templatePath, outPath);
console.log('✅ Dashboard HTML generated at', outPath);
```
Make it executable with `node scripts/generate_dashboard.js`.

---

### 4️⃣ Run the Generation
```bash
# From repo root
npm init -y   # if no package.json yet (optional)
npm install   # install any dependencies you later add
node scripts/generate_dashboard.js
```
The command creates `cognitive_dev_process.html`. Open it in a browser – you will see each stage rendered from the markdown files.

---

### 5️⃣ Propagate to Another Repository
1. **Copy the `cognitive_dev_process/` folder** (or rename it to fit your new repo’s conventions).
2. **Copy the `templates/` folder** and the `scripts/` folder (or just the script you need).
3. **Copy this SKILL.md** into the target repo’s `artifacts/` directory.
4. Run the script again in the new repo – the dashboard will be generated automatically.

---

## Tips & Best Practices
- **Version control**: Commit each markdown stage separately so you can trace the evolution of your thinking.
- **Naming convention**: Prefix files with numbers (01‑07) to guarantee ordering.
- **Styling**: Replace the minimal CSS with your brand’s design system (e.g., dark‑mode colors, glass‑morphism). The template is deliberately simple for easy customization.
- **Extensibility**: Add a “metadata.json” file inside `cognitive_dev_process/` that lists stage titles, timestamps, or responsible owners. The script can read this file to generate a table of contents.
- **Automation**: Hook the generation script into a Git hook (`post-commit`) or a CI pipeline so the HTML dashboard is always up‑to‑date.

---

## Summary
- **Create** `cognitive_dev_process/` with markdown files for each stage.
- **Add** a lightweight HTML template (`dashboard_template.html`).
- **Write** a Node script (`generate_dashboard.js`) that copies the template and produces `cognitive_dev_process.html`.
- **Run** the script; open the generated HTML to visualise the process.
- **Copy** the whole folder structure and this **SKILL.md** to any other repository to reuse the workflow.

You now have a portable, documented skill that turns the cognitive development process into an interactive web page across projects.
