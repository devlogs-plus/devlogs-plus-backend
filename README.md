# Devlogs+
**Devlogs+** is a platform to share projects, devlogs, and proof of work (commits + time) publicly.

## **Features**

### **Projects**

- **Create / Edit projects**
    - Fields:
    - Name
    - Short description
    - WakaTime/Hackatime project(s)
    - Git repository
    - Demo link
    - Collaborators
- **Project page**
    - Shows all project fields
    - Shows all devlogs for the project
    - Comments (separate tab)

### **Devlogs**

- **Add devlogs to projects**
    - Only visible to project owners/collaborators
    - Supports Markdown
    - Automatically attaches time spent to the devlog (from WakaTime/Hackatime)

## **Integrations**

### **WakaTime / Hackatime**

- Connect account (OAuth)
- Import projects (select from a list)
- Constraint: one WakaTime project can’t be linked to multiple Devlogs+ projects

References:

- Hackatime OAuth apps: https://hackatime.hackclub.com/docs/oauth/oauth-apps
- WakaTime API docs: https://wakatime.com/developers

### **Git providers**

- Connect provider: GitHub / GitLab / Bitbucket
- Add repositories via provider API
- Attach commits to a devlog

References:

- GitHub Apps overview: https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps
- GitLab OAuth provider: https://docs.gitlab.com/integration/oauth_provider/
- Bitbucket REST API: https://developer.atlassian.com/cloud/bitbucket/rest/intro/#oauth-2-0

## **Social**

- Feed of devlogs + projects
- Follow people (email updates)
- Topics (pick interests)
- Comment on projects
- Themes (preset + custom)
- Sharing links (project/devlog)
- Collaboration
