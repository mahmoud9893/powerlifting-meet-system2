<template>
  <div class="judge-app-container">
    <h1>Judge Scorecard</h1>

    <div v-if="message" :class="['message-box', messageType]">
      {{ message }}
    </div>

    <!-- PIN Entry / Login Screen -->
    <div v-if="!isLoggedIn" class="login-card">
      <h2>Enter Judge PIN</h2>
      <input
        type="password"
        v-model="pinCode"
        placeholder="Enter 4-digit PIN"
        maxlength="4"
        @keyup.enter="handleLogin"
        class="pin-input"
      />
      <button @click="handleLogin" class="login-btn">Login</button>
      <p v-if="loginError" class="error-message">{{ loginError }}</p>
      <p class="info-text">Please contact the organizer for your PIN.</p>
    </div>

    <!-- Main Judge Scorecard (Visible only after successful login) -->
    <div v-else class="scorecard-container">
      <div v-if="currentLift" class="current-lift-card">
        <h2>Current Lifter:</h2>
        <p class="lifter-name">{{ currentLift.lifter_name }}</p>
        <p class="details">
          ID: {{ currentLift.lifter_id_number }} | Gender:
          {{ currentLift.gender }}
        </p>
        <p class="details">
          Weight Class: {{ currentLift.weight_class_name }} | Attempt:
          {{ currentLift.attempt_number }}
        </p>
        <p class="lift-type">{{ currentLift.lift_type.toUpperCase() }}</p>
        <p class="weight-lifted">{{ currentLift.weight_lifted }} kg</p>

        <div class="judge-buttons">
          <button @click="submitScore(true)" class="good-lift-btn">
            <i class="fas fa-check-circle"></i> Good Lift
          </button>
          <button @click="submitScore(false)" class="bad-lift-btn">
            <i class="fas fa-times-circle"></i> No Lift
          </button>
        </div>

        <div class="current-scores">
          <h3>Current Scores:</h3>
          <p>
            Judge 1:
            <span :class="getScoreClass(currentLift.judge1_score)">{{
              formatScore(currentLift.judge1_score)
            }}</span>
          </p>
          <p>
            Judge 2:
            <span :class="getScoreClass(currentLift.judge2_score)">{{
              formatScore(currentLift.judge2_score)
            }}</span>
          </p>
          <p>
            Judge 3:
            <span :class="getScoreClass(currentLift.judge3_score)">{{
              formatScore(currentLift.judge3_score)
            }}</span>
          </p>
          <p v-if="currentLift.overall_result !== null" class="overall-result">
            Overall:
            <span
              :class="currentLift.overall_result ? 'score-good' : 'score-bad'"
              >{{ currentLift.overall_result ? "GOOD" : "NO LIFT" }}</span
            >
          </p>
        </div>
      </div>
      <div v-else class="no-active-lift">
        <p>No active lift currently. Waiting for organizer...</p>
      </div>

      <!-- Judge ID display (now auto-assigned/shown after login) -->
      <div class="judge-id-section">
        <p>
          You are logged in as Judge: <strong>{{ judgeId }}</strong>
        </p>
        <button @click="logout" class="logout-btn">Logout</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from "vue";
import { io } from "socket.io-client";

