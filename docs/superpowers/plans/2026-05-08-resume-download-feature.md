# Resume Download Feature Implementation Plan

> **For agentic workers:** Use systematic-debugging or test-driven-development workflows as needed. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add download functionality to the existing resume upload section with improved resume visibility.

**Architecture:** Enhance the job detail page frontend to add a download button next to the current resume display, leveraging the existing backend download API endpoint.

**Tech Stack:** HTML, JavaScript, Tailwind CSS, FastAPI backend endpoints

---

### Task 1: Update HTML and Add Download Functionality

**Files:**
- Modify: `/Users/mehran/Documents/Codes/Job Application CRM/index.html:750-777`
- Modify: `/Users/mehran/Documents/Codes/Job Application CRM/index.html:976-996`

- [ ] **Step 1: Update resume display HTML**

Replace the current resume display with enhanced version including download button:

```html
${job.resume_file ? `
  <div class="mb-3 p-3 bg-[#1e2240]/50 rounded-xl border border-[rgba(255,255,255,0.05)]">
    <div class="flex items-center gap-3 mb-2">
      <i class="fa-solid fa-file-pdf text-[#f87171]"></i>
      <span class="text-sm font-medium text-[#eef0ff]">${escHtml(job.resume_version_name||'Resume uploaded')}</span>
    </div>
    <div class="flex items-center gap-2">
      <button onclick="downloadResume(event, '${job.id}')" class="px-3 py-1.5 text-xs bg-[#a78bfa]/20 hover:bg-[#a78bfa]/30 text-[#a78bfa] rounded-lg transition-all border border-[#a78bfa]/30">
        <i class="fa-solid fa-download mr-1"></i> Download
      </button>
      <button onclick="removeResume('${job.id}')" class="px-3 py-1.5 text-xs bg-[#f87171]/20 hover:bg-[#f87171]/30 text-[#f87171] rounded-lg transition-all border border-[#f87171]/30">
        <i class="fa-solid fa-trash mr-1"></i> Remove
      </button>
    </div>
  </div>
` : ''}
```

- [ ] **Step 2: Add downloadResume function with loading state**

Add this function after the existing `removeResume` function:

```javascript
async function downloadResume(event, id) {
  const button = event.currentTarget;
  const originalContent = button.innerHTML;
  button.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Downloading...';
  button.disabled = true;
  
  try {
    const response = await fetch(API_BASE + '/api/jobs/' + id + '/resume');
    if (!response.ok) {
      const err = await response.json().catch(() => ({detail: 'Download failed'}));
      throw new Error(err.detail);
    }
    
    // Get filename from header or use default
    const contentDisposition = response.headers.get('content-disposition');
    let filename = 'resume.pdf';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch) filename = filenameMatch[1];
    }
    
    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    toast('Resume downloaded');
  } catch(e) { 
    toast('Download failed: ' + e.message, 'error'); 
  } finally {
    button.innerHTML = originalContent;
    button.disabled = false;
  }
}
```

- [ ] **Step 3: Test the implementation**

Run: `python main.py` and navigate to a job with status "Will Apply" or higher
Expected: Resume section shows download and remove buttons, download works with loading state

### Task 2: Comprehensive Testing

**Files:**
- Test: `/Users/mehran/Documents/Codes/Job Application CRM/index.html`

- [ ] **Step 1: Test across different job statuses**

Test with jobs in different statuses (Will Apply, Applied, Interviewing, Offer)
Expected: Download functionality works in all applicable statuses

- [ ] **Step 2: Test with different file types**

Test downloading PDF, DOC, and DOCX files
Expected: All file types download correctly

- [ ] **Step 3: Test error scenarios**

Test downloading when no resume is uploaded, when file is missing
Expected: Appropriate error messages shown

- [ ] **Step 4: Verify responsive design**

Test on different screen sizes
Expected: Buttons remain usable and well-styled

- [ ] **Step 5: Save changes**

Save the modified index.html file with all changes implemented

---

## Self-Review

**Spec coverage:** 
- ✅ Download button in resume section
- ✅ Shows uploaded resume information  
- ✅ Download functionality works
- ✅ Maintains existing upload/delete functionality
- ✅ Consistent with glass morphism design

**Placeholder scan:** No placeholders found - all code and steps are complete.

**Type consistency:** All function names and variable usage are consistent throughout the plan.
