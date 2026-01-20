# 🎨 OPS Bot Orchestrator - Architecture Diagrams

This directory contains professional Mermaid diagrams for the OPS Bot Orchestrator presentation.

## 📊 Available Diagrams

### 1. High-Level System Architecture
**File**: `01-high-level-architecture.mermaid`  
**Type**: Flow Diagram (TB - Top to Bottom)  
**Use For**: Opening slides, system overview  
**Shows**: Complete system layers from users to infrastructure

### 2. Orchestrator Details
**File**: `02-orchestrator-details.mermaid`  
**Type**: Flow Diagram (LR - Left to Right)  
**Use For**: Technical deep-dive slides  
**Shows**: Internal orchestrator components and data flow

### 3. CI/CD Pipeline Flow
**File**: `03-cicd-pipeline.mermaid`  
**Type**: Flow Diagram (TD - Top Down)  
**Use For**: Solution slides, workflow demonstration  
**Shows**: Complete deployment workflow with OPS Bot orchestration

### 4. Microservices Deployment
**File**: `04-microservices-deployment.mermaid`  
**Type**: Flow Diagram (TB - Top to Bottom)  
**Use For**: Live demo explanation, real implementation  
**Shows**: Your actual microservices architecture with 2 pods each

### 5. Sequence Flow
**File**: `05-sequence-flow.mermaid`  
**Type**: Sequence Diagram  
**Use For**: Communication patterns, interaction flow  
**Shows**: Real-time message passing between components

---

## 🚀 How to Use

### Method 1: Mermaid Live Editor (Recommended)

1. Visit https://mermaid.live
2. Open any `.mermaid` file
3. Copy the entire content
4. Paste into the editor
5. See instant preview
6. Export as PNG, SVG, or PDF

**Example:**
```bash
# Copy diagram 1
cat 01-high-level-architecture.mermaid | pbcopy

# Then paste in mermaid.live
```

### Method 2: VS Code Preview

1. Install extension: "Markdown Preview Mermaid Support"
2. Create a markdown file:
   ````markdown
   # Architecture
   
   ```mermaid
   [paste diagram content here]
   ```
   ````
3. Open preview: `Cmd/Ctrl + Shift + V`

### Method 3: GitHub (Auto-Render)

1. Push to GitHub repository
2. Reference in README.md:
   ````markdown
   ## Architecture
   
   ```mermaid
   [paste diagram content here]
   ```
   ````
3. GitHub automatically renders Mermaid diagrams

### Method 4: Direct Export

```bash
# Using mmdc (Mermaid CLI)
npm install -g @mermaid-js/mermaid-cli

# Export as PNG
mmdc -i 01-high-level-architecture.mermaid -o diagram1.png

# Export as SVG (scalable)
mmdc -i 01-high-level-architecture.mermaid -o diagram1.svg

# Export all diagrams
for file in *.mermaid; do
  mmdc -i "$file" -o "${file%.mermaid}.png"
done
```

---

## 📋 Usage in Presentation

### PowerPoint/Keynote

1. Export diagrams as PNG using Mermaid Live Editor
2. Insert images into slides
3. Recommended placement:

   - **Slide 2-3**: Diagram #1 (High-Level Architecture)
   - **Slide 6-7**: Diagram #2 (Orchestrator Details)
   - **Slide 8-9**: Diagram #3 (CI/CD Pipeline)
   - **Slide 10**: Diagram #4 (Microservices Deployment)
   - **Slide 11**: Diagram #5 (Sequence Flow)

### Markdown Presentation (Reveal.js, Marp)

```markdown
---
## System Architecture

```mermaid
[paste diagram content]
```

---
```

### Documentation (Confluence, Notion)

Most modern documentation tools support Mermaid:
- Paste diagram code in Mermaid block
- Auto-renders on save

---

## 🎨 Customization Guide

### Change Colors

```mermaid
style NodeName fill:#color
```

**Available colors:**
- `#e1f5ff` - Light Blue
- `#fff3e0` - Light Orange
- `#f3e5f5` - Light Purple
- `#ffebee` - Light Red
- `#c8e6c9` - Light Green
- `#ffcdd2` - Pink Red

### Change Direction

```mermaid
graph TB  %% Top to Bottom
graph LR  %% Left to Right
graph TD  %% Top Down (same as TB)
graph RL  %% Right to Left
```

### Add New Nodes

```mermaid
NewNode[Node Label]
NodeA --> NewNode
NewNode --> NodeB
```

### Modify Connections

```mermaid
A --> B           %% Arrow
A --- B           %% Line
A -.-> B          %% Dotted arrow
A ==> B           %% Thick arrow
A -->|Label| B    %% Labeled arrow
```

---

## 🔧 Troubleshooting

### Diagram Not Rendering?

1. **Check Syntax**: Ensure no typos in node names
2. **Verify Connections**: All referenced nodes must be defined
3. **Test Online**: Use mermaid.live to validate
4. **Check Quotes**: Use proper quotes for labels

### Export Issues?

```bash
# Install Mermaid CLI globally
npm install -g @mermaid-js/mermaid-cli

# Test installation
mmdc --version

# If issues, try with npx
npx @mermaid-js/mermaid-cli -i input.mermaid -o output.png
```

### Performance Issues with Complex Diagrams?

- Break large diagrams into smaller sections
- Use fewer subgraphs
- Simplify connections
- Export at lower resolution for drafts

---

## 📚 Resources

- **Mermaid Documentation**: https://mermaid.js.org
- **Mermaid Live Editor**: https://mermaid.live
- **Syntax Guide**: https://mermaid.js.org/syntax/flowchart.html
- **Sequence Diagrams**: https://mermaid.js.org/syntax/sequenceDiagram.html
- **Examples Gallery**: https://mermaid.js.org/ecosystem/integrations.html

---

## 🎯 Quick Reference

### Diagram Types Used

| Diagram | Type | Best For |
|---------|------|----------|
| #1 | Graph TB | System overview |
| #2 | Graph LR | Process flow |
| #3 | Graph TD | Pipeline flow |
| #4 | Graph TB | Deployment architecture |
| #5 | Sequence | Communication patterns |

### Node Shapes

```mermaid
A[Rectangle]           %% Default
B(Rounded)            %% Soft corners
C([Stadium])          %% Pill shape
D{Diamond}            %% Decision point
E{{Hexagon}}          %% Special process
F[/Parallelogram/]    %% Input/Output
```

### Connection Types

```mermaid
A --> B    %% Solid arrow
A --- B    %% Solid line
A -.-> B   %% Dotted arrow
A ==> B    %% Thick arrow
A --o B    %% Circle end
A --x B    %% Cross end
```

---

## 💡 Pro Tips

1. **For Presentations**: Export as PNG at 2x resolution for clarity
2. **For Documentation**: Use SVG format for scalability
3. **For Print**: Export as PDF for best quality
4. **For Web**: Embed Mermaid code directly in markdown

### Recommended Export Settings

```bash
# High-quality PNG for PowerPoint
mmdc -i diagram.mermaid -o diagram.png -w 2400 -H 1800

# SVG for web/docs
mmdc -i diagram.mermaid -o diagram.svg

# PDF for print
mmdc -i diagram.mermaid -o diagram.pdf
```

---

## ✅ All diagrams are production-ready and tested!

Each diagram is:
- ✓ Syntactically correct
- ✓ Color-coded for clarity
- ✓ Optimized for professional use
- ✓ Ready to render in any Mermaid-compatible tool
