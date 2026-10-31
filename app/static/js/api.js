/**
 * Reusable API Client
 * Wraps browser fetch with JSON parsing and defensive error handling.
 */

async function apiRequest(endpoint, options = {}) {
    const config = {
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        ...options,
    };

    try {
        const response = await fetch(endpoint, config);
        const data = await response.json();

        if (!response.ok) {
            const errorMessage = data && data.message ? data.message : `Server error (Status: ${response.status})`;
            throw new Error(errorMessage);
        }

        return data;
    } catch (err) {
        // Distinguish network failures from application errors
        if (err.name === "TypeError" && err.message.includes("fetch")) {
            throw new Error("Unable to connect to the server. Please check your network or server status.");
        }
        throw err;
    }
}

const API = {
    // Internships
    async getInternships() {
        return apiRequest("/api/internships");
    },

    async getInternship(id) {
        return apiRequest(`/api/internships/${id}`);
    },

    // Students
    async getStudents() {
        return apiRequest("/api/students");
    },

    async getStudent(id) {
        return apiRequest(`/api/students/${id}`);
    },

    async saveStudent(studentData) {
        return apiRequest("/api/students", {
            method: "POST",
            body: JSON.stringify(studentData),
        });
    },

    // Recommendations
    async getRecommendations(payload) {
        return apiRequest("/api/recommend", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },
};
