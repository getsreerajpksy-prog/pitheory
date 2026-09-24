# PiTheory Learning website

## How it works
- Each question is one small file in `content/questions/` (for example `11-03-017.json`).
- You add and edit questions in a form at **pitheory.in/admin**, with an upload button for diagrams.
- Every time you press Publish, GitHub rebuilds the site (about 1 minute) and it goes live.
- Every change is saved in history, so any mistake can be undone.

## Question IDs
`class-chapter-number`, for example `11-03-017` = Class 11, Chapter 3 (Motion in a Plane), question 17.
Never change an ID once published: it is part of the page address Google has indexed.

| Class 11 | | Class 12 | |
|---|---|---|---|
| 11-01 | Units and Measurements | 12-01 | Electric Charges and Fields |
| 11-02 | Motion in a Straight Line | 12-02 | Electrostatic Potential and Capacitance |
| 11-03 | Motion in a Plane | 12-03 | Current Electricity |
| 11-04 | Laws of Motion | 12-04 | Moving Charges and Magnetism |
| 11-05 | Work, Energy and Power | 12-05 | Magnetism and Matter |
| 11-06 | System of Particles and Rotational Motion | 12-06 | Electromagnetic Induction |
| 11-07 | Gravitation | 12-07 | Alternating Current |
| 11-08 | Mechanical Properties of Solids | 12-08 | Electromagnetic Waves |
| 11-09 | Mechanical Properties of Fluids | 12-09 | Ray Optics and Optical Instruments |
| 11-10 | Thermal Properties of Matter | 12-10 | Wave Optics |
| 11-11 | Thermodynamics | 12-11 | Dual Nature of Radiation and Matter |
| 11-12 | Kinetic Theory | 12-12 | Atoms |
| 11-13 | Oscillations | 12-13 | Nuclei |
| 11-14 | Waves | 12-14 | Semiconductor Electronics |

## Writing questions
- Maths between dollar signs: `$v = u + at$`. Centred equation: `$$ ... $$`. Check anything tricky at pitheory.in/admin/preview.html
- Diagram: upload in the Diagram field. It always appears at the end of the question, before the options. PNG or SVG, white background, about 800 px wide, file named with the question ID.
- Previous year question: write the exam and year in Source (`NEET 2023`, `JEE Main 2024 (27 Jan, Shift 1)`). It shows a PYQ badge.
- Numerical questions: JEE pattern only. Put the number in Numerical answer; Allowed error 0 for exact.
- Save as Draft while working. Change Status to Published when it is checked.

## Adding many questions at once
Fill `tools/questions-import-template.csv` in Excel, put diagram files in `static/diagrams/`, then:
`python3 tools/import_csv.py your-file.csv` and push. Questions come in as drafts unless status says published.

## Going live (one time, about 1 hour)
1. Create a free account at github.com. Create a new **private** repository named `pitheory`.
2. Upload everything in this folder to the repository (Add file > Upload files; include the hidden `.github` folder).
3. In `admin/config.yml`, replace `YOUR-GITHUB-USERNAME` with your GitHub username.
4. Repository Settings > Pages > Source: **GitHub Actions**. (Private repos need GitHub Pro for Pages; otherwise make the repo public, which is fine.)
5. Wait for the Actions tab to show a green tick. Settings > Pages > Custom domain: `pitheory.in`, tick Enforce HTTPS.
6. In GoDaddy > My Products > pitheory.in > DNS: delete the old A records for @, add four A records for @ pointing to 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153, and a CNAME `www` pointing to `YOUR-GITHUB-USERNAME.github.io`. This replaces the GoDaddy Website Builder page.
7. Admin login: GitHub > Settings > Developer settings > Fine-grained tokens > Generate. Only select the pitheory repository, Contents: Read and write. Open pitheory.in/admin, choose "Sign in with token", paste it. Keep the token private.
8. Google Search Console (already verified for pitheory.in): Sitemaps > add `sitemap.xml`.
9. Optional: create Google Analytics 4, paste the G- ID in Site settings in the admin.

## Checking a build
The Actions tab shows each build. The log lists question counts per chapter and any question that was skipped and why (missing option, wrong ID, missing diagram). Fix it in the admin and publish again.
