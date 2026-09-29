# M Chavda Security World — Complete Starter

## Included
- Flask + SQLite login/register
- Password hashing
- Course and lesson system
- Persistent lesson progress
- Automatic course-completion certificate records
- PDF certificate generation
- Public certificate verification
- CTF learning area
- Admin dashboard
- Responsive UI

## Run locally
1. Install Python 3.10+.
2. `python -m venv .venv`
3. Activate the environment.
4. `pip install -r requirements.txt`
5. `python app.py`
6. Open `http://127.0.0.1:5000`

## Default admin
Email: chavdamohan965@gmail.com
Temporary password: ChangeMe123!
IMPORTANT: change this password and MCSW_SECRET before deployment.

## Important security architecture
Do NOT execute arbitrary Python/Java submitted by users directly inside the Flask web process.
For production, connect the coding runner to isolated containers/VMs with CPU, memory, filesystem,
network and time limits. Cybersecurity labs should likewise be isolated and restricted to authorized
practice targets.
