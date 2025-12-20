# GitHub Push & Authentication Troubleshooting
## Linux + VS Code + SSH / HTTPS

This document is a complete, self-contained guide to diagnose and fix GitHub
push/authentication problems on Linux, especially when using VS Code
(local or Remote SSH / vscode-server).

---

## Common Errors

### VS Code askpass error
fatal: cannot run ~/.vscode-server/bin/<hash>/extensions/git/dist/askpass.sh

### Password authentication failure
remote: Invalid username or token.
Password authentication is not supported.

### SSH permission denied
git@github.com: Permission denied (publickey).

---

## Recommended Solution: SSH

### Check current remote
git remote -v

### Switch to SSH
git remote set-url origin git@github.com:USER/REPO.git

---

## SSH Setup

eval "$(ssh-agent -s)"
ssh-keygen -t ed25519 -C "your-label"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub

Add the public key to GitHub:
Settings → SSH and GPG keys → New SSH key

Test:
ssh -T git@github.com

---

## Fix Permission Denied

chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

Create ~/.ssh/config:

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes

---

## HTTPS + Token Alternative

Create a Personal Access Token (PAT)
Use token instead of password when pushing.

---

## Fix VS Code askpass Permanently

unset GIT_ASKPASS
unset SSH_ASKPASS
unset VSCODE_GIT_ASKPASS_NODE
unset VSCODE_GIT_ASKPASS_MAIN
unset VSCODE_GIT_ASKPASS_EXTRA_ARGS

Add the same lines to ~/.bashrc or ~/.zshrc

---

## Final Notes

SSH is the most stable solution on Linux and avoids all VS Code askpass issues.
