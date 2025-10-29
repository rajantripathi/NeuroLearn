# 🚀 NeuroLearn Quick Start

## Get Started in 3 Steps

### 1️⃣ Start the Application
```bash
./start.sh
```

### 2️⃣ Open Your Browser
Navigate to: **http://localhost:8501**

### 3️⃣ Start Using NeuroLearn!

---

## First-Time Setup

The startup script will:
- ✅ Launch Docker containers
- ✅ Download AI models (~2-3 GB)
- ✅ Initialize the knowledge base
- ✅ Start the web interface

**First launch takes 5-10 minutes** due to model downloads.

---

## Using NeuroLearn

### Set Your State
**Sidebar → "How are you feeling?"**
- 😌 Neutral - Regular support
- 😰 Overwhelmed - Gentle, step-by-step
- 😵 Distracted - Quick refocus
- 🎯 Focused - Concise, task-mode

### Start a Focus Sprint
1. Enter what you'll work on
2. Choose duration (5-25 min)
3. Click "Start Sprint"
4. Work until timer finishes
5. Rate your focus

### Chat for Help
Try saying:
- "I can't start my assignment"
- "Help me focus in this noisy café"
- "I'm overwhelmed by this reading"
- "Plan my study session"

### Upload Documents
- Click "Upload Document for Help"
- Choose PDF or text file
- Click "Summarize This"
- Get ADHD-friendly summary

### Reflect on Your Session
- Rate your focus (1-5)
- Note what helped
- System learns your preferences

---

## Sample Interactions

**Getting Started:**
> User: "I feel stuck and don't know where to begin"  
> NeuroLearn: "It's normal to freeze before big tasks. Let's make it tiny. Step 1: open the document and write just one line..."

**Focus Sprint:**
> User: *Starts 10-min sprint*  
> NeuroLearn: *Shows countdown timer and progress bar*  
> After: "How focused did you feel?"

**Document Help:**
> User: *Uploads research paper*  
> NeuroLearn: "Main topic: X. Key points: 1) ... 2) ... 3) ... (Based on Open University ADHD guidelines)"

---

## Tips for Success

### 🎯 Best Practices
- Start with 5-10 min sprints if overwhelmed
- Set your focus state honestly
- Reflect after each session
- Use document summaries for long readings

### ⚡ Power Features
- Upload lecture notes for simplification
- Chain sprints with short breaks
- Track what strategies work for you
- Adjust environment based on location

### 🛑 When NOT to Use
- Medical diagnosis questions → See a doctor
- Medication advice → Talk to your psychiatrist
- Crisis situations → Contact support services

---

## Stopping the App

```bash
docker-compose down
```

---

## Need Help?

- **Setup issues**: See `SETUP.md`
- **Usage questions**: See `README.md`
- **Technical problems**: Check logs with `docker-compose logs -f`

---

## What Makes NeuroLearn Different?

✅ **Evidence-Based**: Strategies from ADHD research (Barkley, Brown, Open University)  
✅ **Adaptive Tone**: Adjusts to your current state  
✅ **Privacy-First**: All data stays on your machine  
✅ **Offline Capable**: Works without internet  
✅ **No Judgment**: Supportive, non-clinical approach  

---

**Ready to learn smarter?** Run `./start.sh` and open http://localhost:8501! 🧠

