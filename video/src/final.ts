// THE FINAL'S RESULT: the one place to fill in after the final (Sunday 15 November 2026, 07:00–07:35 UTC).
// Leave a field null and the video shows "__" for it. Then re-render: npm run render (see README.md).
export const FINAL = {
  rank: null as number | null,        // our place among the ranked teams, e.g. 4
  rankedTeams: null as number | null, // how many teams were ranked, e.g. 61
  marginEur: null as number | null,   // margin in euros, e.g. 17442.75
  orders: null as number | null,      // orders won, e.g. 356
  onTimePct: null as number | null,   // on-time share in percent, e.g. 97.2
};

// The best ranking round. Standings move while a round is open; update here if they change.
export const BEST_ROUND = {
  round: "Round 12 · Sunday 06:00",
  rank: 6,             // our place at 06:10 UTC
  rankedTeams: 43,
  marginEur: 79842,    // over its 5 weeks
  runs: 5,
  onTimePct: 96.6,     // mean; every week ranked (95.3–97.6%)
};
