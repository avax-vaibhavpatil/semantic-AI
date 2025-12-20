# 📚 Saved Reports Feature - User Guide

## 🎉 New Features Added!

Your frontend now has a **beautiful collapsible sidebar** for managing saved reports!

---

## 🚀 How to Use

### **1. Open Saved Reports Sidebar**

**Two ways to open:**

**Option A:** Click the **floating menu button** (top-left corner)
- Purple circular button with menu icon
- Always visible, floats above content

**Option B:** Click **"Saved Reports"** button in header
- Located in top-right of the purple header bar

### **2. Save a Report**

**Steps:**
1. Ask a question and get results
2. Click the **"Save Report"** button (above results table)
3. Fill in the form:
   - **Report Name** (required) - Auto-filled from your question
   - **Description** (optional) - What the report shows
   - **Tags** (optional) - Comma-separated (e.g., "sales, monthly, executive")
4. Click **"Save Report"**

**Example:**
```
Question: "Show me top 10 customers by sales"

Report Name: Monthly Top Performers
Description: Shows highest revenue customers
Tags: sales, customers, monthly
```

### **3. View Saved Reports**

**In the sidebar you'll see:**
- 📑 **Report name** (bold, clickable)
- 🏷️ **Tags** (blue chips)
- 📅 **Created date**
- ▶️ **Play button** (execute report)
- ⭐ **Star icon** (mark as favorite)
- 🗑️ **Delete icon** (remove report)

### **4. Execute a Saved Report**

**Two ways:**
1. Click anywhere on the report card
2. Click the play button icon

**What happens:**
- SQL query runs against live database
- Fresh, updated data is displayed
- Execution count is updated
- Sidebar stays open (or closes - your choice!)

### **5. Search Reports**

Use the search box at top of sidebar:
- Type to search by report name
- Results update as you type
- Clear search with X button

### **6. Filter by Favorites**

Click the **"Favorites"** chip:
- Shows only starred reports
- Click again to show all

### **7. Mark as Favorite**

Click the **star icon** on any report:
- Empty star = not favorite
- Gold star = favorite
- Use for quick access to important reports

### **8. Delete a Report**

Click the **trash icon**:
- Confirmation dialog appears
- Report is permanently removed

---

## 🎨 UI Elements

### **Sidebar Features:**

```
┌─────────────────────────────┐
│ 📚 Saved Reports     [5]    │ ← Header with count
├─────────────────────────────┤
│ 🔍 [Search box]        ❌   │ ← Search
│ ⭐ Favorites                 │ ← Filter
├─────────────────────────────┤
│ ▶️  Monthly Sales Report    │
│     🏷️ sales  🏷️ monthly    │ ← Report card
│     📅 Dec 15, 2:30 PM      │
│     Executed 5 times    ⭐ 🗑️│
├─────────────────────────────┤
│ ▶️  Customer Analysis       │
│     🏷️ customers            │
│     📅 Dec 14, 10:15 AM  ⭐ 🗑️│
└─────────────────────────────┘
```

### **Main Page Features:**

```
┌─────────────────────────────────┐
│ 🟣 [Menu]  Semantic AI BI Platform  [Saved Reports] │
├─────────────────────────────────┤
│ Ask Your Question               │
│ [Text input] [Ask]              │
├─────────────────────────────────┤
│ Query Results                    │
│ [💾 Save] [📊 Visualize] [📥 Export] │
│ [Results Table]                  │
└─────────────────────────────────┘
```

---

## 💡 Pro Tips

### **1. Organize with Tags**
```
Good tagging:
- "sales, monthly, executive"
- "finance, quarterly, board-meeting"
- "operations, daily, alerts"
```

### **2. Descriptive Names**
```
❌ Bad:  "Report 1"
✅ Good: "Top 10 Customers - YTD Sales"

❌ Bad:  "Sales"
✅ Good: "Monthly Sales by Region - Q4 2025"
```

### **3. Use Favorites**
- Star your most-used reports
- Filter to favorites for quick access
- Perfect for daily dashboards

### **4. Search Shortcuts**
- Type partial names: "sales" finds "Monthly Sales"
- Search is case-insensitive
- Results update instantly

---

## 🎯 Complete Workflow Example

### **Scenario: Create a Monthly Report**

**Step 1: Generate Query**
```
1. Type: "Show handler-wise sales with customer count"
2. Click "Ask"
3. Review results
```

**Step 2: Save**
```
1. Click "Save Report"
2. Name: "Handler Sales Performance - Monthly"
3. Description: "Handler-wise sales summary with customer metrics"
4. Tags: "sales, handlers, monthly"
5. Click "Save Report"
```

**Step 3: Use Later**
```
1. Open sidebar (click menu button)
2. Find your report
3. Click to execute
4. Fresh data appears instantly!
```

---

## 🔧 Keyboard Shortcuts

- **Enter** - Submit query (in question box)
- **Esc** - Close sidebar (when sidebar is open)
- **Esc** - Close save dialog (when dialog is open)

---

## 📊 Features at a Glance

| Feature | Status |
|---------|--------|
| Collapsible Sidebar | ✅ |
| Save Reports | ✅ |
| Execute Saved Reports | ✅ |
| Search Reports | ✅ |
| Filter by Favorites | ✅ |
| Mark as Favorite | ✅ |
| Delete Reports | ✅ |
| Tag Management | ✅ |
| Execution Count Tracking | ✅ |
| Fresh Data on Execute | ✅ |
| Responsive Design | ✅ |

---

## 🎨 Design Features

- **Beautiful gradients** - Purple-blue theme
- **Smooth animations** - Hover effects, transitions
- **Material Design** - Modern, clean UI
- **Responsive** - Works on all screen sizes
- **Accessible** - Tooltips, clear labels
- **Intuitive** - Click to execute, star to favorite

---

## 🐛 Troubleshooting

### **Sidebar won't open**
- Make sure frontend is running: `npm run dev`
- Check browser console for errors

### **Reports not loading**
- Check backend is running on port 8000
- Verify: `curl http://localhost:8000/health`

### **Can't save report**
- Report name is required
- Backend must be accessible
- Check browser console for errors

### **Search not working**
- Type at least 1 character
- Wait 500ms for debounce
- Clear search and try again

---

## 📂 Files Created

```
frontend/
├── components/
│   └── SavedReportsSidebar.js  ← NEW! Sidebar component
├── pages/
│   └── index.js                ← UPDATED! Added save functionality
└── SAVED_REPORTS_GUIDE.md      ← This file
```

---

## 🚀 Next Steps

**Enhancements you can add:**
1. **Bulk operations** - Delete multiple reports
2. **Share reports** - Share with team members
3. **Schedule reports** - Auto-execute daily/weekly
4. **Export saved list** - Download all reports as JSON
5. **Report folders** - Organize in categories
6. **Version history** - Track report changes
7. **Duplicate report** - Clone existing reports
8. **Report templates** - Pre-defined queries

---

## 💬 Need Help?

**Check:**
1. Backend logs: `/tmp/backend.log`
2. Browser console: F12 → Console tab
3. Network tab: Check API requests

**Common Issues:**
- Backend not running → Start it!
- Port conflict → Change ports
- CORS error → Check CORS settings

---

**Created:** 2025-12-16  
**Version:** 1.0.0  
**Status:** ✅ FEATURE COMPLETE

**Enjoy your new saved reports feature!** 🎉

