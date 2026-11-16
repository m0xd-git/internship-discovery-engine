/**
 * Internships Catalog Controller
 * Manages internship browsing, client-side search, work-mode filtering,
 * expandable role details, and seamless navigation to student recommendations.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References
    const internshipStudentSelect = document.getElementById("internshipStudentSelect");
    const selectedStudentQuickActions = document.getElementById("selectedStudentQuickActions");
    const dashboardDirectLink = document.getElementById("dashboardDirectLink");
    const internshipSearchInput = document.getElementById("internshipSearchInput");
    const clearFiltersBtn = document.getElementById("clearFiltersBtn");
    const resetEmptyBtn = document.getElementById("resetEmptyBtn");
    const filterButtons = document.querySelectorAll(".filter-btn");
    const internshipCountText = document.getElementById("internshipCountText");
    const countModeAll = document.getElementById("countModeAll");
    const countModeRemote = document.getElementById("countModeRemote");
    const countModeHybrid = document.getElementById("countModeHybrid");
    const countModeOnsite = document.getElementById("countModeOnsite");
    const internshipsGrid = document.getElementById("internshipsGrid");
    const emptyInternshipsState = document.getElementById("emptyInternshipsState");
    const loadingInternships = document.getElementById("loadingInternships");
    const internshipAlert = document.getElementById("internshipAlert");

    // State Variables
    let allInternships = [];
    let loadedStudents = [];
    let selectedStudent = null;
    let searchQuery = "";
    let activeWorkMode = "All";

    // -------------------------------------------------------------------------
    // 1. Initialize Page & Data Fetching
    // -------------------------------------------------------------------------
    async function initCatalog() {
        hideAlert();
        loadingInternships.classList.remove("hidden");

        try {
            // Fetch internships and students concurrently
            const [internshipData, studentData] = await Promise.all([
                API.getInternships(),
                API.getStudents(),
            ]);

            allInternships = internshipData.internships || [];
            loadedStudents = studentData.students || [];

            // Populate Student Select Dropdown
            populateStudentSelect();

            // Compute and display work-mode counts
            updateFilterCounts();

            // Initial render
            renderCatalog();
        } catch (err) {
            showAlert(`Failed to load internship opportunities: ${err.message}`, "error");
        } finally {
            loadingInternships.classList.add("hidden");
        }
    }

    // -------------------------------------------------------------------------
    // 2. Student Selection Management
    // -------------------------------------------------------------------------
    function populateStudentSelect() {
        internshipStudentSelect.innerHTML = "";

        const defaultOption = document.createElement("option");
        defaultOption.value = "";
        defaultOption.textContent = "-- Optional: Select a Student to Check Fit --";
        internshipStudentSelect.appendChild(defaultOption);

        loadedStudents.forEach((student) => {
            const opt = document.createElement("option");
            opt.value = student.id;
            opt.textContent = `${student.name} (${student.major}, CGPA: ${student.cgpa.toFixed(2)})`;
            internshipStudentSelect.appendChild(opt);
        });

        // Pre-select student if present in URL query (?student_id=X)
        const urlParams = new URLSearchParams(window.location.search);
        const queryStudentId = parseInt(urlParams.get("student_id"), 10);
        if (queryStudentId) {
            const matchedStudent = loadedStudents.find((s) => s.id === queryStudentId);
            if (matchedStudent) {
                internshipStudentSelect.value = matchedStudent.id;
                setStudentContext(matchedStudent);
            }
        }
    }

    internshipStudentSelect.addEventListener("change", (e) => {
        const studentId = parseInt(e.target.value, 10);
        const matched = loadedStudents.find((s) => s.id === studentId) || null;
        setStudentContext(matched);
        renderCatalog(); // Re-render to update the "View Recommendations" buttons
    });

    function setStudentContext(student) {
        selectedStudent = student;
        if (student) {
            selectedStudentQuickActions.style.display = "block";
            dashboardDirectLink.href = `/?student_id=${student.id}`;
            dashboardDirectLink.textContent = `Go to Dashboard for ${student.name} ➔`;
        } else {
            selectedStudentQuickActions.style.display = "none";
        }
    }

    // -------------------------------------------------------------------------
    // 3. Search & Filter Handlers
    // -------------------------------------------------------------------------
    internshipSearchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.trim().toLowerCase();
        renderCatalog();
    });

    filterButtons.forEach((btn) => {
        btn.setAttribute("aria-pressed", btn.classList.contains("active") ? "true" : "false");
        btn.addEventListener("click", () => {
            filterButtons.forEach((b) => {
                b.classList.remove("active");
                b.setAttribute("aria-pressed", "false");
            });
            btn.classList.add("active");
            btn.setAttribute("aria-pressed", "true");
            activeWorkMode = btn.getAttribute("data-mode") || "All";
            renderCatalog();
        });
    });

    function resetFilters() {
        searchQuery = "";
        internshipSearchInput.value = "";
        activeWorkMode = "All";
        filterButtons.forEach((btn) => {
            const isAll = btn.getAttribute("data-mode") === "All";
            btn.classList.toggle("active", isAll);
            btn.setAttribute("aria-pressed", isAll ? "true" : "false");
        });
        renderCatalog();
    }

    clearFiltersBtn.addEventListener("click", resetFilters);
    if (resetEmptyBtn) {
        resetEmptyBtn.addEventListener("click", resetFilters);
    }

    function updateFilterCounts() {
        countModeAll.textContent = allInternships.length;
        countModeRemote.textContent = allInternships.filter((item) => (item.work_mode || "").toLowerCase() === "remote").length;
        countModeHybrid.textContent = allInternships.filter((item) => (item.work_mode || "").toLowerCase() === "hybrid").length;
        countModeOnsite.textContent = allInternships.filter((item) => (item.work_mode || "").toLowerCase() === "onsite").length;
    }

    // -------------------------------------------------------------------------
    // 4. Catalog Rendering (Safe DOM Construction)
    // -------------------------------------------------------------------------
    function renderCatalog() {
        // Filter logic
        const filtered = allInternships.filter((item) => {
            // Work mode filter
            if (activeWorkMode !== "All") {
                if ((item.work_mode || "").toLowerCase() !== activeWorkMode.toLowerCase()) {
                    return false;
                }
            }

            // Search query filter (title, company, department)
            if (searchQuery) {
                const titleMatch = (item.title || "").toLowerCase().includes(searchQuery);
                const orgMatch = (item.organization || "").toLowerCase().includes(searchQuery);
                const deptMatch = (item.department || "").toLowerCase().includes(searchQuery);
                const skillMatch = (item.required_skills || []).some((s) => s.toLowerCase().includes(searchQuery));
                if (!titleMatch && !orgMatch && !deptMatch && !skillMatch) {
                    return false;
                }
            }

            return true;
        });

        // Update count text
        if (filtered.length === allInternships.length) {
            internshipCountText.textContent = `Showing all ${allInternships.length} opportunities`;
        } else {
            internshipCountText.textContent = `Showing ${filtered.length} of ${allInternships.length} opportunities`;
        }

        // Render Cards
        internshipsGrid.innerHTML = "";

        if (filtered.length === 0) {
            emptyInternshipsState.classList.remove("hidden");
        } else {
            emptyInternshipsState.classList.add("hidden");
            filtered.forEach((internship) => {
                internshipsGrid.appendChild(createInternshipCard(internship));
            });
        }
    }

    function createInternshipCard(item) {
        const card = document.createElement("article");
        card.className = "opp-card internship-catalog-card";

        // 1. Header
        const header = document.createElement("div");
        header.className = "opp-header";

        const titleBox = document.createElement("div");
        const title = document.createElement("h3");
        title.className = "opp-title";
        title.textContent = item.title;

        const orgBox = document.createElement("div");
        orgBox.className = "opp-org";
        const deptStr = item.department ? ` • ${item.department}` : "";
        orgBox.textContent = `${item.organization}${deptStr} • ${item.location}`;

        titleBox.appendChild(title);
        titleBox.appendChild(orgBox);

        // Header Badges Container
        const badgeBox = document.createElement("div");
        badgeBox.style.display = "flex";
        badgeBox.style.flexDirection = "column";
        badgeBox.style.alignItems = "flex-end";
        badgeBox.style.gap = "0.35rem";

        const modeBadge = document.createElement("span");
        modeBadge.className = `badge-workmode badge-workmode-${(item.work_mode || "onsite").toLowerCase()}`;
        modeBadge.textContent = item.work_mode || "Onsite";
        badgeBox.appendChild(modeBadge);

        if (item.is_demo) {
            const demoBadge = document.createElement("span");
            demoBadge.className = "badge-demo";
            demoBadge.textContent = "Demo Listing";
            badgeBox.appendChild(demoBadge);
        }

        header.appendChild(titleBox);
        header.appendChild(badgeBox);
        card.appendChild(header);

        // 2. Key Specifications Grid
        const specsGrid = document.createElement("div");
        specsGrid.className = "catalog-specs-grid";

        specsGrid.appendChild(createSpecItem("💰 Stipend", item.stipend || "Unpaid"));
        specsGrid.appendChild(createSpecItem("🎓 Min CGPA", item.min_cgpa !== undefined ? item.min_cgpa.toFixed(2) : "None"));
        specsGrid.appendChild(createSpecItem("📅 Graduation", `Class of ${item.min_grad_year}–${item.max_grad_year}`));
        specsGrid.appendChild(createSpecItem("⏳ Deadline", item.application_deadline || "Open Enrollment"));

        card.appendChild(specsGrid);

        // 3. Required Skills Preview
        const skillsRow = document.createElement("div");
        skillsRow.className = "catalog-skills-preview";

        const skillsLabel = document.createElement("span");
        skillsLabel.className = "catalog-skills-label";
        skillsLabel.textContent = "Required Skills:";
        skillsRow.appendChild(skillsLabel);

        const pillsContainer = document.createElement("div");
        pillsContainer.className = "pills-container";

        const reqSkills = item.required_skills || [];
        if (reqSkills.length > 0) {
            reqSkills.forEach((skill) => {
                const pill = document.createElement("span");
                pill.className = "pill pill-neutral";
                pill.textContent = skill;
                pillsContainer.appendChild(pill);
            });
        } else {
            const nonePill = document.createElement("span");
            nonePill.className = "field-hint";
            nonePill.textContent = "No specific skills required";
            pillsContainer.appendChild(nonePill);
        }
        skillsRow.appendChild(pillsContainer);
        card.appendChild(skillsRow);

        // 4. Expandable Details Drawer
        const detailsDrawer = document.createElement("div");
        detailsDrawer.className = "catalog-details-drawer hidden";

        // Section A: Description & Core Responsibilities
        const descSection = document.createElement("div");
        descSection.className = "catalog-detail-block";
        const descTitle = document.createElement("h4");
        descTitle.className = "catalog-detail-heading";
        descTitle.textContent = "Role Description & Responsibilities";
        const descText = document.createElement("p");
        descText.className = "catalog-description-text";
        descText.textContent = item.description || "No detailed description provided.";
        descSection.appendChild(descTitle);
        descSection.appendChild(descText);
        detailsDrawer.appendChild(descSection);

        // Section B: Skills Breakdown (Required & Preferred)
        const skillsSection = document.createElement("div");
        skillsSection.className = "catalog-detail-block";
        const skillsTitle = document.createElement("h4");
        skillsTitle.className = "catalog-detail-heading";
        skillsTitle.textContent = "Skill Requirements";
        skillsSection.appendChild(skillsTitle);

        // Required
        const reqDiv = document.createElement("div");
        reqDiv.style.marginBottom = "0.5rem";
        const reqSub = document.createElement("strong");
        reqSub.style.fontSize = "0.8rem";
        reqSub.style.color = "var(--text-main)";
        reqSub.textContent = "Mandatory Technical Skills: ";
        reqDiv.appendChild(reqSub);
        const reqPills = document.createElement("div");
        reqPills.className = "pills-container";
        reqPills.style.marginTop = "0.25rem";
        reqSkills.forEach((s) => {
            const sp = document.createElement("span");
            sp.className = "pill pill-matched-req";
            sp.textContent = `✓ ${s}`;
            reqPills.appendChild(sp);
        });
        reqDiv.appendChild(reqPills);
        skillsSection.appendChild(reqDiv);

        // Preferred
        const prefSkills = item.preferred_skills || [];
        if (prefSkills.length > 0) {
            const prefDiv = document.createElement("div");
            const prefSub = document.createElement("strong");
            prefSub.style.fontSize = "0.8rem";
            prefSub.style.color = "var(--text-main)";
            prefSub.textContent = "Preferred (Nice-to-Have) Skills: ";
            prefDiv.appendChild(prefSub);
            const prefPills = document.createElement("div");
            prefPills.className = "pills-container";
            prefPills.style.marginTop = "0.25rem";
            prefSkills.forEach((s) => {
                const sp = document.createElement("span");
                sp.className = "pill pill-matched-pref";
                sp.textContent = `★ ${s}`;
                prefPills.appendChild(sp);
            });
            prefDiv.appendChild(prefPills);
            skillsSection.appendChild(prefDiv);
        }
        detailsDrawer.appendChild(skillsSection);

        // Section C: Eligibility Rules
        const eligSection = document.createElement("div");
        eligSection.className = "catalog-detail-block";
        const eligTitle = document.createElement("h4");
        eligTitle.className = "catalog-detail-heading";
        eligTitle.textContent = "Eligibility Gatekeeper Criteria";
        eligSection.appendChild(eligTitle);

        const eligList = document.createElement("ul");
        eligList.className = "catalog-eligibility-list";

        const liMajor = document.createElement("li");
        const majors = item.eligible_majors && item.eligible_majors.length > 0
            ? item.eligible_majors.join(", ")
            : "All academic disciplines accepted";
        liMajor.innerHTML = `<strong>Eligible Majors:</strong> `;
        liMajor.appendChild(document.createTextNode(majors));
        eligList.appendChild(liMajor);

        const liCgpa = document.createElement("li");
        liCgpa.innerHTML = `<strong>Minimum Cumulative CGPA:</strong> `;
        liCgpa.appendChild(document.createTextNode(`${item.min_cgpa.toFixed(2)} on a 4.00 scale`));
        eligList.appendChild(liCgpa);

        const liGrad = document.createElement("li");
        liGrad.innerHTML = `<strong>Graduation Range:</strong> `;
        liGrad.appendChild(document.createTextNode(`${item.min_grad_year} through ${item.max_grad_year}`));
        eligList.appendChild(liGrad);

        const liLoc = document.createElement("li");
        liLoc.innerHTML = `<strong>Arrangement & Location:</strong> `;
        liLoc.appendChild(document.createTextNode(`${item.work_mode} (${item.location})`));
        eligList.appendChild(liLoc);

        eligSection.appendChild(eligList);
        detailsDrawer.appendChild(eligSection);

        // Section D: View Recommendations Action (Uses Existing Recommendation System)
        const actionSection = document.createElement("div");
        actionSection.className = "catalog-action-box";

        if (selectedStudent) {
            const actionText = document.createElement("p");
            actionText.style.fontSize = "0.85rem";
            actionText.style.marginBottom = "0.5rem";
            actionText.style.color = "var(--text-main)";
            actionText.textContent = `Selected Student: ${selectedStudent.name} (${selectedStudent.major}, CGPA: ${selectedStudent.cgpa.toFixed(2)})`;

            const recBtn = document.createElement("a");
            recBtn.className = "btn btn-primary";
            recBtn.href = `/?student_id=${selectedStudent.id}`;
            recBtn.textContent = `🎯 View Recommendations for ${selectedStudent.name} on Dashboard ➔`;

            actionSection.appendChild(actionText);
            actionSection.appendChild(recBtn);
        } else {
            const promptText = document.createElement("p");
            promptText.style.fontSize = "0.85rem";
            promptText.style.color = "var(--text-muted)";
            promptText.textContent = "Select a student profile at the top of this page to view personalized recommendation scores and learning roadmaps on the Dashboard.";
            actionSection.appendChild(promptText);
        }
        detailsDrawer.appendChild(actionSection);

        // 5. Expand / Collapse Toggle Button
        const toggleBtn = document.createElement("button");
        toggleBtn.type = "button";
        toggleBtn.className = "breakdown-toggle catalog-toggle-btn";
        toggleBtn.textContent = "View Full Details & Requirements ▼";
        const drawerId = `catalog-drawer-${item.id}`;
        detailsDrawer.id = drawerId;
        toggleBtn.setAttribute("aria-expanded", "false");
        toggleBtn.setAttribute("aria-controls", drawerId);

        toggleBtn.addEventListener("click", () => {
            const isHidden = detailsDrawer.classList.contains("hidden");
            if (isHidden) {
                detailsDrawer.classList.remove("hidden");
                toggleBtn.setAttribute("aria-expanded", "true");
                toggleBtn.textContent = "Hide Full Details ▲";
            } else {
                detailsDrawer.classList.add("hidden");
                toggleBtn.setAttribute("aria-expanded", "false");
                toggleBtn.textContent = "View Full Details & Requirements ▼";
            }
        });

        card.appendChild(toggleBtn);
        card.appendChild(detailsDrawer);

        return card;
    }

    function createSpecItem(label, value) {
        const item = document.createElement("div");
        item.className = "catalog-spec-item";

        const lbl = document.createElement("span");
        lbl.className = "spec-label";
        lbl.textContent = label;

        const val = document.createElement("span");
        val.className = "spec-value";
        val.textContent = value;

        item.appendChild(lbl);
        item.appendChild(val);
        return item;
    }

    // -------------------------------------------------------------------------
    // 5. Alert Helpers
    // -------------------------------------------------------------------------
    function showAlert(message, type = "error") {
        internshipAlert.textContent = message;
        internshipAlert.className = `alert alert-${type}`;
        internshipAlert.classList.remove("hidden");
    }

    function hideAlert() {
        internshipAlert.classList.add("hidden");
    }

    // Initialize Catalog
    initCatalog();
});
