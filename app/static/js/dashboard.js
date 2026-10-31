/**
 * Dashboard Controller
 * Manages student selection, recommendation requests, score visualization,
 * and safe DOM rendering for eligible vs ineligible listings.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References
    const studentSelect = document.getElementById("studentSelect");
    const discoverBtn = document.getElementById("discoverBtn");
    const editProfileLink = document.getElementById("editProfileLink");
    const studentDetailsCard = document.getElementById("studentDetailsCard");
    const loadingState = document.getElementById("loadingState");
    const alertBox = document.getElementById("alertBox");
    const resultsSection = document.getElementById("resultsSection");
    const resultsMeta = document.getElementById("resultsMeta");
    const countEligible = document.getElementById("countEligible");
    const countIneligible = document.getElementById("countIneligible");
    const eligibleCardsContainer = document.getElementById("eligibleCardsContainer");
    const ineligibleCardsContainer = document.getElementById("ineligibleCardsContainer");
    const emptyEligibleState = document.getElementById("emptyEligibleState");
    const emptyIneligibleState = document.getElementById("emptyIneligibleState");
    const tabEligible = document.getElementById("tabEligible");
    const tabIneligible = document.getElementById("tabIneligible");
    const panelEligible = document.getElementById("panelEligible");
    const panelIneligible = document.getElementById("panelIneligible");

    // Local cached student profiles
    let loadedStudents = [];

    // -------------------------------------------------------------------------
    // 1. Initialize Dashboard & Fetch Students
    // -------------------------------------------------------------------------
    async function initDashboard() {
        try {
            const data = await API.getStudents();
            loadedStudents = data.students || [];

            // Reset select dropdown
            studentSelect.innerHTML = "";
            const defaultOption = document.createElement("option");
            defaultOption.value = "";
            defaultOption.textContent = "-- Select a Student Profile --";
            studentSelect.appendChild(defaultOption);

            loadedStudents.forEach((student) => {
                const opt = document.createElement("option");
                opt.value = student.id;
                opt.textContent = `${student.name} (${student.major}, CGPA: ${student.cgpa.toFixed(2)})`;
                studentSelect.appendChild(opt);
            });

            // If students exist, pre-select target student from URL query or the first one
            if (loadedStudents.length > 0) {
                const urlParams = new URLSearchParams(window.location.search);
                const queryStudentId = parseInt(urlParams.get("student_id"), 10);
                const targetStudent = loadedStudents.find((s) => s.id === queryStudentId) || loadedStudents[0];

                studentSelect.value = targetStudent.id;
                renderStudentSummary(targetStudent);
                discoverBtn.disabled = false;
            }
        } catch (err) {
            showAlert(err.message, "error");
        }
    }

    // -------------------------------------------------------------------------
    // 2. Student Selection Change Handler
    // -------------------------------------------------------------------------
    studentSelect.addEventListener("change", (e) => {
        const studentId = parseInt(e.target.value, 10);
        const selected = loadedStudents.find((s) => s.id === studentId);
        if (selected) {
            renderStudentSummary(selected);
            discoverBtn.disabled = false;
            hideAlert();
        } else {
            studentDetailsCard.classList.add("hidden");
            discoverBtn.disabled = true;
            if (editProfileLink) {
                editProfileLink.href = "/profile";
            }
        }
    });

    function renderStudentSummary(student) {
        if (editProfileLink) {
            editProfileLink.href = `/profile?student_id=${student.id}`;
        }
        document.getElementById("summaryName").textContent = student.name;
        document.getElementById("summaryMajor").textContent = student.major;
        document.getElementById("summaryCgpa").textContent = student.cgpa.toFixed(2);
        document.getElementById("summaryGradYear").textContent = student.graduation_year;
        document.getElementById("summaryWorkMode").textContent = student.preferred_work_mode;
        document.getElementById("summaryLocation").textContent = student.preferred_location;

        const skillsContainer = document.getElementById("summarySkills");
        skillsContainer.innerHTML = "";

        if (student.skills && student.skills.length > 0) {
            student.skills.forEach((s) => {
                const pill = document.createElement("span");
                pill.className = "pill pill-neutral";
                const skillName = typeof s === "string" ? s : s.skill_name;
                const proficiency = typeof s === "object" && s.proficiency_level ? ` (${s.proficiency_level})` : "";
                pill.textContent = `${skillName}${proficiency}`;
                skillsContainer.appendChild(pill);
            });
        } else {
            const emptyPill = document.createElement("span");
            emptyPill.className = "field-hint";
            emptyPill.textContent = "No skills listed yet on this profile.";
            skillsContainer.appendChild(emptyPill);
        }

        studentDetailsCard.classList.remove("hidden");
    }

    // -------------------------------------------------------------------------
    // 3. Recommendation Discovery Trigger
    // -------------------------------------------------------------------------
    discoverBtn.addEventListener("click", async () => {
        const studentId = parseInt(studentSelect.value, 10);
        if (!studentId) return;

        // UI State: Loading
        hideAlert();
        loadingState.classList.remove("hidden");
        resultsSection.classList.add("hidden");
        discoverBtn.disabled = true;

        try {
            const data = await API.getRecommendations({ student_id: studentId });

            renderResults(data);

            resultsSection.classList.remove("hidden");
        } catch (err) {
            showAlert(err.message, "error");
        } finally {
            loadingState.classList.add("hidden");
            discoverBtn.disabled = false;
        }
    });

    // -------------------------------------------------------------------------
    // 4. Safe DOM Rendering of Recommendation Results
    // -------------------------------------------------------------------------
    function renderResults(data) {
        const eligible = data.eligible_recommendations || [];
        const ineligible = data.ineligible_listings || [];

        resultsMeta.textContent = `Evaluated ${data.total_evaluated} sample opportunities for ${data.student_name}. Found ${data.eligible_count} eligible and ${data.ineligible_count} disqualified.`;
        countEligible.textContent = eligible.length;
        countIneligible.textContent = ineligible.length;

        // Render Panel 1: Eligible Cards
        eligibleCardsContainer.innerHTML = "";
        if (eligible.length > 0) {
            emptyEligibleState.classList.add("hidden");
            eligible.forEach((rec) => {
                eligibleCardsContainer.appendChild(createEligibleCard(rec));
            });
        } else {
            emptyEligibleState.classList.remove("hidden");
        }

        // Render Panel 2: Ineligible Cards
        ineligibleCardsContainer.innerHTML = "";
        if (ineligible.length > 0) {
            emptyIneligibleState.classList.add("hidden");
            ineligible.forEach((rec) => {
                ineligibleCardsContainer.appendChild(createIneligibleCard(rec));
            });
        } else {
            emptyIneligibleState.classList.remove("hidden");
        }

        // Default to Eligible tab
        switchTab("eligible");
    }

    function createEligibleCard(rec) {
        const card = document.createElement("article");
        card.className = "opp-card";

        // Header
        const header = document.createElement("div");
        header.className = "opp-header";

        const titleBox = document.createElement("div");
        const title = document.createElement("h3");
        title.className = "opp-title";
        title.textContent = rec.internship_title;
        const org = document.createElement("div");
        org.className = "opp-org";
        org.textContent = rec.organization;
        titleBox.appendChild(title);
        titleBox.appendChild(org);

        // Score display
        const scoreBox = document.createElement("div");
        scoreBox.className = "score-display";
        const scoreNum = document.createElement("div");
        scoreNum.className = "score-number";
        scoreNum.textContent = rec.total_score.toFixed(1);
        const scoreDenom = document.createElement("div");
        scoreDenom.className = "score-denom";
        scoreDenom.textContent = "/ 100";
        const scoreLbl = document.createElement("div");
        scoreLbl.className = "score-label";
        scoreLbl.textContent = "Match Score";
        scoreBox.appendChild(scoreNum);
        scoreBox.appendChild(scoreDenom);
        scoreBox.appendChild(scoreLbl);

        header.appendChild(titleBox);
        header.appendChild(scoreBox);
        card.appendChild(header);

        // Demo Badge
        if (rec.is_demo) {
            const demoBadge = document.createElement("span");
            demoBadge.className = "badge-demo";
            demoBadge.style.display = "inline-block";
            demoBadge.style.marginBottom = "0.5rem";
            demoBadge.textContent = "Demonstration Opportunity";
            card.appendChild(demoBadge);
        }

        // Score Breakdown Accordion
        const breakdownToggle = document.createElement("button");
        breakdownToggle.className = "breakdown-toggle";
        breakdownToggle.type = "button";
        breakdownToggle.textContent = "View Score Breakdown (4 Factors) ▼";

        const breakdownBox = document.createElement("div");
        breakdownBox.className = "breakdown-box hidden";

        const bd = rec.score_breakdown;
        const factors = [
            { label: "Required Skills (45%)", data: bd.required_skills },
            { label: "Preferred Skills (15%)", data: bd.preferred_skills },
            { label: "Academic Alignment (20%)", data: bd.academic_alignment },
            { label: "Location & Mode Match (20%)", data: bd.location_alignment },
        ];

        factors.forEach((f) => {
            const row = document.createElement("div");
            row.className = "breakdown-row";

            const hdr = document.createElement("div");
            hdr.className = "breakdown-header";
            const lbl = document.createElement("span");
            lbl.textContent = f.label;
            const pts = document.createElement("span");
            pts.textContent = `${f.data.points.toFixed(1)} / ${f.data.max_points.toFixed(1)} pts`;
            hdr.appendChild(lbl);
            hdr.appendChild(pts);

            const track = document.createElement("div");
            track.className = "progress-track";
            const fill = document.createElement("div");
            fill.className = "progress-fill";
            const pct = f.data.max_points > 0 ? (f.data.points / f.data.max_points) * 100 : 0;
            fill.style.width = `${Math.min(100, Math.max(0, pct))}%`;
            track.appendChild(fill);

            const detail = document.createElement("div");
            detail.className = "breakdown-detail";
            detail.textContent = f.data.details;

            row.appendChild(hdr);
            row.appendChild(track);
            row.appendChild(detail);
            breakdownBox.appendChild(row);
        });

        breakdownToggle.addEventListener("click", () => {
            const isHidden = breakdownBox.classList.contains("hidden");
            if (isHidden) {
                breakdownBox.classList.remove("hidden");
                breakdownToggle.textContent = "Hide Score Breakdown ▲";
            } else {
                breakdownBox.classList.add("hidden");
                breakdownToggle.textContent = "View Score Breakdown (4 Factors) ▼";
            }
        });

        card.appendChild(breakdownToggle);
        card.appendChild(breakdownBox);

        // Skill Gaps Section
        const skillsSection = document.createElement("div");
        skillsSection.style.marginTop = "0.75rem";
        skillsSection.style.paddingTop = "0.75rem";
        skillsSection.style.borderTop = "1px solid var(--border-color)";

        const gaps = rec.skill_gaps;

        // Matched Required Skills
        if (gaps.matched_required_skills && gaps.matched_required_skills.length > 0) {
            const row = createSkillPillRow("Matched Required:", gaps.matched_required_skills, "pill-matched-req");
            skillsSection.appendChild(row);
        }

        // Missing Required Skills (Critical)
        if (gaps.missing_required_skills && gaps.missing_required_skills.length > 0) {
            const row = createSkillPillRow("Critical Gaps (Missing Mandatory):", gaps.missing_required_skills, "pill-missing-req");
            skillsSection.appendChild(row);
        }

        // Matched Preferred Skills
        if (gaps.matched_preferred_skills && gaps.matched_preferred_skills.length > 0) {
            const row = createSkillPillRow("Matched Preferred:", gaps.matched_preferred_skills, "pill-matched-pref");
            skillsSection.appendChild(row);
        }

        // Missing Preferred Skills
        if (gaps.missing_preferred_skills && gaps.missing_preferred_skills.length > 0) {
            const row = createSkillPillRow("Growth Areas (Missing Preferred):", gaps.missing_preferred_skills, "pill-missing-pref");
            skillsSection.appendChild(row);
        }

        card.appendChild(skillsSection);
        return card;
    }

    function createIneligibleCard(rec) {
        const card = document.createElement("article");
        card.className = "opp-card";
        card.style.borderColor = "#fecaca";

        // Header
        const header = document.createElement("div");
        header.className = "opp-header";

        const titleBox = document.createElement("div");
        const title = document.createElement("h3");
        title.className = "opp-title";
        title.textContent = rec.internship_title;
        const org = document.createElement("div");
        org.className = "opp-org";
        org.textContent = rec.organization;
        titleBox.appendChild(title);
        titleBox.appendChild(org);

        const scoreBox = document.createElement("div");
        scoreBox.className = "score-display";
        const scoreNum = document.createElement("div");
        scoreNum.className = "score-number";
        scoreNum.style.color = "var(--danger)";
        scoreNum.textContent = "0.0";
        const scoreLbl = document.createElement("div");
        scoreLbl.className = "score-label";
        scoreLbl.textContent = "Disqualified";
        scoreBox.appendChild(scoreNum);
        scoreBox.appendChild(scoreLbl);

        header.appendChild(titleBox);
        header.appendChild(scoreBox);
        card.appendChild(header);

        // Demonstration badge
        if (rec.is_demo) {
            const demoBadge = document.createElement("span");
            demoBadge.className = "badge-demo";
            demoBadge.style.display = "inline-block";
            demoBadge.style.marginBottom = "0.5rem";
            demoBadge.textContent = "Demonstration Opportunity";
            card.appendChild(demoBadge);
        }

        // Callout box with explicit rejection reasons
        const callout = document.createElement("div");
        callout.className = "callout-rejection";
        const rTitle = document.createElement("div");
        rTitle.className = "rejection-title";
        rTitle.textContent = "Mandatory Eligibility Rejection Reasons:";
        const rList = document.createElement("ul");
        rList.className = "rejection-list";

        const reasons = rec.eligibility && rec.eligibility.rejection_reasons ? rec.eligibility.rejection_reasons : ["Criteria requirements not satisfied."];
        reasons.forEach((r) => {
            const li = document.createElement("li");
            li.textContent = r;
            rList.appendChild(li);
        });

        callout.appendChild(rTitle);
        callout.appendChild(rList);
        card.appendChild(callout);

        return card;
    }

    function createSkillPillRow(label, skills, pillClass) {
        const container = document.createElement("div");
        container.style.marginBottom = "0.4rem";

        const lbl = document.createElement("span");
        lbl.style.fontSize = "0.75rem";
        lbl.style.fontWeight = "600";
        lbl.style.color = "var(--text-muted)";
        lbl.textContent = label;
        container.appendChild(lbl);

        const pillsDiv = document.createElement("div");
        pillsDiv.className = "pills-container";

        skills.forEach((skill) => {
            const span = document.createElement("span");
            span.className = `pill ${pillClass}`;
            span.textContent = skill;
            pillsDiv.appendChild(span);
        });

        container.appendChild(pillsDiv);
        return container;
    }

    // -------------------------------------------------------------------------
    // 5. Tabs Switching Logic
    // -------------------------------------------------------------------------
    tabEligible.addEventListener("click", () => switchTab("eligible"));
    tabIneligible.addEventListener("click", () => switchTab("ineligible"));

    function switchTab(target) {
        if (target === "eligible") {
            tabEligible.classList.add("active");
            tabEligible.setAttribute("aria-selected", "true");
            tabIneligible.classList.remove("active");
            tabIneligible.setAttribute("aria-selected", "false");
            panelEligible.classList.remove("hidden");
            panelIneligible.classList.add("hidden");
        } else {
            tabIneligible.classList.add("active");
            tabIneligible.setAttribute("aria-selected", "true");
            tabEligible.classList.remove("active");
            tabEligible.setAttribute("aria-selected", "false");
            panelIneligible.classList.remove("hidden");
            panelEligible.classList.add("hidden");
        }
    }

    // -------------------------------------------------------------------------
    // 6. Alert Helpers
    // -------------------------------------------------------------------------
    function showAlert(message, type = "error") {
        alertBox.textContent = message;
        alertBox.className = `alert alert-${type}`;
        alertBox.classList.remove("hidden");
    }

    function hideAlert() {
        alertBox.classList.add("hidden");
    }

    // Kick off initialization
    initDashboard();
});
