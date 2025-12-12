ParkingDetection
===============

This is a Django-based parking detection project. Use Python 3.11 in a virtual environment.

Quick setup
-----------

- Create and activate a Python 3.11 venv:
  ```bash
  python3.11 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
  ```

GitHub / Push notes
-------------------
- Don't commit local virtual environments or large model files. Use Git LFS for model weights (`*.pt`).
- To create a remote repo and push (using `gh`):
  ```bash
  gh repo create <user>/ParkingDetection --public --source=. --remote=origin --push
  ```
  Or create a repo on GitHub and run:
  ```bash
  git remote add origin https://github.com/<user>/ParkingDetection.git
  git push -u origin main
  ```

If you want me to push the repo for you, tell me which option and auth method to use.
