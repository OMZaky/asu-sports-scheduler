"use client";

import { useState } from "react";
import TimeGrid, { Slot } from "@/components/TimeGrid";
import { SparklesText } from "@/components/magicui/sparkles-text";
import { FloatingFootballs } from "@/components/FloatingFootballs";

export default function Home() {
  const [teamName, setTeamName] = useState("");
  const [captainName, setCaptainName] = useState("");
  const [availability, setAvailability] = useState<Slot[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!teamName.trim()) {
      alert("Please enter a team name.");
      return;
    }
    if (!captainName.trim()) {
      alert("Please enter the captain's name.");
      return;
    }
    if (availability.length === 0) {
      alert("Please select at least one available time slot.");
      return;
    }

    setIsSubmitting(true);
    
    // Simulate API call to Supabase
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    // Here we would typically save to Supabase:
    // await supabase.from('teams').insert({ name: teamName, captain: captainName, availability: availability })
    
    setIsSubmitting(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
        <FloatingFootballs />
        <div className="bg-secondary p-10 rounded-3xl border border-border text-center max-w-lg shadow-2xl relative z-10">
          <div className="w-20 h-20 bg-primary/20 text-primary rounded-full flex items-center justify-center mx-auto mb-6 text-4xl">
            ✓
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-4">Availability Submitted!</h1>
          <p className="text-muted mb-8">
            Thank you, <span className="text-foreground font-semibold">{captainName}</span> of <span className="text-foreground font-semibold">{teamName}</span>! We have recorded your free times. The final schedule will be announced soon.
          </p>
          <button 
            onClick={() => { setSubmitted(false); setTeamName(""); setCaptainName(""); setAvailability([]); }}
            className="px-6 py-3 bg-background border border-border text-foreground font-medium rounded-xl hover:bg-border transition-colors"
          >
            Submit Another Team
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen py-12 px-4 sm:px-8 bg-background relative overflow-hidden">
      <FloatingFootballs />
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 blur-[120px] rounded-full pointer-events-none z-0" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/10 blur-[120px] rounded-full pointer-events-none z-0" />
      
      <div className="max-w-5xl mx-auto relative z-10">
        <header className="mb-12 flex flex-col items-center text-center">
          <div className="w-full max-w-lg mx-auto mb-8 mt-4 flex justify-center">
            <SparklesText 
              className="text-5xl md:text-7xl font-black italic tracking-tighter drop-shadow-[0_0_15px_rgba(16,185,129,0.3)] text-transparent bg-clip-text bg-gradient-to-br from-white to-emerald-400 pr-4 pb-2"
              colors={{ first: "#10b981", second: "#34d399" }}
              sparklesCount={8}
            >
              ASU SPORTS
            </SparklesText>
          </div>

          <p className="text-lg text-muted max-w-2xl mx-auto mt-2">
            Welcome teams! Please enter your team details and drag on the grid below to mark all the times you are available to play.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-10">
          <div className="max-w-2xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2 ml-1" htmlFor="teamName">
                Team Name
              </label>
              <input
                id="teamName"
                type="text"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="e.g. The Invincibles"
                className="w-full px-5 py-4 bg-secondary border border-border rounded-xl text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all shadow-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-foreground mb-2 ml-1" htmlFor="captainName">
                Captain Name
              </label>
              <input
                id="captainName"
                type="text"
                value={captainName}
                onChange={(e) => setCaptainName(e.target.value)}
                placeholder="e.g. Lionel Messi"
                className="w-full px-5 py-4 bg-secondary border border-border rounded-xl text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all shadow-sm"
                required
              />
            </div>
          </div>

          <TimeGrid onChange={setAvailability} />

          <div className="text-center">
            <button
              type="submit"
              disabled={isSubmitting}
              className={`
                px-10 py-4 rounded-xl font-bold text-lg shadow-xl transition-all
                ${isSubmitting 
                  ? 'bg-primary/50 text-white cursor-not-allowed' 
                  : 'bg-primary text-white hover:bg-primary-hover hover:scale-105 active:scale-95 shadow-[0_10px_20px_-10px_rgba(16,185,129,0.5)]'}
              `}
            >
              {isSubmitting ? 'Saving...' : 'Submit Availability'}
            </button>
            <p className="mt-4 text-sm text-muted">
              {availability.length} slots selected ({(availability.length * 0.5).toFixed(1)} hours)
            </p>
          </div>
        </form>
      </div>
    </main>
  );
}
