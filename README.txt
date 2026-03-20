GROCERY SHOP MANAGER — SETUP GUIDE
====================================

DEFAULT LOGIN DETAILS
----------------------
Admin (Mum):   username: admin   password: admin123
Staff (Worker): username: staff   password: staff123

Change these passwords after first login by editing app.py line 49-50.


HOW TO PUT IT ONLINE (FREE) — RAILWAY
=======================================

Step 1: Create accounts
- Go to github.com → Sign up (free)
- Go to railway.app → Sign up with your GitHub account

Step 2: Upload files to GitHub
- On github.com, click "New repository"
- Name it: shop-manager
- Click "Create repository"
- Upload ALL these files (drag and drop):
    app.py
    requirements.txt
    Procfile
    And the folders: templates/ and static/

Step 3: Deploy on Railway
- On railway.app, click "New Project"
- Click "Deploy from GitHub repo"
- Select your shop-manager repo
- Railway will build and deploy it automatically
- After a minute, click "Settings" → "Domains" → "Generate Domain"
- You get a link like: https://shop-manager-abc123.up.railway.app

Step 4: Share the link
- Mum bookmarks the link on her phone
- Worker bookmarks the link on her phone
- Both can access it anywhere with internet!


WHAT EACH ACCOUNT CAN DO
==========================
Admin (Mum):
  - Record sales
  - Add / edit / delete products
  - View all sales history
  - View daily reports
  - See low stock alerts
  - See top selling products

Staff (Worker):
  - Record sales only
  - See receipt after each sale


CHANGING PASSWORDS
===================
Open app.py, find lines 49-50:
  c.execute("INSERT INTO tblUsers VALUES (1, 'admin', 'admin123', 'Admin')")
  c.execute("INSERT INTO tblUsers VALUES (2, 'staff', 'staff123', 'Staff')")

Change admin123 and staff123 to your own passwords.
Then re-upload app.py to GitHub — Railway will redeploy automatically.


NEED HELP?
===========
WhatsApp or call the developer 😄
