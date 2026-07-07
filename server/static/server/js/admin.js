/* ─── Modal helpers ─────────────────────────────────────────── */
function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
    document.body.classList.add("overflow-hidden");
}
function closeModal(id) {
    document.getElementById(id).classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
}
// Close on backdrop click
document.addEventListener("click", function (e) {
    if (e.target.classList.contains("modal-backdrop")) {
        e.target.closest("[id]").id && closeModal(e.target.closest("[id]").id);
    }
});
// Close on Escape
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        document.querySelectorAll(".modal-wrap:not(.hidden)").forEach(function (m) {
            closeModal(m.id);
        });
    }
});

/* ─── Flash-message auto-dismiss ───────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        document.querySelectorAll(".flash-msg").forEach(function (el) {
            el.style.transition = "opacity .4s";
            el.style.opacity = "0";
            setTimeout(function () { el.remove(); }, 400);
        });
    }, 3500);
});

/* ─── Generic JSON → edit-modal filler ─────────────────────── */
async function loadEdit(url, modalId, fieldMap) {
    const resp = await fetch(url);
    const data = await resp.json();
    Object.entries(fieldMap).forEach(function ([key, elId]) {
        const el = document.getElementById(elId);
        if (!el) return;
        if (el.type === "checkbox") {
            el.checked = !!data[key];
        } else {
            el.value = data[key] ?? "";
        }
    });
    openModal(modalId);
}

/* ─── Delete confirmation ───────────────────────────────────── */
function confirmDelete(modalId, recordId, inputId) {
    document.getElementById(inputId).value = recordId;
    openModal(modalId);
}

/* ─── Grievance view modal (fetches full detail JSON) ───────── */
async function openGrievanceView(pk) {
    const modal   = document.getElementById("modal-view-grievance");
    const content = document.getElementById("gv-content");
    content.innerHTML = `<div class="flex justify-center py-12">
        <svg class="animate-spin h-8 w-8 text-brand-blue" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
        </svg></div>`;
    openModal("modal-view-grievance");
    try {
        const resp = await fetch(`/admin-panel/grievances/${pk}/json/`);
        const d    = await resp.json();
        const timelineHtml = d.timeline.length ? d.timeline.map(h => `
            <div class="flex gap-3 items-start">
                <div class="flex flex-col items-center flex-shrink-0 mt-1">
                    <span class="w-3 h-3 rounded-full bg-brand-blue block"></span>
                    <span class="w-px flex-1 bg-gray-300 block my-1"></span>
                </div>
                <div class="pb-3">
                    <p class="text-sm font-semibold text-gray-800">${h.status}</p>
                    <p class="text-xs text-gray-400">${h.updated_at} &bull; ${h.updated_by}</p>
                    ${h.remarks ? `<p class="text-sm text-gray-600 mt-0.5 italic">${h.remarks}</p>` : ""}
                </div>
            </div>`).join("") : `<p class="text-sm text-gray-400 italic">No history yet.</p>`;

        content.innerHTML = `
<div class="space-y-5">
  <div>
    <h3 class="text-xl font-bold text-gray-900">${d.subject}</h3>
    <p class="text-sm text-gray-500 mt-1">Filed by <strong>${d.user}</strong> (${d.user_email}) &bull; ${d.created_at}</p>
  </div>
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
    <div class="bg-gray-50 rounded-lg p-3"><p class="text-gray-400 mb-1">Category</p><p class="font-semibold">${d.category}</p></div>
    <div class="bg-gray-50 rounded-lg p-3"><p class="text-gray-400 mb-1">Priority</p>
      <span class="px-2 py-0.5 rounded-full text-xs font-medium ${d.priority_colour}">${d.priority}</span></div>
    <div class="bg-gray-50 rounded-lg p-3"><p class="text-gray-400 mb-1">Status</p>
      <span class="px-2 py-0.5 rounded-full text-xs font-medium ${d.status_colour}">${d.status}</span></div>
    <div class="bg-gray-50 rounded-lg p-3"><p class="text-gray-400 mb-1">Spam Score</p>
      <p class="font-semibold ${d.spam_score > 50 ? 'text-red-600' : 'text-green-600'}">${d.spam_score}%</p></div>
  </div>
  ${d.attachment ? `<img src="${d.attachment}" alt="Attachment" class="w-full max-h-56 object-cover rounded-lg border">` : ""}
  ${d.location_url ? `<p class="text-sm"><span class="font-semibold text-gray-600">Location:</span> <a href="${d.location_url}" target="_blank" class="text-brand-blue underline break-all">${d.location_url}</a></p>` : ""}
  <div>
    <p class="text-sm font-semibold text-gray-700 mb-1">Description</p>
    <p class="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-lg p-3">${d.description}</p>
  </div>
  ${d.resolution_note ? `<div class="border-l-4 border-brand-blue pl-4">
    <p class="text-sm font-semibold text-gray-700 mb-1">Resolution / Rejection Note</p>
    <p class="text-sm text-gray-600 whitespace-pre-wrap">${d.resolution_note}</p>
  </div>` : ""}
  <div>
    <p class="text-sm font-semibold text-gray-700 mb-2">Status Timeline</p>
    <div>${timelineHtml}</div>
  </div>
</div>`;
    } catch (err) {
        content.innerHTML = `<p class="text-red-500 text-center py-8">Failed to load details.</p>`;
    }
}

