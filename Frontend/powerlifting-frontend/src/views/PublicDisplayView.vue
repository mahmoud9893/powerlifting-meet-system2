<template>
  <div class="public-display-container">
    <!-- Add your logo/flag here, for example, right after the main heading -->
    <img
      src="C:\Users\MBR\Documents\PowerliftingApp\Frontend\Public\Images\309183211_398500805821088_2233664516381151015_n.jpg"
      alt="Meet Logo"
      class="meet-logo"
      onerror="this.onerror=null;this.src='https://placehold.co/150x150/cccccc/333333?text=Logo';"
    />
    <!-- Or for a flag:
    <img
      src="/images/your-flag.png"
      alt="Country Flag"
      class="country-flag"
      onerror="this.onerror=null;this.src='https://placehold.co/100x60/cccccc/333333?text=Flag';"
    />
    -->

    <h1>Live Lift Board</h1>

    <div class="meet-state-info">
      <p>
        Current Lift Type:
        <strong>{{ currentMeetState.current_lift_type.toUpperCase() }}</strong>
      </p>
      <p>
        Current Attempt:
        <strong>{{ currentMeetState.current_attempt_number }}</strong>
      </p>
    </div>

    <div v-if="currentLift" class="current-lift-info">
      <h2>CURRENT LIFT</h2>
      <p class="lifter-name">{{ currentLift.lifter_name }}</p>
      <p class="weight-class">({{ currentLift.weight_class_name }})</p>
      <p class="lift-type">{{ currentLift.lift_type.toUpperCase() }}</p>
      <p class="lift-details">
        {{ currentLift.weight_lifted }} kg - Attempt
        {{ currentLift.attempt_number }}
      </p>

      <div class="judge-scores">
        <div class="judge-score-item">
          <span>Judge 1:</span>
          <span :class="getScoreClass(currentLift.judge1_score)">{{
            formatScore(currentLift.judge1_score)
          }}</span>
        </div>
        <div class="judge-score-item">
          <span>Judge 2:</span>
          <span :class="getScoreClass(currentLift.judge2_score)">{{
            formatScore(currentLift.judge2_score)
          }}</span>
        </div>
        <div class="judge-score-item">
          <span>Judge 3:</span>
          <span :class="getScoreClass(currentLift.judge3_score)">{{
            formatScore(currentLift.judge3_score)
          }}</span>
        </div>
      </div>

      <div v-if="currentLift.overall_result !== null" class="overall-result">
        <h2>OVERALL RESULT</h2>
        <p :class="currentLift.overall_result ? 'result-good' : 'result-bad'">
          {{ currentLift.overall_result ? "GOOD LIFT" : "NO LIFT" }}
        </p>
      </div>
      <div v-else class="overall-result">
        <h2>OVERALL RESULT</h2>
        <p class="result-pending">PENDING</p>
      </div>

      <div class="lifter-best-lifts">
        <h3>{{ currentLift.lifter_name }}'s Best Lifts:</h3>
        <div class="best-lifts-grid">
          <div class="best-lift-item">
            <span>Squat:</span>
            <span class="best-lift-value"
              >{{ bestLifts.squat || "N/A" }} kg</span
            >
          </div>
          <div class="best-lift-item">
            <span>Bench:</span>
            <span class="best-lift-value"
              >{{ bestLifts.bench || "N/A" }} kg</span
            >
          </div>
          <div class="best-lift-item">
            <span>Deadlift:</span>
            <span class="best-lift-value"
              >{{ bestLifts.deadlift || "N/A" }} kg</span
            >
          </div>
        </div>
      </div>
    </div>
    <div v-else class="no-current-lift">
      <h2>No Active Lift Currently</h2>
      <p>Please wait for the organizer to set the next lift.</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from "vue";
import { io } from "socket.io-client";

