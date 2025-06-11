# Team Factory Quick Reference Guide

## 🚀 Creating Your First Enhanced Team

### Basic Command
```bash
cd tools
python team_factory.py
```

### The Enhanced Flow

#### Step 1: Describe Your Need
```
What kind of team do you need?
> "A team to improve customer retention through data-driven strategies"
```

#### Step 2: Choose AI Composition (Recommended)
```
Would you like AI to propose the optimal team composition? [Y/n]
> Y

🤖 Analyzing requirements...
[AI proposes 5-member team with roles, responsibilities, and rationale]

Would you like to refine this composition? [y/N]
> N
```

#### Step 3: Generate Enhanced Prompts
```
Would you like to generate enhanced contextual prompts for all agents? [Y/n]
> Y

🎯 Let's define the context for customer-retention-team
Team PURPOSE: [shown AI suggestion]
> "Reduce churn by 25% through proactive engagement"

What are the team's TOP 3 GOALS?
Goal 1: > Identify at-risk customers before they churn
Goal 2: > Create personalized retention campaigns
Goal 3: > Measure and optimize intervention effectiveness
```

#### Step 4: Select Framework
```
Choose framework:
1. CrewAI (natural language collaboration)
2. LangGraph (state-machine workflows)
> 1
```

#### Step 5: Team Generated!
```
✅ Team created with:
- AI-optimized composition (including skeptic)
- Rich contextual prompts for each agent
- Advanced capabilities (memory, error handling, etc.)
- Conversation logging enabled
- Ready for deployment
```

---

## 🛠️ Post-Creation Operations

### Modify Agent Prompts
```bash
python team_factory.py --modify-prompt --team customer-retention-team --agent retention_analyst
```

### View Team Structure
```bash
ls teams/customer-retention-team/
├── agents/           # Individual agents with enhanced code
├── crew.py          # Team orchestration
├── config/          # Team and A2A configuration
├── tasks/           # Sample tasks
├── tools/           # Team-specific tools
└── k8s/            # Deployment manifests
```

### Check Agent Capabilities
Look in any agent file to see:
- Smart memory management
- Error recovery mechanisms
- Parallel execution support
- Adaptive behavior tracking
- Conversation logging

---

## 📋 Enhancement Features Checklist

### ✅ AI Team Composition
- [x] Natural language team request
- [x] AI analyzes and proposes optimal team
- [x] Includes skeptic for teams ≥5 members
- [x] Interactive refinement available
- [x] Explains rationale for each role

### ✅ Enhanced Prompts Include
- [x] Organization context (mission, stage, priorities)
- [x] Team purpose and goals
- [x] Individual role details
- [x] Team dynamics and interaction styles
- [x] Success criteria
- [x] Operating constraints
- [x] Communication guidelines

### ✅ Code Enhancements
- [x] **Smart Memory**: Token-aware context management
- [x] **Error Recovery**: Retry with exponential backoff
- [x] **Parallel Execution**: Process multiple tasks concurrently
- [x] **Tool Orchestration**: Intelligent tool selection
- [x] **Adaptive Behavior**: Learn from successes/failures
- [x] **Context Awareness**: Consider team and task context

### ✅ Conversation Logging
- [x] All agent interactions logged
- [x] Natural language and structured formats
- [x] Local files and Supabase storage
- [x] Ready for Quality Auditor analysis

---

## 🎯 Common Team Patterns

### Innovation Team
```
Request: "A team to explore new product opportunities"
AI Proposes: Innovation Lead, Researcher, Prototyper, Skeptic, User Advocate
```

### Analytics Team
```
Request: "A team for business intelligence and reporting"
AI Proposes: BI Lead, Data Engineer, Analyst, Visualizer, Quality Advocate
```

### Customer Team
```
Request: "A team to improve customer experience"
AI Proposes: CX Lead, Journey Designer, Support Specialist, Advocate, Skeptic
```

### Crisis Team
```
Request: "A team for rapid incident response"
AI Proposes: Incident Commander, Tech Lead, Communicator, Resolver, Coordinator
```

---

## 💡 Pro Tips

### 1. Be Specific in Requests
❌ "I need a marketing team"
✅ "I need a team to increase organic traffic through content marketing"

### 2. Provide Context When Asked
The more context you provide about goals and constraints, the better the agent prompts will be.

### 3. Trust the AI Composition
The AI knows about team dynamics and includes roles you might not think of (like skeptics).

### 4. Refine If Needed
You can always add/remove team members or modify roles during the refinement step.

### 5. Update Prompts Later
Use `--modify-prompt` to refine agent prompts based on actual performance.

---

## 🆘 Troubleshooting

### Issue: Team seems too large/small
**Solution**: During refinement, adjust team size. AI follows 3-7 member guideline but you can override.

### Issue: Missing specific expertise
**Solution**: Add a specialist during refinement or modify an existing role to include needed skills.

### Issue: Agents not collaborating well
**Solution**: Review and modify prompts to clarify interaction styles and communication patterns.

### Issue: Want different capabilities
**Solution**: The code enhancer automatically selects capabilities based on role, but you can customize in the generated files.

---

## 📚 Further Reading

- `docs/TEAM_FACTORY_ENHANCEMENTS.md` - Detailed technical documentation
- `docs/TEAM_FACTORY_TRANSFORMATION.md` - Before/after comparison
- `docs/Agent Design Pattern V2.md` - Team-based architecture patterns
- `docs/QUALITY_AUDITOR_IMPROVEMENT_LOOP.md` - Continuous improvement system

---

## 🎉 You're Ready!

With these enhancements, every team you create will be:
- **Optimally composed** by AI
- **Deeply contextual** with rich prompts
- **Highly capable** with advanced code
- **Self-improving** through logging and adaptation

Happy team building! 🚀