/* ─── Notice view modal ─────────────────────────────────────── */
async function openNoticeView(pk) {
    const content = document.getElementById("nv-content");
    content.innerHTML = `<div class="flex justify-center py-10"><svg class="animate-spin h-7 w-7 text-brand-blue" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg></div>`;
    openModal("modal-view-notice");
    const d = await (await fetch(`/admin-panel/notices/${pk}/json/`)).json();
    content.innerHTML = `
<div class="space-y-4">
  <h3 class="text-xl font-bold text-gray-900">${d.title}</h3>
  <p class="text-xs text-gray-400">Created by ${d.created_by} &bull; Issue date: ${d.issue_date}</p>
  ${d.image ? `<img src="${d.image}" alt="Notice image" class="w-full max-h-56 object-cover rounded-lg border">` : ""}
  <p class="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 rounded-lg p-4">${d.description}</p>
</div>`;
}

/* ─── Job view modal ────────────────────────────────────────── */
async function openJobView(pk) {
    const content = document.getElementById("jv-content");
    content.innerHTML = `<div class="flex justify-center py-10"><svg class="animate-spin h-7 w-7 text-brand-blue" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg></div>`;
    openModal("modal-view-job");
    const d = await (await fetch(`/admin-panel/jobs/${pk}/json/`)).json();
    content.innerHTML = `
<div class="space-y-4">
  <div>
    <h3 class="text-xl font-bold text-gray-900">${d.job_title}</h3>
    <p class="text-sm text-gray-500">${d.department} &bull; ${d.department_location}</p>
  </div>
  <div class="grid grid-cols-2 gap-3 text-xs">
    <div class="bg-gray-50 rounded p-3"><p class="text-gray-400">Issue Date</p><p class="font-semibold">${d.issue_date}</p></div>
    <div class="bg-gray-50 rounded p-3"><p class="text-gray-400">Deadline</p><p class="font-semibold">${d.deadline}</p></div>
    <div class="bg-gray-50 rounded p-3"><p class="text-gray-400">Age Requirement</p><p class="font-semibold">${d.age_requirement}</p></div>
    <div class="bg-gray-50 rounded p-3"><p class="text-gray-400">Status</p><p class="font-semibold">${d.is_active ? 'Active' : 'Closed'}</p></div>
  </div>
  <div><p class="text-sm font-semibold text-gray-700 mb-1">Job Description</p>
    <p class="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-lg p-3">${d.job_description}</p></div>
  <div><p class="text-sm font-semibold text-gray-700 mb-1">Requirements</p>
    <p class="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-lg p-3">${d.job_requirements}</p></div>
  <div><p class="text-sm font-semibold text-gray-700 mb-1">Contact Information</p>
    <p class="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-lg p-3">${d.contact_information}</p></div>
</div>`;
}