export default {
  name: "PublicDisplayView",
  setup() {
    const currentLift = ref(null);
    const bestLifts = ref({ squat: null, bench: null, deadlift: null });
    const currentMeetState = ref({
      current_lift_type: "squat",
      current_attempt_number: 1,
    });
    let socket = null; // Declare socket here for onUnmounted access

    const fetchCurrentLift = async () => {
      try {
        const response = await fetch("http://localhost:5000/current_lift");
        if (response.ok) {
          const data = await response.json();
          currentLift.value = data;
          if (currentLift.value) {
            fetchLifterAttempts(currentLift.value.lifter_id);
          }
        } else if (response.status === 404) {
          currentLift.value = null; // No active lift found
          bestLifts.value = { squat: null, bench: null, deadlift: null }; // Clear best lifts
        }
      } catch (error) {
        console.error("Error fetching current lift:", error);
      }
    };

    const fetchLifterAttempts = async (lifterId) => {
      try {
        const response = await fetch(
          `http://localhost:5000/lifters/${lifterId}/attempts`
        );
        if (response.ok) {
          const attempts = await response.json();
          const newBestLifts = { squat: null, bench: null, deadlift: null };

          attempts.forEach((attempt) => {
            if (attempt.overall_result === true) {
              // Only count successful lifts
              if (attempt.lift_type === "squat") {
                newBestLifts.squat = Math.max(
                  newBestLifts.squat || 0,
                  attempt.weight_lifted
                );
              } else if (attempt.lift_type === "bench") {
                newBestLifts.bench = Math.max(
                  newBestLifts.bench || 0,
                  attempt.weight_lifted
                );
              } else if (attempt.lift_type === "deadlift") {
                newBestLifts.deadlift = Math.max(
                  newBestLifts.deadlift || 0,
                  attempt.weight_lifted
                );
              }
            }
          });
          bestLifts.value = newBestLifts;
        } else {
          console.error(
            "Failed to fetch lifter attempts:",
            response.statusText
          );
          bestLifts.value = { squat: null, bench: null, deadlift: null };
        }
      } catch (error) {
        console.error("Error fetching lifter attempts:", error);
        bestLifts.value = { squat: null, bench: null, deadlift: null };
      }
    };

    const fetchMeetState = async () => {
      try {
        const response = await fetch("http://localhost:5000/meet_state");
        if (response.ok) {
          const data = await response.json();
          currentMeetState.value = data;
        }
      } catch (error) {
        console.error("Error fetching meet state:", error);
      }
    };

    const formatScore = (score) => {
      if (score === true) return "GOOD";
      if (score === false) return "BAD";
      return "PENDING";
    };

    const getScoreClass = (score) => {
      if (score === true) return "score-good";
      if (score === false) return "score-bad";
      return "score-pending";
    };

    // Watch for changes in currentLift.value.lifter_id to refetch best lifts
    watch(
      () => currentLift.value?.lifter_id,
      (newLifterId, oldLifterId) => {
        if (newLifterId && newLifterId !== oldLifterId) {
          fetchLifterAttempts(newLifterId);
        } else if (!newLifterId) {
          bestLifts.value = { squat: null, bench: null, deadlift: null }; // Clear if no lifter
        }
      }
    );

    onMounted(() => {
      fetchCurrentLift(); // Initial fetch
      fetchMeetState(); // Fetch initial meet state

      // Connect to Socket.IO
      socket = io("http://localhost:5000");

      // Listen for active lift changes
      socket.on("active_lift_changed", (lift) => {
        console.log("Active lift changed via WS:", lift);
        currentLift.value = lift;
        // fetchLifterAttempts will be triggered by the watch effect
      });

      // Listen for lift updates (e.g., judge scores coming in)
      socket.on("lift_updated", (lift) => {
        console.log("Lift updated via WS:", lift);
        if (currentLift.value && currentLift.value.id === lift.id) {
          currentLift.value = lift; // Update current lift details if it's the same lift
          // If the updated lift is the current one and it's completed, refresh best lifts
          if (lift.status === "completed" && lift.overall_result === true) {
            fetchLifterAttempts(lift.lifter_id);
          }
        }
      });

      // Listen for meet state updates (e.g., lift type or attempt number changed by organizer)
      socket.on("meet_state_updated", (state) => {
        console.log("Meet state updated via WS:", state);
        currentMeetState.value = state;
      });
    });

    onUnmounted(() => {
      // Clean up socket listeners when component is unmounted
      if (socket) {
        socket.off("active_lift_changed");
        socket.off("lift_updated");
        socket.off("meet_state_updated");
        socket.disconnect();
      }
    });

    return {
      currentLift,
      bestLifts,
      currentMeetState,
      formatScore,
      getScoreClass,
    };
  },
};
</script>

<style scoped>
.public-display-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background-color: #2c3e50; /* Dark blue/grey */
  color: #ecf0f1; /* Light text */
  font-family: "Inter", sans-serif; /* Use Inter font */
  padding: 20px;
  box-sizing: border-box;
}

/* Style for the logo/flag image */
.meet-logo,
.country-flag {
  max-width: 150px; /* Adjust as needed */
  height: auto;
  margin-bottom: 20px; /* Space below the image */
  border-radius: 8px; /* Slightly rounded corners for aesthetics */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); /* Subtle shadow */
}

h1 {
  font-size: 3.5em;
  color: #f39c12; /* Orange/Gold */
  margin-bottom: 30px;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.4);
}

.meet-state-info {
  background-color: #34495e;
  border-radius: 10px;
  padding: 15px 25px;
  margin-bottom: 30px;
  display: flex;
  gap: 30px;
  font-size: 1.3em;
  color: #bdc3c7;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.meet-state-info strong {
  color: #1abc9c; /* Turquoise */
}

