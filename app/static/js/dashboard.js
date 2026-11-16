/**
 * Dashboard Controller
 * Manages student selection, recommendation requests, score visualization,
 * factor attribution explanations, learning roadmaps, and dedicated modal access.
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

    // Modal DOM Elements
    const roadmapModal = document.getElementById("roadmapModal");
    const closeRoadmapModalBtn = document.getElementById("closeRoadmapModalBtn");
    const modalRoadmapTitle = document.getElementById("modalRoadmapTitle");
    const modalRoadmapSubtitle = document.getElementById("modalRoadmapSubtitle");
    const modalRoadmapBody = document.getElementById("modalRoadmapBody");

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

        const numSkills = student.skills ? student.skills.length : 0;
        const countEl = document.getElementById("summarySkillsCount");
        if (countEl) {
            countEl.textContent = `${numSkills} Skills Listed:`;
        }

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

            renderResults(data, studentId);

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
    function renderResults(data, currentStudentId) {
        const eligible = data.eligible_recommendations || [];
        const ineligible = data.ineligible_listings || [];
        const studentId = currentStudentId || data.student_id;

        resultsMeta.textContent = `Evaluated ${data.total_evaluated} sample opportunities for ${data.student_name}. Found ${data.eligible_count} eligible and ${data.ineligible_count} disqualified.`;
        countEligible.textContent = eligible.length;
        countIneligible.textContent = ineligible.length;

        // Render Panel 1: Eligible Cards
        eligibleCardsContainer.innerHTML = "";
        if (eligible.length > 0) {
            emptyEligibleState.classList.add("hidden");
            eligible.forEach((rec) => {
                eligibleCardsContainer.appendChild(createEligibleCard(rec, studentId));
            });
        } else {
            emptyEligibleState.classList.remove("hidden");
        }

        // Render Panel 2: Ineligible Cards
        ineligibleCardsContainer.innerHTML = "";
        if (ineligible.length > 0) {
            emptyIneligibleState.classList.add("hidden");
            ineligible.forEach((rec) => {
                ineligibleCardsContainer.appendChild(createIneligibleCard(rec, studentId));
            });
        } else {
            emptyIneligibleState.classList.remove("hidden");
        }

        // Default to Eligible tab
        switchTab("eligible");
    }

    function getImpactBadgeClass(impactLevel) {
        switch (impactLevel) {
            case "High Positive Impact":
                return "badge-impact badge-impact-high";
            case "Moderate Positive Impact":
                return "badge-impact badge-impact-moderate";
            case "Low Positive Impact":
                return "badge-impact badge-impact-low";
            case "Disqualified":
                return "badge-impact badge-impact-disqualified";
            default:
                return "badge-impact badge-impact-zero";
        }
    }

    function getMatchTier(score) {
        const s = Number(score);
        if (s >= 75) return { label: "Strong Match", className: "badge-tier badge-tier-strong" };
        if (s >= 50) return { label: "Moderate Match", className: "badge-tier badge-tier-moderate" };
        if (s > 0) return { label: "Partial Match", className: "badge-tier badge-tier-partial" };
        return { label: "Disqualified", className: "badge-tier badge-tier-disqualified" };
    }

    function createEligibleCard(rec, studentId) {
        const card = document.createElement("article");
        card.className = "opp-card";

        // 1. Header (Title, Organization, Location, Score & Tier)
        const header = document.createElement("div");
        header.className = "opp-header";

        const titleBox = document.createElement("div");
        const title = document.createElement("h3");
        title.className = "opp-title";
        title.textContent = rec.internship_title;

        const org = document.createElement("div");
        org.className = "opp-org";
        const metaParts = [rec.organization];
        if (rec.location) metaParts.push(rec.location);
        if (rec.work_mode) metaParts.push(rec.work_mode);
        org.textContent = metaParts.join(" • ");

        titleBox.appendChild(title);
        titleBox.appendChild(org);

        // Score display with qualitative match tier badge
        const scoreBox = document.createElement("div");
        scoreBox.className = "score-display";

        const scoreNum = document.createElement("div");
        scoreNum.className = "score-number";
        scoreNum.textContent = Number(rec.total_score).toFixed(1);

        const scoreDenom = document.createElement("div");
        scoreDenom.className = "score-denom";
        scoreDenom.textContent = "/ 100";

        const tierInfo = getMatchTier(rec.total_score);
        const tierBadge = document.createElement("div");
        tierBadge.className = tierInfo.className;
        tierBadge.textContent = tierInfo.label;

        scoreBox.appendChild(scoreNum);
        scoreBox.appendChild(scoreDenom);
        scoreBox.appendChild(tierBadge);

        header.appendChild(titleBox);
        header.appendChild(scoreBox);
        card.appendChild(header);

        // Demonstration Badge
        if (rec.is_demo) {
            const demoBadge = document.createElement("span");
            demoBadge.className = "badge-demo";
            demoBadge.style.display = "inline-block";
            demoBadge.style.marginBottom = "0.5rem";
            demoBadge.textContent = "Demonstration Opportunity";
            card.appendChild(demoBadge);
        }

        // 2. Recommendation Explanation Rationale (Always Visible)
        if (rec.explanation) {
            const exp = rec.explanation;
            const expBox = document.createElement("div");
            expBox.className = "explanation-box";

            // Headline
            const headlineEl = document.createElement("div");
            headlineEl.className = "explanation-headline";
            headlineEl.textContent = exp.headline || "Recommendation Rationale";
            expBox.appendChild(headlineEl);

            // Strongest Factors Tags
            if (exp.strongest_factors && exp.strongest_factors.length > 0) {
                const sRow = document.createElement("div");
                sRow.className = "strongest-factors-row";
                const sLbl = document.createElement("span");
                sLbl.className = "strongest-factors-label";
                sLbl.textContent = "Top Scoring Drivers:";
                sRow.appendChild(sLbl);

                exp.strongest_factors.forEach((fName) => {
                    const sPill = document.createElement("span");
                    sPill.className = "pill-strongest";
                    sPill.textContent = `★ ${fName}`;
                    sRow.appendChild(sPill);
                });
                expBox.appendChild(sRow);
            }

            // Semantic Fallback Notice if triggered
            if (exp.fallback_summary) {
                const fbBox = document.createElement("div");
                fbBox.style.fontSize = "0.75rem";
                fbBox.style.color = "var(--warning)";
                fbBox.style.marginTop = "0.35rem";
                fbBox.textContent = `⚡ System Notice: ${exp.fallback_summary}`;
                expBox.appendChild(fbBox);
            }

            card.appendChild(expBox);
        }

        // 3. Concise Roadmap Summary Bar (Always Visible)
        const rmSummaryCard = document.createElement("div");
        rmSummaryCard.className = "roadmap-summary-card";

        const rmText = document.createElement("div");
        rmText.className = "roadmap-summary-card-text";

        const rmTitle = document.createElement("div");
        rmTitle.className = "roadmap-summary-card-title";
        const totalDuration = rec.roadmap ? (rec.roadmap.estimated_total_duration || "Self-paced estimate") : "Self-paced estimate";
        rmTitle.textContent = `⏱ Actionable Learning Roadmap: ${totalDuration}`;

        const rmMeta = document.createElement("div");
        rmMeta.className = "roadmap-summary-card-meta";
        const stepCount = rec.roadmap ? rec.roadmap.total_steps : 0;
        const metaBits = [`${stepCount} Pedagogical Steps`];
        if (rec.roadmap && rec.roadmap.injected_prerequisites_count > 0) {
            metaBits.push(`${rec.roadmap.injected_prerequisites_count} Foundational Prerequisite Injected`);
        }
        if (rec.roadmap && rec.roadmap.is_fully_qualified) {
            metaBits.push("100% Skills Matched (Interview Readiness Plan)");
        }
        rmMeta.textContent = metaBits.join(" • ");

        rmText.appendChild(rmTitle);
        rmText.appendChild(rmMeta);
        rmSummaryCard.appendChild(rmText);

        const openModalBtn = document.createElement("button");
        openModalBtn.type = "button";
        openModalBtn.className = "btn-roadmap-primary";
        openModalBtn.textContent = "🗺 Open Full Learning Roadmap Dialog ➔";
        openModalBtn.addEventListener("click", () => {
            openRoadmapModal(studentId, rec.internship_id, openModalBtn);
        });
        rmSummaryCard.appendChild(openModalBtn);

        card.appendChild(rmSummaryCard);

        // 4. Progressive Disclosure Controls Row
        const actionsRow = document.createElement("div");
        actionsRow.className = "card-actions-row";

        const gaps = rec.skill_gaps || {};
        const matchedReq = gaps.matched_required_skills || [];
        const missingReq = gaps.missing_required_skills || [];
        const matchedPref = gaps.matched_preferred_skills || [];
        const missingPref = gaps.missing_preferred_skills || [];

        const totalMatched = matchedReq.length + matchedPref.length;
        const totalGaps = missingReq.length + missingPref.length;

        const factorDrawerId = `factor-drawer-${rec.internship_id}`;
        const skillDrawerId = `skill-drawer-${rec.internship_id}`;

        const factorToggleBtn = document.createElement("button");
        factorToggleBtn.type = "button";
        factorToggleBtn.className = "btn-accordion-toggle";
        factorToggleBtn.textContent = "📊 View Factor Attribution (5 Factors) ▼";
        factorToggleBtn.setAttribute("aria-expanded", "false");
        factorToggleBtn.setAttribute("aria-controls", factorDrawerId);

        const skillToggleBtn = document.createElement("button");
        skillToggleBtn.type = "button";
        skillToggleBtn.className = "btn-accordion-toggle";
        skillToggleBtn.textContent = `🔍 View Skill Gap Analysis (${totalMatched} Matched • ${totalGaps} Gaps) ▼`;
        skillToggleBtn.setAttribute("aria-expanded", "false");
        skillToggleBtn.setAttribute("aria-controls", skillDrawerId);

        actionsRow.appendChild(factorToggleBtn);
        actionsRow.appendChild(skillToggleBtn);
        card.appendChild(actionsRow);

        // 5. Drawer 1: Factor Attribution Breakdown (Expandable)
        const breakdownBox = document.createElement("div");
        breakdownBox.className = "breakdown-box hidden";
        breakdownBox.id = factorDrawerId;

        if (rec.explanation && rec.explanation.factors) {
            const factorsMap = rec.explanation.factors;
            const factorKeys = Object.keys(factorsMap);

            factorKeys.forEach((key) => {
                const factor = factorsMap[key];
                const row = document.createElement("div");
                row.className = "breakdown-row";

                const hdr = document.createElement("div");
                hdr.className = "breakdown-header";

                const lblBox = document.createElement("span");
                lblBox.textContent = `${factor.display_name} (${Number(factor.weight_percentage).toFixed(0)}%)`;

                const rightBox = document.createElement("span");
                rightBox.style.display = "inline-flex";
                rightBox.style.alignItems = "center";
                rightBox.style.gap = "0.5rem";

                const ptsBox = document.createElement("span");
                ptsBox.textContent = `${Number(factor.points_earned).toFixed(1)} / ${Number(factor.max_points).toFixed(1)} pts`;
                rightBox.appendChild(ptsBox);

                const impactBadge = document.createElement("span");
                impactBadge.className = getImpactBadgeClass(factor.impact_level);
                impactBadge.textContent = factor.impact_level;
                rightBox.appendChild(impactBadge);

                hdr.appendChild(lblBox);
                hdr.appendChild(rightBox);

                // Progress Bar
                const track = document.createElement("div");
                track.className = "progress-track";
                const fill = document.createElement("div");
                fill.className = "progress-fill";
                const pct = factor.max_points > 0 ? (factor.points_earned / factor.max_points) * 100 : 0;
                fill.style.width = `${Math.min(100, Math.max(0, pct))}%`;

                if (factor.impact_level === "High Positive Impact") {
                    fill.style.backgroundColor = "var(--success)";
                } else if (factor.impact_level === "Moderate Positive Impact") {
                    fill.style.backgroundColor = "var(--info)";
                } else {
                    fill.style.backgroundColor = "var(--secondary)";
                }
                track.appendChild(fill);

                // Summary detail
                const detail = document.createElement("div");
                detail.className = "breakdown-detail";
                detail.textContent = factor.summary;

                row.appendChild(hdr);
                row.appendChild(track);
                row.appendChild(detail);

                // Semantic AI disclosures
                if (key === "semantic_similarity" && factor.details) {
                    if (factor.details.fallback_applied) {
                        const fbPill = document.createElement("span");
                        fbPill.className = "pill pill-neutral";
                        fbPill.style.marginTop = "0.3rem";
                        fbPill.style.display = "inline-block";
                        fbPill.textContent = "Fallback Active: Scored with 4 Baseline Heuristic Weights";
                        row.appendChild(fbPill);
                    } else if (factor.details.raw_similarity > 0) {
                        const metaBox = document.createElement("div");
                        metaBox.style.marginTop = "0.3rem";
                        metaBox.style.display = "flex";
                        metaBox.style.gap = "0.5rem";
                        metaBox.style.alignItems = "center";
                        metaBox.style.flexWrap = "wrap";

                        const alignBadge = document.createElement("span");
                        alignBadge.className = "pill pill-neutral";
                        alignBadge.textContent = `Alignment: ${factor.details.qualitative_label || "Evaluated"}`;

                        const cosText = document.createElement("span");
                        cosText.style.fontSize = "0.75rem";
                        cosText.style.color = "var(--text-muted)";
                        cosText.textContent = `Cosine Sim: ${Number(factor.details.raw_similarity).toFixed(4)}`;

                        metaBox.appendChild(alignBadge);
                        metaBox.appendChild(cosText);
                        row.appendChild(metaBox);
                    }

                    if (factor.details.notice) {
                        const nEl = document.createElement("div");
                        nEl.className = "field-hint";
                        nEl.style.marginTop = "0.3rem";
                        nEl.style.fontSize = "0.72rem";
                        nEl.style.fontStyle = "italic";
                        nEl.textContent = factor.details.notice;
                        row.appendChild(nEl);
                    }
                }

                breakdownBox.appendChild(row);
            });

            // Ethical Notice
            if (rec.explanation.ethical_notice) {
                const ethBox = document.createElement("div");
                ethBox.className = "ethical-notice-box";
                ethBox.textContent = rec.explanation.ethical_notice;
                breakdownBox.appendChild(ethBox);
            }
        }

        factorToggleBtn.addEventListener("click", () => {
            const isHidden = breakdownBox.classList.contains("hidden");
            if (isHidden) {
                breakdownBox.classList.remove("hidden");
                factorToggleBtn.classList.add("active");
                factorToggleBtn.setAttribute("aria-expanded", "true");
                factorToggleBtn.textContent = "📊 Hide Factor Attribution ▲";
            } else {
                breakdownBox.classList.add("hidden");
                factorToggleBtn.classList.remove("active");
                factorToggleBtn.setAttribute("aria-expanded", "false");
                factorToggleBtn.textContent = "📊 View Factor Attribution (5 Factors) ▼";
            }
        });

        card.appendChild(breakdownBox);

        // 6. Drawer 2: Skill Gaps Section (4 Distinct Categories)
        const skillGapsDrawer = document.createElement("div");
        skillGapsDrawer.className = "skill-gaps-drawer hidden";
        skillGapsDrawer.id = skillDrawerId;

        // 1. Matched Mandatory Skills
        skillGapsDrawer.appendChild(createSkillPillCategory(
            "Matched Mandatory Skills:",
            matchedReq,
            "pill-matched-req",
            "None currently matched"
        ));

        // 2. Critical Gaps (Missing Mandatory — Profile Omissions)
        skillGapsDrawer.appendChild(createSkillPillCategory(
            "Critical Gaps (Missing Mandatory — Profile Omissions):",
            missingReq,
            "pill-missing-req",
            "None! All mandatory skills matched"
        ));

        // 3. Matched Preferred Skills
        skillGapsDrawer.appendChild(createSkillPillCategory(
            "Matched Preferred Bonus Skills:",
            matchedPref,
            "pill-matched-pref",
            "None"
        ));

        // 4. Missing Preferred Skills (Growth Areas)
        skillGapsDrawer.appendChild(createSkillPillCategory(
            "Growth Areas (Missing Preferred):",
            missingPref,
            "pill-missing-pref",
            "None"
        ));

        skillToggleBtn.addEventListener("click", () => {
            const isHidden = skillGapsDrawer.classList.contains("hidden");
            if (isHidden) {
                skillGapsDrawer.classList.remove("hidden");
                skillToggleBtn.classList.add("active");
                skillToggleBtn.setAttribute("aria-expanded", "true");
                skillToggleBtn.textContent = "🔍 Hide Skill Gap Analysis ▲";
            } else {
                skillGapsDrawer.classList.add("hidden");
                skillToggleBtn.classList.remove("active");
                skillToggleBtn.setAttribute("aria-expanded", "false");
                skillToggleBtn.textContent = `🔍 View Skill Gap Analysis (${totalMatched} Matched • ${totalGaps} Gaps) ▼`;
            }
        });

        card.appendChild(skillGapsDrawer);

        return card;
    }

    function createIneligibleCard(rec, studentId) {
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
        const metaParts = [rec.organization];
        if (rec.location) metaParts.push(rec.location);
        if (rec.work_mode) metaParts.push(rec.work_mode);
        org.textContent = metaParts.join(" • ");

        titleBox.appendChild(title);
        titleBox.appendChild(org);

        const scoreBox = document.createElement("div");
        scoreBox.className = "score-display";
        const scoreNum = document.createElement("div");
        scoreNum.className = "score-number";
        scoreNum.style.color = "var(--danger)";
        scoreNum.textContent = "0.0";

        const scoreDenom = document.createElement("div");
        scoreDenom.className = "score-denom";
        scoreDenom.textContent = "/ 100";

        const tierBadge = document.createElement("div");
        tierBadge.className = "badge-tier badge-tier-disqualified";
        tierBadge.textContent = "Disqualified";

        scoreBox.appendChild(scoreNum);
        scoreBox.appendChild(scoreDenom);
        scoreBox.appendChild(tierBadge);

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

        const clarifNotice = document.createElement("div");
        clarifNotice.style.fontSize = "0.75rem";
        clarifNotice.style.marginTop = "0.5rem";
        clarifNotice.style.fontWeight = "600";
        clarifNotice.style.color = "#7f1d1d";
        clarifNotice.textContent = "Important: Learning the missing skills does not automatically resolve academic, graduation-year, major, or work-mode restrictions.";

        callout.appendChild(rTitle);
        callout.appendChild(rList);
        callout.appendChild(clarifNotice);
        card.appendChild(callout);

        // Skill Gaps (Progressive Disclosure)
        const gaps = rec.skill_gaps || {};
        const matchedReq = gaps.matched_required_skills || [];
        const missingReq = gaps.missing_required_skills || [];
        const matchedPref = gaps.matched_preferred_skills || [];
        const missingPref = gaps.missing_preferred_skills || [];

        const totalMatched = matchedReq.length + matchedPref.length;
        const totalGaps = missingReq.length + missingPref.length;

        const actionsRow = document.createElement("div");
        actionsRow.className = "card-actions-row";

        const ineligSkillDrawerId = `inelig-skill-drawer-${rec.internship_id}`;

        const skillToggleBtn = document.createElement("button");
        skillToggleBtn.type = "button";
        skillToggleBtn.className = "btn-accordion-toggle";
        skillToggleBtn.textContent = `🔍 View Skill Gap Analysis (${totalMatched} Matched • ${totalGaps} Gaps) ▼`;
        skillToggleBtn.setAttribute("aria-expanded", "false");
        skillToggleBtn.setAttribute("aria-controls", ineligSkillDrawerId);

        const planBtn = document.createElement("button");
        planBtn.className = "btn-roadmap-modal btn-roadmap-modal-disqualified";
        planBtn.type = "button";
        planBtn.textContent = "📖 Inspect Skill Learning Plan (Educational Only)";
        planBtn.addEventListener("click", () => {
            openRoadmapModal(studentId, rec.internship_id, planBtn);
        });

        actionsRow.appendChild(skillToggleBtn);
        actionsRow.appendChild(planBtn);
        card.appendChild(actionsRow);

        const skillGapsDrawer = document.createElement("div");
        skillGapsDrawer.className = "skill-gaps-drawer hidden";
        skillGapsDrawer.id = ineligSkillDrawerId;

        skillGapsDrawer.appendChild(createSkillPillCategory("Matched Mandatory Skills:", matchedReq, "pill-matched-req", "None"));
        skillGapsDrawer.appendChild(createSkillPillCategory("Critical Gaps (Missing Mandatory — Profile Omissions):", missingReq, "pill-missing-req", "None"));
        skillGapsDrawer.appendChild(createSkillPillCategory("Matched Preferred Bonus Skills:", matchedPref, "pill-matched-pref", "None"));
        skillGapsDrawer.appendChild(createSkillPillCategory("Growth Areas (Missing Preferred):", missingPref, "pill-missing-pref", "None"));

        skillToggleBtn.addEventListener("click", () => {
            const isHidden = skillGapsDrawer.classList.contains("hidden");
            if (isHidden) {
                skillGapsDrawer.classList.remove("hidden");
                skillToggleBtn.classList.add("active");
                skillToggleBtn.setAttribute("aria-expanded", "true");
                skillToggleBtn.textContent = "🔍 Hide Skill Gap Analysis ▲";
            } else {
                skillGapsDrawer.classList.add("hidden");
                skillToggleBtn.classList.remove("active");
                skillToggleBtn.setAttribute("aria-expanded", "false");
                skillToggleBtn.textContent = `🔍 View Skill Gap Analysis (${totalMatched} Matched • ${totalGaps} Gaps) ▼`;
            }
        });

        card.appendChild(skillGapsDrawer);

        return card;
    }

    function createSkillPillCategory(label, skills, pillClass, emptyNote) {
        const container = document.createElement("div");
        container.className = "skill-gap-category";

        const headerRow = document.createElement("div");
        headerRow.className = "skill-gap-category-header";

        const lbl = document.createElement("span");
        lbl.textContent = label;
        headerRow.appendChild(lbl);

        const countBadge = document.createElement("span");
        countBadge.className = "tab-badge";
        countBadge.textContent = skills.length;
        headerRow.appendChild(countBadge);

        container.appendChild(headerRow);

        const pillsDiv = document.createElement("div");
        pillsDiv.className = "pills-container";

        if (skills && skills.length > 0) {
            skills.forEach((skill) => {
                const span = document.createElement("span");
                span.className = `pill ${pillClass}`;
                span.textContent = skill;
                pillsDiv.appendChild(span);
            });
        } else {
            const emptySpan = document.createElement("span");
            emptySpan.className = "field-hint";
            emptySpan.style.margin = "0.2rem 0";
            emptySpan.textContent = emptyNote;
            pillsDiv.appendChild(emptySpan);
        }

        container.appendChild(pillsDiv);
        return container;
    }

    function createSkillPillRow(label, skills, pillClass) {
        return createSkillPillCategory(label, skills, pillClass, "None");
    }

    // -------------------------------------------------------------------------
    // 5. Shared Roadmap Timeline Renderer
    // -------------------------------------------------------------------------
    function renderRoadmapTimeline(roadmap) {
        const container = document.createElement("div");

        // Summary Chips
        const metaChips = document.createElement("div");
        metaChips.className = "roadmap-meta-chips";

        const durChip = document.createElement("span");
        durChip.className = "roadmap-chip";
        durChip.textContent = `⏱ Duration: ${roadmap.estimated_total_duration || "Self-paced"}`;
        metaChips.appendChild(durChip);

        const stepsChip = document.createElement("span");
        stepsChip.className = "roadmap-chip";
        stepsChip.textContent = `📚 Steps: ${roadmap.total_steps || 0}`;
        metaChips.appendChild(stepsChip);

        if (roadmap.mandatory_steps_count !== undefined) {
            const mandChip = document.createElement("span");
            mandChip.className = "roadmap-chip roadmap-chip-mandatory";
            mandChip.textContent = `Mandatory: ${roadmap.mandatory_steps_count}`;
            metaChips.appendChild(mandChip);
        }

        if (roadmap.preferred_steps_count !== undefined) {
            const prefChip = document.createElement("span");
            prefChip.className = "roadmap-chip";
            prefChip.textContent = `Preferred: ${roadmap.preferred_steps_count}`;
            metaChips.appendChild(prefChip);
        }

        if (roadmap.injected_prerequisites_count > 0) {
            const injChip = document.createElement("span");
            injChip.className = "roadmap-chip roadmap-chip-injected";
            injChip.textContent = `Injected Prerequisites: ${roadmap.injected_prerequisites_count}`;
            metaChips.appendChild(injChip);
        }

        container.appendChild(metaChips);

        // Timeline Steps
        const timeline = document.createElement("div");
        timeline.className = "roadmap-timeline";

        const steps = roadmap.steps || [];
        if (steps.length === 0) {
            const emptyMsg = document.createElement("p");
            emptyMsg.className = "field-hint";
            emptyMsg.textContent = "No roadmap steps required for this candidate.";
            timeline.appendChild(emptyMsg);
        } else {
            steps.forEach((step) => {
                const stepItem = document.createElement("div");
                stepItem.className = "timeline-step-item";

                // Marker
                const marker = document.createElement("div");
                marker.className = step.is_prerequisite ? "timeline-step-marker timeline-step-marker-injected" : "timeline-step-marker";
                marker.textContent = step.step_number || "•";
                stepItem.appendChild(marker);

                // Content Box
                const content = document.createElement("div");
                content.className = "timeline-step-content";

                // Header
                const sHeader = document.createElement("div");
                sHeader.className = "step-header";

                const sTitle = document.createElement("h4");
                sTitle.className = "step-title";
                sTitle.textContent = step.skill_name;
                sHeader.appendChild(sTitle);

                const sBadges = document.createElement("div");
                sBadges.className = "step-badges";

                if (step.phase) {
                    const phaseBadge = document.createElement("span");
                    phaseBadge.className = "badge-phase";
                    phaseBadge.textContent = step.phase;
                    sBadges.appendChild(phaseBadge);
                }

                if (step.priority) {
                    const prioBadge = document.createElement("span");
                    if (step.priority.includes("High") || step.priority.includes("Mandatory")) {
                        prioBadge.className = "badge-priority-high";
                    } else if (step.priority.includes("Medium") || step.priority.includes("Growth")) {
                        prioBadge.className = "badge-priority-med";
                    } else {
                        prioBadge.className = "badge-priority-opt";
                    }
                    prioBadge.textContent = step.priority;
                    sBadges.appendChild(prioBadge);
                }

                if (step.is_prerequisite) {
                    const injBadge = document.createElement("span");
                    injBadge.className = "badge-injected";
                    injBadge.textContent = "Supporting Prerequisite";
                    sBadges.appendChild(injBadge);
                } else if (step.origin) {
                    const origBadge = document.createElement("span");
                    origBadge.className = "badge-phase";
                    origBadge.textContent = step.origin;
                    sBadges.appendChild(origBadge);
                }

                sHeader.appendChild(sBadges);
                content.appendChild(sHeader);

                // Duration
                if (step.estimated_duration) {
                    const dur = document.createElement("div");
                    dur.className = "step-duration";
                    dur.textContent = `⏱ Estimated self-study: ${step.estimated_duration}`;
                    content.appendChild(dur);
                }

                // Rationale
                if (step.rationale) {
                    const rat = document.createElement("div");
                    rat.className = "step-rationale";
                    rat.textContent = step.rationale;
                    content.appendChild(rat);
                }

                // Prerequisite dependencies
                if (step.prerequisites && step.prerequisites.length > 0) {
                    const prereqRow = document.createElement("div");
                    prereqRow.className = "prereq-tags-row";
                    const prereqLbl = document.createElement("span");
                    prereqLbl.style.fontSize = "0.72rem";
                    prereqLbl.style.fontWeight = "600";
                    prereqLbl.style.color = "var(--text-muted)";
                    prereqLbl.textContent = "Prerequisites: ";
                    prereqRow.appendChild(prereqLbl);

                    step.prerequisites.forEach((p) => {
                        const tag = document.createElement("span");
                        tag.className = "pill pill-neutral";
                        tag.textContent = p;
                        prereqRow.appendChild(tag);
                    });
                    content.appendChild(prereqRow);
                }

                // Expand/Collapse Details Button
                const hasDetails = (step.learning_focus && step.learning_focus.length > 0) || step.practical_milestone;
                if (hasDetails) {
                    const toggleBtn = document.createElement("button");
                    toggleBtn.className = "step-toggle-btn";
                    toggleBtn.type = "button";
                    toggleBtn.textContent = "View Focus Topics & Milestone ▼";

                    const detailsBox = document.createElement("div");
                    detailsBox.className = "step-details-box hidden";
                    const stepDetailsId = `step-details-${step.step_number || Math.random().toString(36).substr(2, 6)}`;
                    detailsBox.id = stepDetailsId;
                    toggleBtn.setAttribute("aria-expanded", "false");
                    toggleBtn.setAttribute("aria-controls", stepDetailsId);

                    if (step.learning_focus && step.learning_focus.length > 0) {
                        const focusHeading = document.createElement("div");
                        focusHeading.className = "step-section-heading";
                        focusHeading.textContent = "Key Technical Topics to Master:";
                        detailsBox.appendChild(focusHeading);

                        const focusList = document.createElement("ul");
                        focusList.className = "focus-list";
                        step.learning_focus.forEach((item) => {
                            const li = document.createElement("li");
                            li.textContent = item;
                            focusList.appendChild(li);
                        });
                        detailsBox.appendChild(focusList);
                    }

                    if (step.practical_milestone) {
                        const msHeading = document.createElement("div");
                        msHeading.className = "step-section-heading";
                        msHeading.textContent = "Hands-On Project Milestone:";
                        detailsBox.appendChild(msHeading);

                        const msBox = document.createElement("div");
                        msBox.className = "milestone-box";
                        msBox.textContent = `🎯 ${step.practical_milestone}`;
                        detailsBox.appendChild(msBox);
                    }

                    toggleBtn.addEventListener("click", () => {
                        const isHidden = detailsBox.classList.contains("hidden");
                        if (isHidden) {
                            detailsBox.classList.remove("hidden");
                            toggleBtn.setAttribute("aria-expanded", "true");
                            toggleBtn.textContent = "Hide Focus Topics & Milestone ▲";
                        } else {
                            detailsBox.classList.add("hidden");
                            toggleBtn.setAttribute("aria-expanded", "false");
                            toggleBtn.textContent = "View Focus Topics & Milestone ▼";
                        }
                    });

                    content.appendChild(toggleBtn);
                    content.appendChild(detailsBox);
                }

                stepItem.appendChild(content);
                timeline.appendChild(stepItem);
            });
        }

        container.appendChild(timeline);

        // Ethical Notice
        if (roadmap.ethical_notice) {
            const eNotice = document.createElement("div");
            eNotice.className = "ethical-notice-box";
            eNotice.textContent = roadmap.ethical_notice;
            container.appendChild(eNotice);
        }

        return container;
    }

    // -------------------------------------------------------------------------
    // 6. Dedicated Roadmap Modal Dialog Controller (Accessible & Focus-Trapped)
    // -------------------------------------------------------------------------
    let lastActiveTrigger = null;

    async function openRoadmapModal(studentId, internshipId, triggerElement = null) {
        if (!roadmapModal || !modalRoadmapBody) return;

        lastActiveTrigger = triggerElement || document.activeElement;

        modalRoadmapBody.innerHTML = "";
        modalRoadmapTitle.textContent = "Personalized Learning Roadmap";
        modalRoadmapSubtitle.textContent = "Retrieving student profile and calculating progression...";
        roadmapModal.classList.remove("hidden");

        if (closeRoadmapModalBtn) {
            closeRoadmapModalBtn.focus();
        }

        // Spinner state
        const spinnerBox = document.createElement("div");
        spinnerBox.className = "loading-state";
        const spinner = document.createElement("div");
        spinner.className = "spinner";
        const loadingText = document.createElement("p");
        loadingText.textContent = "Computing deterministic prerequisite DAG and self-study milestones...";
        spinnerBox.appendChild(spinner);
        spinnerBox.appendChild(loadingText);
        modalRoadmapBody.appendChild(spinnerBox);

        try {
            const data = await API.getRoadmap(studentId, internshipId);
            modalRoadmapBody.innerHTML = "";

            modalRoadmapTitle.textContent = `${data.internship_title} — Learning Roadmap`;
            modalRoadmapSubtitle.textContent = `Personalized for ${data.student_name} (${data.organization})`;

            // Eligibility context callout
            if (!data.is_eligible) {
                const callout = document.createElement("div");
                callout.className = "educational-callout educational-callout-warning";
                const cHeading = document.createElement("strong");
                cHeading.textContent = "Educational Learning Plan Only: ";
                const cText = document.createElement("span");
                cText.textContent = "The candidate does not currently satisfy mandatory eligibility requirements for this position. This curriculum is provided for self-study and skill growth only; learning these competencies does not confer eligibility.";
                callout.appendChild(cHeading);
                callout.appendChild(cText);

                if (data.eligibility && data.eligibility.rejection_reasons && data.eligibility.rejection_reasons.length > 0) {
                    const rList = document.createElement("ul");
                    rList.style.marginTop = "0.35rem";
                    rList.style.paddingLeft = "1.2rem";
                    data.eligibility.rejection_reasons.forEach((r) => {
                        const li = document.createElement("li");
                        li.textContent = r;
                        rList.appendChild(li);
                    });
                    callout.appendChild(rList);
                }
                modalRoadmapBody.appendChild(callout);
            } else {
                const callout = document.createElement("div");
                callout.className = "educational-callout";
                const cHeading = document.createElement("strong");
                cHeading.textContent = "Personalized Curriculum: ";
                const cText = document.createElement("span");
                cText.textContent = "Sequenced using transitive prerequisite dependency analysis and priority weighting for this specific student-internship pair.";
                callout.appendChild(cHeading);
                callout.appendChild(cText);
                modalRoadmapBody.appendChild(callout);
            }

            if (data.roadmap) {
                modalRoadmapBody.appendChild(renderRoadmapTimeline(data.roadmap));
            } else {
                const emptyP = document.createElement("p");
                emptyP.className = "field-hint";
                emptyP.textContent = "No roadmap data was returned for this opportunity.";
                modalRoadmapBody.appendChild(emptyP);
            }

        } catch (err) {
            modalRoadmapBody.innerHTML = "";
            modalRoadmapSubtitle.textContent = "Unable to load roadmap";
            const errAlert = document.createElement("div");
            errAlert.className = "alert alert-error";
            errAlert.textContent = `Failed to load learning roadmap: ${err.message}`;
            modalRoadmapBody.appendChild(errAlert);
        }
    }

    function closeRoadmapModal() {
        if (roadmapModal) {
            roadmapModal.classList.add("hidden");
        }
        if (lastActiveTrigger && typeof lastActiveTrigger.focus === "function") {
            lastActiveTrigger.focus();
        }
        lastActiveTrigger = null;
    }

    if (closeRoadmapModalBtn) {
        closeRoadmapModalBtn.addEventListener("click", closeRoadmapModal);
    }

    if (roadmapModal) {
        roadmapModal.addEventListener("click", (e) => {
            if (e.target === roadmapModal) {
                closeRoadmapModal();
            }
        });

        // Accessible Focus Trapping inside Roadmap Modal
        roadmapModal.addEventListener("keydown", (e) => {
            if (e.key === "Tab") {
                const focusable = Array.from(
                    roadmapModal.querySelectorAll('button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
                ).filter((el) => el.offsetParent !== null);
                if (focusable.length === 0) return;
                const firstEl = focusable[0];
                const lastEl = focusable[focusable.length - 1];
                if (e.shiftKey && document.activeElement === firstEl) {
                    e.preventDefault();
                    lastEl.focus();
                } else if (!e.shiftKey && document.activeElement === lastEl) {
                    e.preventDefault();
                    firstEl.focus();
                }
            }
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && roadmapModal && !roadmapModal.classList.contains("hidden")) {
            closeRoadmapModal();
        }
    });

    // -------------------------------------------------------------------------
    // 7. Tabs Switching Logic
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
    // 8. Alert Helpers
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