export default {
  name: "JudgeView",
  setup() {
    const currentLift = ref(null);
    const judgeId = ref(null); // Will be set after successful PIN login
    const isLoggedIn = ref(false); // New: Tracks login state
    const pinCode = ref(""); // New: For PIN input
    const loginError = ref(""); // New: For login error messages

    const message = ref(""); // For custom messages
    const messageType = ref(""); // 'success', 'error', 'warning'
    let socket = null; // Declare socket here for onUnmounted access

    // Function to display messages
    const showMessage = (msg, type = "info") => {
      message.value = msg;
      messageType.value = type;
      setTimeout(() => {
        message.value = "";
        messageType.value = "";
      }, 3000); // Message disappears after 3 seconds
    };

    // New: Handle PIN login
    const handleLogin = async () => {
      loginError.value = ""; // Clear previous errors
      if (!pinCode.value) {
        loginError.value = "Please enter a PIN.";
        return;
      }

      try {
        const response = await fetch("http://192.168.1.21:5000/judge_login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ pin: pinCode.value }),
        });

        if (response.ok) {
          const data = await response.json();
          judgeId.value = data.judge_id;
          isLoggedIn.value = true;
          showMessage(`Logged in as Judge ${judgeId.value}`, "success");
          // Fetch initial lift data once logged in
          fetchCurrentLift();
          // Connect to Socket.IO only after successful login
          connectSocket();
        } else {
          const errorData = await response.json();
          loginError.value = errorData.error || "Login failed.";
          showMessage(`Login failed: ${loginError.value}`, "error");
        }
      } catch (error) {
        console.error("Login error:", error);
        loginError.value = "Network error or unexpected login issue.";
        showMessage("Network error during login.", "error");
      }
    };

    // New: Handle Logout
    const logout = () => {
      isLoggedIn.value = false;
      judgeId.value = null;
      pinCode.value = "";
      currentLift.value = null; // Clear current lift on logout
      if (socket) {
        socket.disconnect(); // Disconnect socket on logout
        socket = null; // Clear socket reference
      }
      showMessage("Logged out successfully.", "info");
    };

    // Function to fetch the current active lift
    const fetchCurrentLift = async () => {
      try {
        const response = await fetch("http://192.168.1.21:5000/current_lift");
        if (response.ok) {
          const data = await response.json();
          currentLift.value = data;
        } else if (response.status === 404) {
          currentLift.value = null;
        }
      } catch (error) {
        console.error("Error fetching current lift:", error);
        showMessage(
          "Error fetching current lift. Please check server connection.",
          "error"
        );
      }
    };

    // Function to submit a judge's score
    const submitScore = async (score) => {
      if (!isLoggedIn.value || !judgeId.value) {
        showMessage(
          "You must be logged in as a Judge to submit scores.",
          "warning"
        );
        return;
      }
      if (!currentLift.value) {
        showMessage("No active lift to score.", "warning");
        return;
      }

      try {
        const payload = {
          lift_id: currentLift.value.id,
          judge_number: judgeId.value,
          score: score, // true for good, false for bad
        };

        const response = await fetch("http://192.168.1.21:5000/submit_score", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (response.ok) {
          const updatedLift = await response.json();
          console.log("Score submitted successfully:", updatedLift);
          showMessage("Score submitted successfully!", "success");
          // The lift_updated WebSocket event will update currentLift.value
        } else {
          const errorData = await response.json();
          console.error("Failed to submit score:", response.status, errorData);
          showMessage(
            `Failed to submit score: ${errorData.error || response.statusText}`,
            "error"
          );
        }
      } catch (error) {
        console.error("Error submitting score:", error);
        showMessage(
          "Network error or unexpected error while submitting score.",
          "error"
        );
      }
    };

    const formatScore = (score) => {
      if (score === true) return "GOOD";
      if (score === false) return "NO LIFT"; // Changed to NO LIFT for judge clarity
      return "PENDING";
    };

    const getScoreClass = (score) => {
      if (score === true) return "score-good";
      if (score === false) return "score-bad";
      return "score-pending";
    };

    // New: Function to connect to Socket.IO
    const connectSocket = () => {
      if (socket && socket.connected) return; // Already connected

      socket = io("http://192.168.1.21:5000");

      socket.on("connect", () => {
        console.log("Judge App connected to backend Socket.IO");
        showMessage("Connected to meet updates.", "info");
      });

      socket.on("disconnect", () => {
        console.log("Judge App disconnected from backend Socket.IO");
        showMessage("Disconnected from meet updates.", "warning");
      });

      // Listen for lift updates (e.g., when judges submit scores or organizer sets new lift)
      socket.on("lift_updated", (lift) => {
        console.log("Lift updated via WS for judge:", lift);
        if (currentLift.value && currentLift.value.id === lift.id) {
          currentLift.value = lift; // Update current lift details
        } else if (lift.status === "active") {
          // If a new lift becomes active, display it
          currentLift.value = lift;
        }
      });

      // Listen for active lift changes (when organizer sets a new lifter)
      socket.on("active_lift_changed", (lift) => {
        console.log("Active lift changed via WS for judge:", lift);
        currentLift.value = lift; // Immediately show the newly active lift
      });
    };

    onMounted(() => {
      // Don't fetch current lift or connect socket immediately on mount
      // Wait for successful login via PIN
    });

    onUnmounted(() => {
      if (socket) {
        socket.off("lift_updated");
        socket.off("active_lift_changed");
        socket.disconnect();
      }
    });

    return {
      currentLift,
      judgeId,
      isLoggedIn,
      pinCode,
      loginError,
      message,
      messageType,
      handleLogin,
      logout,
      submitScore,
      formatScore,
      getScoreClass,
    };
  },
};
</script>