.current-lift-info {
  background-color: #34495e; /* Slightly lighter dark blue */
  border-radius: 15px;
  padding: 40px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 700px;
  text-align: center;
  margin-bottom: 30px;
}

.current-lift-info h2 {
  font-size: 2.5em;
  color: #e74c3c; /* Red */
  margin-bottom: 20px;
  text-transform: uppercase;
}

.lifter-name {
  font-size: 4em;
  font-weight: bold;
  color: #ecf0f1;
  margin-bottom: 10px;
  text-transform: uppercase;
}

.weight-class {
  font-size: 1.8em;
  color: #bdc3c7;
  margin-bottom: 15px;
}

.lift-type {
  font-size: 2.2em;
  font-weight: bold;
  color: #1abc9c; /* Turquoise */
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.lift-details {
  font-size: 2.5em;
  font-weight: bold;
  color: #2ecc71; /* Green */
  margin-bottom: 40px;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
}

.judge-scores {
  display: flex;
  justify-content: space-around;
  margin-bottom: 40px;
  flex-wrap: wrap; /* Allow wrapping on smaller screens */
  gap: 20px;
}

.judge-score-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 1.5em;
  font-weight: bold;
  color: #bdc3c7;
}

.judge-score-item span:first-child {
  margin-bottom: 5px;
}

.judge-score-item span:last-child {
  padding: 10px 20px;
  border-radius: 10px;
  color: white;
  min-width: 120px; /* Ensure consistent button size */
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.score-good {
  background-color: #28a745;
} /* Bootstrap success green */
.score-bad {
  background-color: #dc3545;
} /* Bootstrap danger red */
.score-pending {
  background-color: #ffc107;
  color: #333;
} /* Bootstrap warning yellow */

.overall-result {
  margin-top: 30px;
}

.overall-result h2 {
  font-size: 2.2em;
  color: #f39c12;
  margin-bottom: 15px;
  text-transform: uppercase;
}

.overall-result p {
  font-size: 5em;
  font-weight: bold;
  text-transform: uppercase;
  text-shadow: 4px 4px 8px rgba(0, 0, 0, 0.5);
}

.result-good {
  color: #1abc9c;
} /* Turquoise */
.result-bad {
  color: #e74c3c;
} /* Alizarin red */
.result-pending {
  color: #bdc3c7;
} /* Silver */

.lifter-best-lifts {
  background-color: #2c3e50; /* Darker background for this section */
  border-radius: 10px;
  padding: 25px;
  margin-top: 40px;
  box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.3);
}

.lifter-best-lifts h3 {
  font-size: 1.8em;
  color: #f39c12;
  margin-bottom: 25px;
}

.best-lifts-grid {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 20px;
}

.best-lift-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 1.4em;
  color: #ecf0f1;
}

.best-lift-item span:first-child {
  font-weight: bold;
  margin-bottom: 8px;
  color: #bdc3c7;
}

.best-lift-value {
  font-size: 1.8em;
  font-weight: bold;
  color: #2ecc71; /* Green */
  padding: 8px 15px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.no-current-lift {
  background-color: #34495e;
  border-radius: 15px;
  padding: 50px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
  width: 100%;
  max-width: 700px;
  text-align: center;
  margin-bottom: 30px;
}

.no-current-lift h2 {
  font-size: 2.5em;
  color: #bdc3c7;
  margin-bottom: 20px;
}

.no-current-lift p {
  font-size: 1.5em;
  color: #95a5a6;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .meet-logo,
  .country-flag {
    max-width: 100px; /* Smaller on mobile */
  }

  h1 {
    font-size: 2.5em;
    margin-bottom: 25px;
  }
  .meet-state-info {
    flex-direction: column;
    gap: 10px;
    font-size: 1.1em;
  }
  .current-lift-info {
    padding: 25px;
  }
  .current-lift-info h2 {
    font-size: 2em;
  }
  .lifter-name {
    font-size: 3em;
  }
  .weight-class {
    font-size: 1.5em;
  }
  .lift-type {
    font-size: 1.8em;
  }
  .lift-details {
    font-size: 2em;
  }
  .judge-scores {
    flex-direction: column;
    gap: 15px;
  }
  .judge-score-item span:last-child {
    min-width: unset;
    width: 80%;
  }
  .overall-result p {
    font-size: 4em;
  }
  .lifter-best-lifts {
    padding: 15px;
  }
  .lifter-best-lifts h3 {
    font-size: 1.5em;
  }
  .best-lifts-grid {
    flex-direction: column;
    gap: 15px;
  }
  .best-lift-item {
    font-size: 1.2em;
  }
  .best-lift-value {
    font-size: 1.5em;
  }
  .no-current-lift {
    padding: 30px;
  }
  .no-current-lift h2 {
    font-size: 2em;
  }
  .no-current-lift p {
    font-size: 1.2em;
  }
}
</style>
