/**
 * Student Profile Controller
 * Manages existing student profile selection, full profile loading,
 * interactive skill management, validation, and persistent storage in SQLite.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Top Profile Selector Elements
    const profileStudentSelect = document.getElementById("profileStudentSelect");
    const createNewProfileBtn = document.getElementById("createNewProfileBtn");

    // Mode Banner Elements
    const profileModeBanner = document.getElementById("profileModeBanner");
    const modeBadge = document.getElementById("modeBadge");
    const modeTitle = document.getElementById("modeTitle");
    const modeDescription = document.getElementById("modeDescription");

    // Form & Alert Elements
    const profileForm = document.getElementById("studentProfileForm");
    const profileAlert = document.getElementById("profileAlert");
    const saveProfileBtn = document.getElementById("saveProfileBtn");

    // Form Field Inputs
    const studentName = document.getElementById("studentName");
    const studentEmail = document.getElementById("studentEmail");
    const studentMajor = document.getElementById("studentMajor");
    const studentCgpa = document.getElementById("studentCgpa");
    const studentGradYear = document.getElementById("studentGradYear");
    const studentWorkMode = document.getElementById("studentWorkMode");
    const studentLocation = document.getElementById("studentLocation");
    const studentBio = document.getElementById("studentBio");

    // Validation Error Spans
    const nameError = document.getElementById("nameError");
    const emailError = document.getElementById("emailError");
    const majorError = document.getElementById("majorError");
    const cgpaError = document.getElementById("cgpaError");
    const gradYearError = document.getElementById("gradYearError");
    const workModeError = document.getElementById("workModeError");
    const locationError = document.getElementById("locationError");

    // Skill Management Elements
    const skillNameInput = document.getElementById("skillNameInput");
    const skillProficiencySelect = document.getElementById("skillProficiencySelect");
    const addSkillBtn = document.getElementById("addSkillBtn");
    const quickChips = document.querySelectorAll(".chip-btn");
    const skillsList = document.getElementById("skillsList");
    const skillCount = document.getElementById("skillCount");
    const noSkillsNotice = document.getElementById("noSkillsNotice");

    // Controller State
    let loadedStudents = [];
    let currentEditingStudentId = null; // null indicates New Student creation mode
    let currentSkills = [];             // Array<{ name: string, proficiency: string }>

    // -------------------------------------------------------------------------
    // 1. Initialize Profile Controller & Load Student List
    // -------------------------------------------------------------------------
    async function initProfile() {
        try {
            const data = await API.getStudents();
            loadedStudents = data.students || [];

            populateStudentDropdown();

            // Check URL query parameters (e.g. ?student_id=2 or ?student_id=new)
            const urlParams = new URLSearchParams(window.location.search);
            const studentIdParam = urlParams.get("student_id") || urlParams.get("id");

            if (studentIdParam === "new") {
                switchToNewStudentMode();
            } else if (studentIdParam) {
                const targetId = parseInt(studentIdParam, 10);
                const found = loadedStudents.find((s) => s.id === targetId);
                if (found) {
                    await loadStudentProfile(targetId);
                } else {
                    showAlert(
                        `Student profile with ID ${studentIdParam} was not found. Loaded default student.`,
                        "warning"
                    );
                    if (loadedStudents.length > 0) {
                        await loadStudentProfile(loadedStudents[0].id);
                    } else {
                        switchToNewStudentMode();
                    }
                }
            } else {
                // Default: If existing student profiles exist, automatically load the first one
                if (loadedStudents.length > 0) {
                    await loadStudentProfile(loadedStudents[0].id);
                } else {
                    switchToNewStudentMode();
                }
            }
        } catch (err) {
            showAlert(`Unable to load student profiles: ${err.message}`, "danger");
            switchToNewStudentMode();
        }
    }

    function populateStudentDropdown() {
        profileStudentSelect.innerHTML = "";

        if (loadedStudents.length === 0) {
            const emptyOpt = document.createElement("option");
            emptyOpt.value = "new";
            emptyOpt.textContent = "-- No Profiles Found (+ Create New Student) --";
            profileStudentSelect.appendChild(emptyOpt);
            return;
        }

        // Add registered students
        loadedStudents.forEach((student) => {
            const opt = document.createElement("option");
            opt.value = student.id;
            opt.textContent = `${student.name} (${student.major}, CGPA: ${student.cgpa.toFixed(2)})`;
            profileStudentSelect.appendChild(opt);
        });

        // Add explicit "+ Create New Student Profile" option
        const newOpt = document.createElement("option");
        newOpt.value = "new";
        newOpt.textContent = "+ Create New Student Profile...";
        profileStudentSelect.appendChild(newOpt);
    }

    // -------------------------------------------------------------------------
    // 2. Load Existing Student Profile by ID
    // -------------------------------------------------------------------------
    async function loadStudentProfile(studentId) {
        clearErrors();
        hideAlert();
        saveProfileBtn.disabled = true;

        try {
            const res = await API.getStudent(studentId);
            const student = res.student;

            if (!student) {
                throw new Error(`Profile for student ID ${studentId} not found.`);
            }

            // Populate form fields
            studentName.value = student.name || "";
            studentEmail.value = student.email || "";
            studentMajor.value = student.major || "";
            studentCgpa.value = student.cgpa !== undefined ? student.cgpa.toFixed(2) : "";
            studentGradYear.value = student.graduation_year || "";
            studentWorkMode.value = student.preferred_work_mode || "Remote";
            studentLocation.value = student.preferred_location || "";
            studentBio.value = student.bio_summary || "";

            // Populate skills
            if (student.skills && Array.isArray(student.skills)) {
                currentSkills = student.skills.map((s) => {
                    if (typeof s === "string") {
                        return { name: s, proficiency: "Intermediate" };
                    }
                    return {
                        name: s.skill_name || s.name || "",
                        proficiency: s.proficiency_level || "Intermediate",
                    };
                }).filter((s) => s.name.length > 0);
            } else {
                currentSkills = [];
            }
            renderSkills();

            // Update mode & state
            currentEditingStudentId = student.id;
            profileStudentSelect.value = student.id;

            profileModeBanner.className = "profile-mode-bar";
            modeBadge.className = "profile-mode-badge";
            modeBadge.textContent = "Editing Profile";
            modeTitle.textContent = `${student.name} (ID: ${student.id})`;
            modeDescription.textContent = "Editing existing profile. Changes will update this SQLite record.";

            saveProfileBtn.querySelector(".btn-text").textContent = "Save Changes (Update Profile)";
            saveProfileBtn.disabled = false;

            // Synchronize browser URL query param without full page reload
            const newUrl = `${window.location.pathname}?student_id=${student.id}`;
            window.history.replaceState({ studentId: student.id }, "", newUrl);
        } catch (err) {
            showAlert(`Error loading student profile: ${err.message}`, "danger");
            saveProfileBtn.disabled = false;
        }
    }

    // -------------------------------------------------------------------------
    // 3. Switch to New Student Creation Mode
    // -------------------------------------------------------------------------
    function switchToNewStudentMode() {
        clearErrors();
        hideAlert();

        // Clear all form fields
        studentName.value = "";
        studentEmail.value = "";
        studentMajor.value = "";
        studentCgpa.value = "";
        studentGradYear.value = "";
        studentWorkMode.value = "Remote";
        studentLocation.value = "";
        studentBio.value = "";

        // Reset skills
        currentSkills = [];
        renderSkills();

        // Update mode & state
        currentEditingStudentId = null;
        profileStudentSelect.value = "new";

        profileModeBanner.className = "profile-mode-bar mode-create";
        modeBadge.className = "profile-mode-badge badge-create";
        modeBadge.textContent = "New Profile";
        modeTitle.textContent = "Creating New Student Profile";
        modeDescription.textContent = "Creating a new candidate. A new record will be added to SQLite upon saving.";

        saveProfileBtn.querySelector(".btn-text").textContent = "Save New Profile to Database";
        saveProfileBtn.disabled = false;

        // Synchronize browser URL query param
        window.history.replaceState({}, "", `${window.location.pathname}?student_id=new`);

        // Focus first field for convenience
        studentName.focus();
    }

    // -------------------------------------------------------------------------
    // 4. Dropdown & Button Event Handlers
    // -------------------------------------------------------------------------
    profileStudentSelect.addEventListener("change", async (e) => {
        const val = e.target.value;
        if (val === "new") {
            switchToNewStudentMode();
        } else if (val) {
            await loadStudentProfile(parseInt(val, 10));
        }
    });

    createNewProfileBtn.addEventListener("click", () => {
        switchToNewStudentMode();
    });

    // -------------------------------------------------------------------------
    // 5. Skill Tag Management Operations
    // -------------------------------------------------------------------------
    function addSkill(name, proficiency = "Intermediate") {
        const trimmed = name.trim();
        if (!trimmed) return;

        // Check for duplicates (case-insensitive)
        const existingIdx = currentSkills.findIndex(
            (s) => s.name.toLowerCase() === trimmed.toLowerCase()
        );

        if (existingIdx >= 0) {
            // Update proficiency level if already present
            currentSkills[existingIdx].proficiency = proficiency;
        } else {
            currentSkills.push({ name: trimmed, proficiency });
        }

        renderSkills();
        skillNameInput.value = "";
        skillNameInput.focus();
    }

    function removeSkill(index) {
        if (index >= 0 && index < currentSkills.length) {
            currentSkills.splice(index, 1);
            renderSkills();
        }
    }

    function renderSkills() {
        skillCount.textContent = currentSkills.length;
        if (currentSkills.length === 0) {
            noSkillsNotice.style.display = "block";
        } else {
            noSkillsNotice.style.display = "none";
        }

        skillsList.innerHTML = "";

        currentSkills.forEach((skill, idx) => {
            const pill = document.createElement("span");
            pill.className = "pill pill-neutral";

            const textSpan = document.createElement("span");
            textSpan.textContent = `${skill.name} (${skill.proficiency})`;
            pill.appendChild(textSpan);

            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "tag-remove";
            removeBtn.setAttribute("aria-label", `Remove ${skill.name}`);
            removeBtn.textContent = "×";
            removeBtn.addEventListener("click", () => removeSkill(idx));

            pill.appendChild(removeBtn);
            skillsList.appendChild(pill);
        });
    }

    // Add skill on button click
    addSkillBtn.addEventListener("click", () => {
        addSkill(skillNameInput.value, skillProficiencySelect.value);
    });

    // Add skill on Enter keypress in skill input (prevents accidental form submission)
    skillNameInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            addSkill(skillNameInput.value, skillProficiencySelect.value);
        }
    });

    // Quick suggestion chips
    quickChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const skillName = chip.getAttribute("data-skill");
            if (skillName) {
                addSkill(skillName, "Intermediate");
            }
        });
    });

    // -------------------------------------------------------------------------
    // 6. Form Validation & Submission
    // -------------------------------------------------------------------------
    function clearErrors() {
        nameError.textContent = "";
        emailError.textContent = "";
        majorError.textContent = "";
        cgpaError.textContent = "";
        gradYearError.textContent = "";
        workModeError.textContent = "";
        locationError.textContent = "";
        hideAlert();
    }

    function validateForm() {
        clearErrors();
        let isValid = true;
        let firstInvalidInput = null;

        // Name
        if (!studentName.value.trim()) {
            nameError.textContent = "Full name is required.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentName;
        }

        // Email
        const email = studentEmail.value.trim();
        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!email) {
            emailError.textContent = "Email address is required.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentEmail;
        } else if (!emailRegex.test(email)) {
            emailError.textContent = "Please enter a valid email address (e.g. name@example.edu).";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentEmail;
        }

        // Major
        if (!studentMajor.value.trim()) {
            majorError.textContent = "Academic major / discipline is required.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentMajor;
        }

        // CGPA
        const cgpa = parseFloat(studentCgpa.value);
        if (isNaN(cgpa)) {
            cgpaError.textContent = "CGPA must be a valid numeric value.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentCgpa;
        } else if (cgpa < 0.0 || cgpa > 4.0) {
            cgpaError.textContent = "CGPA must be between 0.00 and 4.00.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentCgpa;
        }

        // Graduation Year
        const gradYear = parseInt(studentGradYear.value, 10);
        if (isNaN(gradYear)) {
            gradYearError.textContent = "Graduation year must be a valid integer year.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentGradYear;
        } else if (gradYear < 2020 || gradYear > 2035) {
            gradYearError.textContent = "Graduation year must be between 2020 and 2035.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentGradYear;
        }

        // Preferred Work Mode
        const workMode = studentWorkMode.value;
        if (!["Remote", "Hybrid", "Onsite", "Any"].includes(workMode)) {
            workModeError.textContent = "Please select a valid work mode arrangement.";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentWorkMode;
        }

        // Location
        if (!studentLocation.value.trim()) {
            locationError.textContent = "Preferred location is required (e.g. 'Bengaluru, India' or 'Any').";
            isValid = false;
            if (!firstInvalidInput) firstInvalidInput = studentLocation;
        }

        if (firstInvalidInput) {
            firstInvalidInput.focus();
        }

        return isValid;
    }

    profileForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        // Prepare payload
        const payload = {
            name: studentName.value.trim(),
            email: studentEmail.value.trim(),
            major: studentMajor.value.trim(),
            cgpa: parseFloat(studentCgpa.value),
            graduation_year: parseInt(studentGradYear.value, 10),
            preferred_work_mode: studentWorkMode.value,
            preferred_location: studentLocation.value.trim(),
            bio_summary: studentBio.value.trim(),
            skills: currentSkills,
        };

        // If editing an existing profile, include the ID so backend updates rather than duplicates
        if (currentEditingStudentId) {
            payload.id = currentEditingStudentId;
        }

        // UI State: Submitting
        saveProfileBtn.disabled = true;
        const origBtnText = saveProfileBtn.querySelector(".btn-text").textContent;
        saveProfileBtn.querySelector(".btn-text").textContent = currentEditingStudentId
            ? "Updating Profile..."
            : "Saving New Profile...";

        try {
            const result = await API.saveStudent(payload);
            const actionText = currentEditingStudentId ? "updated" : "saved";
            showAlert(
                `Profile for "${result.student.name}" ${actionText} successfully! Redirecting to discovery dashboard...`,
                "success"
            );

            // Redirect back to dashboard to view recommendations for this student
            setTimeout(() => {
                window.location.href = `/?student_id=${result.student.id}`;
            }, 1200);
        } catch (err) {
            showAlert(err.message, "danger");
            saveProfileBtn.disabled = false;
            saveProfileBtn.querySelector(".btn-text").textContent = origBtnText;
        }
    });

    // -------------------------------------------------------------------------
    // 7. Alert Box Helpers
    // -------------------------------------------------------------------------
    function showAlert(message, type = "danger") {
        profileAlert.textContent = message;
        profileAlert.className = `alert alert-${type}`;
        profileAlert.classList.remove("hidden");
    }

    function hideAlert() {
        profileAlert.classList.add("hidden");
    }

    // Kick off initialization
    initProfile();
});