<style scoped>
/* Font Awesome for icons */
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css");

.judge-app-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background-color: #2c3e50; /* Dark background */
  color: #ecf0f1; /* Light text */
  font-family: "Inter", sans-serif; /* Use Inter font */
  text-align: center;
}

h1 {
  font-size: 2.5em;
  color: #f39c12; /* Gold/Orange highlight */
  margin-bottom: 30px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

/* Message Box Styles */
.message-box {
  padding: 10px 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-weight: bold;
  width: 90%;
  max-width: 500px;
  box-sizing: border-box;
  animation: fadeInOut 3s forwards;
}

.message-box.success {
  background-color: #28a745; /* Green */
  color: white;
}

.message-box.error {
  background-color: #dc3545; /* Red */
  color: white;
}

.message-box.warning {
  background-color: #ffc107; /* Yellow */
  color: #333;
}

@keyframes fadeInOut {
  0% {
    opacity: 0;
    transform: translateY(-10px);
  }
  10% {
    opacity: 1;
    transform: translateY(0);
  }
  90% {
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-10px);
  }
}

/* Login Card Styles */
.login-card {
  background-color: #34495e;
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
  width: 100%;
  max-width: 400px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.login-card h2 {
  font-size: 1.8em;
  color: #1abc9c; /* Turquoise */
  margin-bottom: 10px;
}

.pin-input {
  padding: 12px;
  border: 1px solid #555;
  border-radius: 8px;
  font-size: 1.5em;
  text-align: center;
  width: 100%;
  max-width: 200px;
  background-color: #ecf0f1;
  color: #333;
}

.login-btn {
  padding: 12px 25px;
  background-color: #3498db; /* Blue */
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.2em;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.login-btn:hover {
  background-color: #2980b9;
  transform: translateY(-2px);
}

.error-message {
  color: #e74c3c;
  font-weight: bold;
}

.info-text {
  font-size: 0.9em;
  color: #bdc3c7;
}

/* Scorecard Container (holds lift card and judge ID section after login) */
.scorecard-container {
  width: 100%;
  max-width: 500px; /* Keep consistent with login card width for responsive look */
  display: flex;
  flex-direction: column;
  align-items: center;
}

.current-lift-card {
  background-color: #34495e; /* Slightly lighter dark background */
  border-radius: 15px;
  padding: 30px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
  width: 100%;
  margin-bottom: 30px;
  box-sizing: border-box; /* Include padding in width */
}

.current-lift-card h2 {
  font-size: 1.8em;
  color: #e74c3c; /* Red for emphasis */
  margin-bottom: 15px;
}

.lifter-name {
  font-size: 2.8em;
  font-weight: bold;
  color: #ecf0f1;
  margin-bottom: 10px;
  text-transform: uppercase;
}

.details {
  font-size: 1.2em;
  color: #bdc3c7;
  margin-bottom: 15px;
}

.lift-type {
  /* New style for lift type */
  font-size: 2.2em;
  font-weight: bold;
  color: #1abc9c; /* Turquoise */
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.weight-lifted {
  font-size: 3.5em;
  font-weight: bold;
  color: #27ae60; /* Green for weight */
  margin-bottom: 30px;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
}

.judge-buttons {
  display: flex;
  justify-content: space-around;
  gap: 20px;
  margin-bottom: 30px;
}

.judge-buttons button {
  flex: 1;
  padding: 15px 20px;
  border: none;
  border-radius: 10px;
  font-size: 1.3em;
  font-weight: bold;
  cursor: pointer;
  color: white;
  transition: all 0.2s ease-in-out;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.good-lift-btn {
  background: linear-gradient(145deg, #2ecc71, #27ae60); /* Green gradient */
}

.good-lift-btn:hover {
  background: linear-gradient(145deg, #27ae60, #2ecc71);
  transform: translateY(-2px);
}

.bad-lift-btn {
  background: linear-gradient(145deg, #e74c3c, #c0392b); /* Red gradient */
}

.bad-lift-btn:hover {
  background: linear-gradient(145deg, #c0392b, #e74c3c);
  transform: translateY(-2px);
}

.judge-buttons button i {
  font-size: 1.5em;
}

.current-scores {
  background-color: #2c3e50;
  border-radius: 10px;
  padding: 15px;
  margin-top: 20px;
}

.current-scores h3 {
  font-size: 1.2em;
  color: #f39c12;
  margin-bottom: 10px;
}

.current-scores p {
  font-size: 1em;
  margin-bottom: 5px;
}

.current-scores span {
  padding: 3px 8px;
  border-radius: 5px;
  font-weight: bold;
  color: white;
}

.score-good {
  background-color: #2ecc71;
}
.score-bad {
  background-color: #e74c3c;
}
.score-pending {
  background-color: #f1c40f;
  color: #333;
}

.overall-result {
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 15px;
}

.overall-result .score-good {
  background-color: #1abc9c;
}
.overall-result .score-bad {
  background-color: #e74c3c;
}

.no-active-lift {
  background-color: #34495e;
  border-radius: 15px;
  padding: 40px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
  width: 100%;
  box-sizing: border-box;
}

.no-active-lift p {
  font-size: 1.5em;
  color: #bdc3c7;
}

.judge-id-section {
  background-color: #34495e;
  border-radius: 15px;
  padding: 20px;
  margin-top: 30px;
  width: 100%;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.judge-id-section p {
  font-size: 1.2em;
  color: #f39c12;
}

.judge-id-section strong {
  color: #1abc9c;
  font-size: 1.5em;
}

.logout-btn {
  padding: 8px 15px;
  background-color: #95a5a6; /* Grey */
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.logout-btn:hover {
  background-color: #7f8c8d;
  transform: translateY(-1px);
}

/* Responsive adjustments */
@media (max-width: 600px) {
  h1 {
    font-size: 2em;
  }
  .login-card,
  .current-lift-card,
  .no-active-lift,
  .judge-id-section {
    padding: 20px;
  }
  .lifter-name {
    font-size: 2em;
  }
  .weight-lifted {
    font-size: 3em;
  }
  .lift-type {
    font-size: 1.8em;
  }
  .judge-buttons {
    flex-direction: column;
    gap: 15px;
  }
  .judge-buttons button {
    font-size: 1.1em;
    padding: 12px 15px;
  }
  .message-box {
    width: 100%;
    padding: 8px 15px;
  }
  .pin-input {
    font-size: 1.2em;
    padding: 10px;
  }
  .login-btn {
    font-size: 1.1em;
    padding: 10px 20px;
  }
}
</style>
