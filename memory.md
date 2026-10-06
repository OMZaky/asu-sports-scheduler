# ASU Sports Scheduler - Memory & Context

## 🏆 Project Overview
**ASU Sports Scheduler** is a full-stack web application designed to collect availability from sports teams and programmatically generate a fair, conflict-free tournament schedule (Group Stages + Knockout Stages).
*   **Frontend:** Next.js (App Router), Tailwind CSS, Framer Motion, MagicUI.
*   **Backend:** Supabase (PostgreSQL).
*   **Algorithm:** Python.
*   **Deployment:** Vercel (Web), GitHub (Code).

---

## ✅ What We Built (Current State)

### 1. The Web App (`web/`)
*   **Time Grid System:** Created a custom, mobile-responsive "Day Stack" grid. Runs Saturday through Thursday (Fridays excluded) from 10:00 AM to 8:00 PM.
*   **Form & Database Connection:** The form collects Team Name, Captain Name, and selected time slots. It directly pushes this data to Supabase using the `@supabase/supabase-js` client.
*   **Premium UI/UX:** 
    *   Interactive physics engine (`FloatingFootballs.tsx`) simulating bouncing footballs repelled by the user's cursor at 60fps.
    *   Glowing, animated text inputs that react on hover and focus.
    *   Success state overlay that prevents duplicate form submissions.
*   **Polish:** Added a custom `icon.png` (football), updated SEO metadata, and integrated `@vercel/speed-insights`.

### 2. The Database (Supabase)
*   **Schema:** 
    *   `teams` table (`id`, `team_name` [UNIQUE], `captain_name`).
    *   `availability` table (`id`, `team_id` [FOREIGN KEY], `day`, `time`).
*   **Cascade Deletion:** Configured `ON DELETE CASCADE` so deleting a team automatically wipes their availability slots.
*   **Security (RLS):** Policies are strictly set to **Insert Only** for the public. This ensures users can submit data, but malicious users cannot delete or edit other teams' data.

### 3. The Algorithm (`algorithm.py`)
*   **Direct Cloud Sync:** Bypasses local JSON files and connects directly to Supabase using `python-dotenv` (reads `web/.env.local`).
*   **Group Stage Logic:** Randomly sorts teams into groups of 4. Matches every team against each other (Round Robin). 
*   **Smart Penalties:** Applies a massive `-50` priority penalty if a team is forced to play twice on the same day, heavily encouraging spread-out schedules.
*   **Pitch Management:** Enforces a hard limit of `MAX_CONCURRENT_MATCHES = 2` (Pitch 1 and Pitch 2).
*   **Knockout Stage Logic:** Scans the entire tournament's available slots, sorts them chronologically backwards, and claims the very last slots of the week for the Quarter-Finals, Semi-Finals, and Final ("TBD vs TBD").
*   **File Output:** Formats the schedule beautifully and writes it to `tournament_schedule.txt` (ignoring it from Git to keep the repo clean).

---

## 🧠 Crucial Knowledge & Gotchas
*   **Vercel Root Directory:** Because the Next.js app lives inside the `web/` folder, Vercel's "Root Directory" setting MUST be set to `web`. If left blank, builds will fail.
*   **Environment Variables:** The Next.js frontend strictly requires `NEXT_PUBLIC_SUPABASE_ANON_KEY`. (Do not accidentally use the Publishable Key name). If `.env.local` is modified locally, `npm run dev` must be restarted.
*   **Cleaning Fake Data:** Because of RLS security, fake data cannot be deleted via the frontend or Python script. It must be deleted manually in the Supabase Dashboard by selecting rows in the `teams` table and clicking Delete.
*   **Windows Encoding:** The Python script uses standard text instead of Emojis to prevent `UnicodeEncodeError` crashes on Windows terminals.

---

## 🚀 Ideas for Future Sessions
1.  **Public "Live Schedule" Page:** Instead of just generating a `.txt` file, we can have the Python script write the final schedule back to a new Supabase table. Then, create a `/schedule` page on the Next.js site where teams can view the live bracket.
2.  **Dynamic Group Sizing:** Upgrade the algorithm to gracefully handle uneven numbers of teams (e.g., 5, 6, 7 teams) and dynamically adjust the number of groups and knockout bracket sizes.
3.  **Score Tracking:** Add an admin dashboard where you can input the scores of finished games, automatically advancing the winning teams into the "TBD" Knockout slots.
4.  **Notifications:** Integrate an email API (like Resend) or WhatsApp bot to automatically notify captains when the schedule is finalized.
