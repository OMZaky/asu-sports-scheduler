# ASU Sports Scheduler ⚽

A full-stack web application designed to collect availability from sports teams and programmatically generate a fair, conflict-free tournament schedule for both Group Stages and Knockout Stages.

## Features ✨
* **Interactive Next.js Frontend:** A beautiful, responsive "Day Stack" time-grid for teams to submit their availability. Features premium animations (Framer Motion) and a custom 60fps physics engine for interactive background footballs.
* **Direct Supabase Integration:** Teams submit their `Team Name`, `Captain Name`, and available `Slots` directly to a secure PostgreSQL database.
* **Algorithmic Scheduling (`algorithm.py`):**
  * Automatically sorts teams into groups of 4.
  * Connects directly to Supabase to fetch live availability.
  * Heavily penalizes same-day double headers to ensure fair spread-out schedules.
  * Enforces pitch capacity (Max 2 concurrent matches).
  * Automatically reserves late-week slots for Quarter-Finals, Semi-Finals, and Finals.
  * Outputs a perfectly formatted, printable `tournament_schedule.txt`.

---

## 🛠️ Tech Stack
* **Frontend:** Next.js (App Router), React, Tailwind CSS, Framer Motion, MagicUI.
* **Backend:** Supabase (PostgreSQL).
* **Scripting:** Python 3, `supabase-py`, `python-dotenv`.
* **Hosting:** Vercel.

---

## 🚀 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/OMZaky/asu-sports-scheduler.git
cd asu-sports-scheduler
```

### 2. Frontend Setup
Navigate into the web directory and install the dependencies:
```bash
cd web
npm install
```

### 3. Environment Variables
Create a `.env.local` file inside the `web/` folder and add your Supabase credentials:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-url.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Run the Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser to see the app.

---

## 🎲 Running the Algorithm

Once teams have submitted their availability via the live website or your local server, you can generate the tournament schedule.

1. Ensure you are in the root directory (not the `web/` folder).
2. Install the required Python libraries:
```bash
pip install supabase python-dotenv
```
3. Run the scheduler script:
```bash
python algorithm.py
```
The script will pull the live data from Supabase, process the brackets, and instantly create a `tournament_schedule.txt` file containing the chronological schedule!

---

## 🔒 Database Security
The Supabase tables are secured with **Row Level Security (RLS)**. The public `insert` policy is enabled, meaning anyone can submit their team's availability, but **no one can delete, edit, or view** other teams' submissions via the web app. 

*Note: To wipe the database or remove spam submissions, you must log in to the Supabase Dashboard and delete the rows manually from the `teams` table.*
