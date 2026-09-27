# CS3501 Final Presentation - Execution & Preparation Plan

**Group:** Group 14  
**Project:** Sinhala-Script Language Identification (LangID) for Sinhala, Pali, and Sanskrit  
**Submission Deadline:** Friday, 2 October 2026, 11:59 PM  
**Total Allocated Time:** 15–20 minutes presentation + 10 minutes Viva/Q&A  

---

## 1. Team Speaker Roles & Time Allocation (4-Member Standard)

To secure the **10 points for Presentation** and **10 points for Demonstration**, transitions between speakers must be crisp, with each member owning a clear domain:

```
┌─────────────────┬────────────────────────────────────────────┬─────────────┐
│ Speaker         │ Section / Responsibilities                 │ Time        │
├─────────────────┼────────────────────────────────────────────┼─────────────┤
│ Speaker 1       │ Hook, Problem Understanding, Motivation    │ 3.5 mins    │
│                 │ (Slides 1–7)                               │             │
├─────────────────┼────────────────────────────────────────────┼─────────────┤
│ Speaker 2       │ Data Pipeline & Benchmark Engineering      │ 3.5 mins    │
│                 │ (Slides 8–14)                              │             │
├─────────────────┼────────────────────────────────────────────┼─────────────┤
│ Speaker 3       │ Methodology: Leaf Surgery & Model Building │ 4.5 mins    │
│                 │ (Slides 15–22)                             │             │
├─────────────────┼────────────────────────────────────────────┼─────────────┤
│ Speaker 4       │ Empirical Results (Tables 1, 2, 3)         │ 4.5 mins    │
│                 │ (Slides 23–29)                             │             │
├─────────────────┼────────────────────────────────────────────┼─────────────┤
│ Speaker 1 / 4   │ System Architecture, Pytest CI/CD, & DEMO  │ 4.0 mins    │
│                 │ (Slides 30–43)                             │             │
└─────────────────┴────────────────────────────────────────────┴─────────────┘
Total Presentation Time: 20 Minutes Max | Q&A: 10 Minutes
```

---

## 2. 7-Day Countdown Checklist (Target: Friday, 2 Oct)

### Day 1–2: Slide Creation & Visual Assets
- [ ] Build the 16:9 master deck using the **Slate / Deep Navy + Emerald & Gold** color palette.
- [ ] Incorporate the **Side-by-Side Text Graphic** (Slide 3: Sinhala vs. Pali vs. Sanskrit).
- [ ] Draw the **Binary Huffman Tree Leaf Surgery Diagram** (Slide 16–17).
- [ ] Insert the cleaned Tables 1, 2, and 3 from `Comparison Tables - Final Corrected.csv`.

### Day 3: Full-Stack Demo Recording & Live Backup
- [ ] Record a high-resolution 1080p fallback screen recording of the web platform (in case local servers or internet fail during viva).
- [ ] Test the live `/predict` endpoint on FastAPI with real samples of Dhammapada stanzas and modern Sinhala news.

### Day 4: Speaker Dry Run #1 (Content & Timing)
- [ ] Conduct a full run-through with a stopwatch.
- [ ] Ensure strict adherence to individual time caps (<4 minutes per speaker).
- [ ] Fix verbal stumbles and replace filler phrases.

### Day 5: Multi-Tier Testing & Engineering Proofs
- [ ] Capture terminal screenshots of **Pytest passing 40+ unit tests** (Slide 37).
- [ ] Capture GitHub Actions green CI/CD build badge (Slide 38).
- [ ] Capture Locust load test graphs showing sub-5ms latency under 100 concurrent requests (Slide 39).

### Day 6: Speaker Dry Run #2 (The Mock Viva)
- [ ] Drill the **Top 10 Viva Questions** from `03_VIVA_QUESTIONS_AND_DEFENSE_GUIDE.md`.
- [ ] Practice jumping seamlessly to the **Appendix Slides (Slides 44–50)** when asked about mathematical derivations or data leakage proofs.

### Day 7: Final Polish & PDF Export
- [ ] Export final deck as PDF and PPTX.
- [ ] Verify that fonts and ligature diacritics render perfectly across all platforms.
- [ ] Submit via LMS before 11:59 PM.

---

## 3. High-Scoring Non-Verbal & Delivery Rules

1. **Avoid Reading Slides:** Slides must contain diagrams, metrics, and bulleted takeaways; speak to the insights, not the text on screen.
2. **Never Say "We didn't have time for...":** Frame past challenges as conscious engineering trade-offs (e.g., *"We prioritized CPU sub-millisecond inference over heavy GPUs because LangID is a pipeline bottleneck"*).
3. **Praise the Data First:** Examiners love data hygiene. Spending 3 focused minutes proving zero data leakage and proper Unicode normalization demonstrates academic maturity.
