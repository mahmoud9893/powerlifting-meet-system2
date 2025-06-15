<template>
  <div class="organizer-container">
    <h1>Organizer Dashboard</h1>

    <!-- Meet State and Lift Type Control (Kept at top as it's global) -->
    <section class="meet-control-section">
      <h2>Meet Control</h2>
      <div class="lift-type-selector">
        <label for="liftType">Current Lift Type:</label>
        <select
          id="liftType"
          v-model="currentMeetState.current_lift_type"
          @change="setLiftType"
        >
          <option value="squat">Squat</option>
          <option value="bench">Bench</option>
          <option value="deadlift">Deadlift</option>
        </select>
        <p class="current-type-display">
          Currently focusing on:
          <strong>{{
            currentMeetState.current_lift_type.toUpperCase()
          }}</strong>
        </p>
      </div>

      <div class="attempt-control">
        <h3>
          Current Attempt Number: {{ currentMeetState.current_attempt_number }}
        </h3>
        <button
          @click="advanceAttemptNumber"
          :disabled="currentMeetState.current_attempt_number >= 3"
        >
          Advance to Attempt {{ currentMeetState.current_attempt_number + 1 }}
        </button>
      </div>

      <div class="data-export-section">
        <h3>Data Backup</h3>
        <button @click="exportMeetData" class="export-btn">
          Export All Data to Excel
        </button>
        <p v-if="exportMessage" class="export-message">{{ exportMessage }}</p>
      </div>
    </section>

    <!-- Weight Class Management Section (Moved to top) -->
    <section class="weight-class-management">
      <h2>Weight Class Management</h2>
      <form @submit.prevent="addWeightClass" class="add-wc-form">
        <input
          v-model="newWeightClass.name"
          placeholder="Class Name (e.g., Men's 83kg)"
          required
        />
        <input
          type="number"
          v-model.number="newWeightClass.min_weight"
          placeholder="Min Weight (kg)"
          step="0.01"
          required
        />
        <input
          type="number"
          v-model.number="newWeightClass.max_weight"
          placeholder="Max Weight (kg, leave empty for unlimited)"
          step="0.01"
        />
        <button type="submit">Add Weight Class</button>
      </form>

      <h3>Defined Weight Classes:</h3>
      <ul class="class-list">
        <li v-for="wc in weightClasses" :key="wc.id">
          {{ wc.name }} ({{ wc.min_weight }}kg -
          {{ wc.max_weight || "Unlimited" }}kg)
          <button @click="deleteWeightClass(wc.id)" class="delete-btn">
            Delete
          </button>
        </li>
      </ul>
    </section>

    <!-- NEW: Age Class Management Section (Moved to second) -->
    <section class="age-class-management">
      <h2>Age Class Management</h2>
      <form @submit.prevent="addAgeClass" class="add-ac-form">
        <input
          v-model="newAgeClass.name"
          placeholder="Class Name (e.g., Juniors, 23+)"
          required
        />
        <input
          type="number"
          v-model.number="newAgeClass.min_age"
          placeholder="Min Age"
          required
        />
        <input
          type="number"
          v-model.number="newAgeClass.max_age"
          placeholder="Max Age (leave empty for unlimited)"
        />
        <button type="submit">Add Age Class</button>
      </form>

      <h3>Defined Age Classes:</h3>
      <ul class="class-list">
        <li v-for="ac in ageClasses" :key="ac.id">
          {{ ac.name }} (Age {{ ac.min_age }} - {{ ac.max_age || "Unlimited" }})
          <button @click="deleteAgeClass(ac.id)" class="delete-btn">
            Delete
          </button>
        </li>
      </ul>
    </section>

    <!-- Add New Lifter Section (Moved after class management) -->
    <section class="add-lifter-section">
      <h2>Add New Lifter</h2>
      <form @submit.prevent="addLifter">
        <input v-model="newLifter.name" placeholder="Lifter Name" required />
        <input
          v-model="newLifter.lifter_id_number"
          placeholder="Lifter ID (e.g., JD001)"
          required
        />
        <select v-model="newLifter.gender" required>
          <option value="">Select Gender</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </select>
        <input
          type="number"
          v-model.number="newLifter.actual_weight"
          placeholder="Actual Weight (kg)"
          step="0.1"
          required
        />
        <input
          type="date"
          v-model="newLifter.birth_date"
          placeholder="Birth Date (YYYY-MM-DD)"
          required
        />
        <input
          type="number"
          v-model.number="newLifter.opener_squat"
          placeholder="Opener Squat (kg)"
          step="0.5"
          required
        />
        <input
          type="number"
          v-model.number="newLifter.opener_bench"
          placeholder="Opener Bench (kg)"
          step="0.5"
          required
        />
        <input
          type="number"
          v-model.number="newLifter.opener_deadlift"
          placeholder="Opener Deadlift (kg)"
          step="0.5"
          required
        />
        <button type="submit">Add Lifter</button>
      </form>
    </section>

    <!-- Lifter Queue Section (Moved after adding lifters) -->
    <section class="lifter-queue">
      <h2>
        Lifter Queue ({{ currentMeetState.current_lift_type.toUpperCase() }} -
        Attempt {{ currentMeetState.current_attempt_number }})
      </h2>
      <div v-if="currentLift" class="current-lift">
        <h3>Current Lift:</h3>
        <p>
          {{ currentLift.lifter_name }} ({{ currentLift.weight_class_name }}) -
          {{ currentLift.weight_lifted }}kg - Attempt
          {{ currentLift.attempt_number }}
        </p>
        <div class="scores">
          Judge 1:
          <span :class="getScoreClass(currentLift.judge1_score)">{{
            formatScore(currentLift.judge1_score)
          }}</span>
          | Judge 2:
          <span :class="getScoreClass(currentLift.judge2_score)">{{
            formatScore(currentLift.judge2_score)
          }}</span>
          | Judge 3:
          <span :class="getScoreClass(currentLift.judge3_score)">{{
            formatScore(currentLift.judge3_score)
          }}</span>
        </div>
        <p v-if="currentLift.overall_result !== null" class="overall-result">
          Overall Result:
          <span
            :class="currentLift.overall_result ? 'score-good' : 'score-bad'"
            >{{ currentLift.overall_result ? "GOOD LIFT" : "NO LIFT" }}</span
          >
        </p>
      </div>
      <div v-else class="current-lift">
        <h3>Current Lift:</h3>
        <p>No active lift currently.</p>
      </div>

      <div class="upcoming-lifts">
        <h3>
          Next in Queue (Attempt {{ currentMeetState.current_attempt_number }}):
        </h3>
        <ul v-if="nextLiftsInQueue.length">
          <li v-for="lift in nextLiftsInQueue" :key="lift.id">
            {{ lift.lifter_name }} ({{ lift.weight_class_name }}) -
            {{ lift.weight_lifted }}kg - Attempt
            {{ lift.attempt_number }}
            <button @click="setActiveLift(lift.id)">Set Active</button>
          </li>
        </ul>
        <p v-else>
          No upcoming {{ currentMeetState.current_lift_type }} lifts for Attempt
          {{ currentMeetState.current_attempt_number }} in queue.
        </p>
        <button @click="setActiveLift(null)" class="next-lift-btn">
          Set Next Lift (Auto)
        </button>
      </div>
    </section>

    <!-- All Lifters Section (Moved after lifter queue) -->
    <section class="all-lifters-section">
      <h2>All Registered Lifters</h2>
      <ul>
        <li v-for="lifter in allLifters" :key="lifter.id">
          {{ lifter.name }} (ID: {{ lifter.lifter_id_number }},
          {{ lifter.gender }}, {{ lifter.actual_weight }}kg, Born:
          {{ lifter.birth_date }})
          <br />
          Primary Weight Class:
          <strong>{{ lifter.primary_weight_class_name || "N/A" }}</strong>
          <span
            v-if="
              lifter.additional_weight_class_ids &&
              lifter.additional_weight_class_ids.length
            "
          >
            (Addtl:
            <span
              v-for="(wcId, index) in lifter.additional_weight_class_ids"
              :key="wcId"
            >
              {{ getWeightClassNameById(wcId)
              }}<span
                v-if="index < lifter.additional_weight_class_ids.length - 1"
                >,
              </span> </span
            >)
          </span>
          <br />
          Primary Age Class:
          <strong>{{ lifter.primary_age_class_name || "N/A" }}</strong>
          <span
            v-if="
              lifter.additional_age_class_ids &&
              lifter.additional_age_class_ids.length
            "
          >
            (Addtl:
            <span
              v-for="(acId, index) in lifter.additional_age_class_ids"
              :key="acId"
            >
              {{ getAgeClassNameById(acId)
              }}<span v-if="index < lifter.additional_age_class_ids.length - 1"
                >,
              </span> </span
            >)
          </span>

          <div class="lifter-class-actions">
            <details>
              <summary>Manage Classes</summary>
              <div class="class-selector-group">
                <select v-model="selectedWeightClassToAdd[lifter.id]">
                  <option :value="null">Add Weight Class</option>
                  <option
                    v-for="wc in availableWeightClassesForAdd(lifter)"
                    :key="wc.id"
                    :value="wc.id"
                  >
                    {{ wc.name }} ({{ wc.min_weight }}kg -
                    {{ wc.max_weight || "Unlimited" }}kg)
                  </option>
                </select>
                <button
                  @click="
                    addAdditionalWeightClass(
                      lifter.id,
                      selectedWeightClassToAdd[lifter.id]
                    )
                  "
                  :disabled="!selectedWeightClassToAdd[lifter.id]"
                >
                  Add
                </button>
                <select v-model="selectedWeightClassToRemove[lifter.id]">
                  <option :value="null">Remove Weight Class</option>
                  <option
                    v-for="wcId in lifter.additional_weight_class_ids"
                    :key="wcId"
                    :value="wcId"
                  >
                    {{ getWeightClassNameById(wcId) }}
                  </option>
                </select>
                <button
                  @click="
                    removeAdditionalWeightClass(
                      lifter.id,
                      selectedWeightClassToRemove[lifter.id]
                    )
                  "
                  :disabled="!selectedWeightClassToRemove[lifter.id]"
                >
                  Remove
                </button>
              </div>

              <div class="class-selector-group">
                <select v-model="selectedAgeClassToAdd[lifter.id]">
                  <option :value="null">Add Age Class</option>
                  <option
                    v-for="ac in availableAgeClassesForAdd(lifter)"
                    :key="ac.id"
                    :value="ac.id"
                  >
                    {{ ac.name }} (Age {{ ac.min_age }} -
                    {{ ac.max_age || "Unlimited" }})
                  </option>
                </select>
                <button
                  @click="
                    addAdditionalAgeClass(
                      lifter.id,
                      selectedAgeClassToAdd[lifter.id]
                    )
                  "
                  :disabled="!selectedAgeClassToAdd[lifter.id]"
                >
                  Add
                </button>
                <select v-model="selectedAgeClassToRemove[lifter.id]">
                  <option :value="null">Remove Age Class</option>
                  <option
                    v-for="acId in lifter.additional_age_class_ids"
                    :key="acId"
                    :value="acId"
                  >
                    {{ getAgeClassNameById(acId) }}
                  </option>
                </select>
                <button
                  @click="
                    removeAdditionalAgeClass(
                      lifter.id,
                      selectedAgeClassToRemove[lifter.id]
                    )
                  "
                  :disabled="!selectedAgeClassToRemove[lifter.id]"
                >
                  Remove
                </button>
              </div>
            </details>
          </div>
        </li>
      </ul>
    </section>

    <!-- Meet Rankings Section (Moved to last) -->
    <section class="meet-rankings-section">
      <h2>Meet Rankings</h2>
      <button @click="fetchRankings" class="fetch-rankings-btn">
        Refresh Rankings
      </button>
      <div v-if="Object.keys(rankings).length">
        <div
          v-for="(lifters, wc_name) in rankings"
          :key="wc_name"
          class="weight-class-rankings"
        >
          <h3>{{ wc_name }}</h3>
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Lifter</th>
                <th>Squat</th>
                <th>Bench</th>
                <th>Deadlift</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(lifter, index) in lifters" :key="lifter.id">
                <td>{{ index + 1 }}</td>
                <td>{{ lifter.name }} ({{ lifter.lifter_id_number }})</td>
                <td>{{ lifter.best_squat }}</td>
                <td>{{ lifter.best_bench }}</td>
                <td>{{ lifter.best_deadlift }}</td>
                <td>
                  <strong>{{ lifter.total }}</strong>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <p v-else>No rankings available yet. Ensure lifts are completed.</p>
    </section>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from "vue"; // Added computed
import { io } from "socket.io-client";

export default {
  name: "OrganizerView",
  setup() {
    // --- Reactive State ---
    const allLifters = ref([]);
    const currentLift = ref(null);
    const nextLiftsInQueue = ref([]);
    const newLifter = ref({
      name: "",
      lifter_id_number: "",
      gender: "",
      actual_weight: null,
      birth_date: "", // NEW: Birth Date field
      opener_squat: null,
      opener_bench: null,
      opener_deadlift: null,
    });
    const weightClasses = ref([]);
    const newWeightClass = ref({
      name: "",
      min_weight: null,
      max_weight: null,
    });
    const ageClasses = ref([]); // NEW: Age classes array
    const newAgeClass = ref({
      name: "",
      min_age: null,
      max_age: null,
    });
    const currentMeetState = ref({
      current_lift_type: "squat",
      current_active_lift_id: null,
      current_attempt_number: 1,
    });
    const rankings = ref({});
    const exportMessage = ref(""); // For displaying export success/error

    // For dynamic selection of classes to add/remove for each lifter
    const selectedWeightClassToAdd = ref({});
    const selectedWeightClassToRemove = ref({});
    const selectedAgeClassToAdd = ref({});
    const selectedAgeClassToRemove = ref({});

    const socket = io("http://localhost:5000");

    // --- Functions ---

    const fetchLifters = async () => {
      try {
        const response = await fetch("http://localhost:5000/lifters");
        const data = await response.json();
        allLifters.value = data;
        // Initialize selection states for new lifters
        data.forEach((lifter) => {
          if (!(lifter.id in selectedWeightClassToAdd.value))
            selectedWeightClassToAdd.value[lifter.id] = null;
          if (!(lifter.id in selectedWeightClassToRemove.value))
            selectedWeightClassToRemove.value[lifter.id] = null;
          if (!(lifter.id in selectedAgeClassToAdd.value))
            selectedAgeClassToAdd.value[lifter.id] = null;
          if (!(lifter.id in selectedAgeClassToRemove.value))
            selectedAgeClassToRemove.value[lifter.id] = null;
        });
      } catch (error) {
        console.error("Error fetching lifters:", error);
      }
    };

    const fetchCurrentLift = async () => {
      try {
        const response = await fetch("http://localhost:5000/current_lift");
        if (response.ok) {
          const data = await response.json();
          currentLift.value = data;
        } else if (response.status === 404) {
          currentLift.value = null;
        }
      } catch (error) {
        console.error("Error fetching current lift:", error);
      }
    };

    const fetchNextLiftsInQueue = async () => {
      try {
        await fetch(`http://localhost:5000/next_lift_in_queue`); // Trigger backend queue logic
        const allLiftsResponse = await fetch("http://localhost:5000/lifts");
        if (allLiftsResponse.ok) {
          const allLifts = await allLiftsResponse.json();
          nextLiftsInQueue.value = allLifts
            .filter(
              (lift) =>
                lift.status === "pending" &&
                lift.lift_type === currentMeetState.value.current_lift_type &&
                lift.attempt_number ===
                  currentMeetState.value.current_attempt_number
            )
            .sort((a, b) => {
              if (a.weight_lifted !== b.weight_lifted) {
                return a.weight_lifted - b.weight_lifted;
              }
              if (a.actual_weight !== b.actual_weight) {
                return a.actual_weight - b.actual_weight;
              }
              return (
                new Date(a.timestamp).getTime() -
                new Date(b.timestamp).getTime()
              );
            });
        }
      } catch (error) {
        console.error("Error fetching next lifts in queue:", error);
      }
    };

    const addLifter = async () => {
      try {
        const response = await fetch("http://localhost:5000/lifters", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newLifter.value),
        });
        if (response.ok) {
          const addedLifter = await response.json();
          console.log("Lifter added successfully:", addedLifter);
          newLifter.value = {
            name: "",
            lifter_id_number: "",
            gender: "",
            actual_weight: null,
            birth_date: "",
            opener_squat: null,
            opener_bench: null,
            opener_deadlift: null,
          };
          fetchLifters();
          fetchNextLiftsInQueue();
        } else {
          const errorData = await response.json();
          console.error("Failed to add lifter:", response.status, errorData);
          alert(
            `Failed to add lifter: ${errorData.error || response.statusText}`
          );
        }
      } catch (error) {
        console.error("Error adding lifter (network or unexpected):", error);
        alert("Network error or unexpected error while adding lifter.");
      }
    };

    const setActiveLift = async (liftId = null) => {
      try {
        const payload = liftId ? { lift_id: liftId } : {};
        const response = await fetch(`http://localhost:5000/set_active_lift`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (response.ok) {
          const activatedLift = await response.json();
          console.log("Lift activated:", activatedLift);
          fetchCurrentLift();
          fetchNextLiftsInQueue();
        } else {
          const errorData = await response.json();
          console.error(
            "Failed to set active lift:",
            response.status,
            errorData
          );
          alert(
            `Failed to set active lift: ${
              errorData.error || response.statusText
            }`
          );
        }
      } catch (error) {
        console.error("Error setting active lift:", error);
        alert("Network error or unexpected error while setting active lift.");
      }
    };

    const formatScore = (score) => {
      if (score === true) return "GOOD";
      if (score === false) return "BAD";
      return "Pending";
    };

    const getScoreClass = (score) => {
      if (score === true) return "score-good";
      if (score === false) return "score-bad";
      return "score-pending";
    };

    const fetchWeightClasses = async () => {
      try {
        const response = await fetch("http://localhost:5000/weight_classes");
        const data = await response.json();
        weightClasses.value = data;
      } catch (error) {
        console.error("Error fetching weight classes:", error);
      }
    };

    const addWeightClass = async () => {
      try {
        const response = await fetch("http://localhost:5000/weight_classes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newWeightClass.value),
        });
        if (response.ok) {
          console.log("Weight class added successfully!");
          newWeightClass.value = {
            name: "",
            min_weight: null,
            max_weight: null,
          };
          fetchWeightClasses(); // Refresh list
          fetchLifters(); // Lifters might be re-assigned, refresh them too
        } else {
          const errorData = await response.json();
          console.error(
            "Failed to add weight class:",
            response.status,
            errorData
          );
          alert(
            `Failed to add weight class: ${
              errorData.error || response.statusText
            }`
          );
        }
      } catch (error) {
        console.error("Error adding weight class:", error);
        alert("Network error or unexpected error while adding weight class.");
      }
    };

    const deleteWeightClass = async (wcId) => {
      if (
        !confirm(
          "Are you sure you want to delete this weight class? Lifters in this class will be unassigned or re-assigned."
        )
      ) {
        return;
      }
      try {
        const response = await fetch(
          `http://localhost:5000/weight_classes/${wcId}`,
          {
            method: "DELETE",
          }
        );
        if (response.ok) {
          console.log("Weight class deleted successfully!");
          fetchWeightClasses();
          fetchLifters(); // Lifters might be re-assigned, refresh them too
        } else {
          const errorData = await response.json();
          console.error(
            "Failed to delete weight class:",
            response.status,
            errorData
          );
          alert(
            `Failed to delete weight class: ${
              errorData.error || response.statusText
            }`
          );
        }
      } catch (error) {
        console.error("Error deleting weight class:", error);
        alert("Network error or unexpected error while deleting weight class.");
      }
    };

    // NEW: Age Class Functions
    const fetchAgeClasses = async () => {
      try {
        const response = await fetch("http://localhost:5000/age_classes");
        const data = await response.json();
        ageClasses.value = data;
      } catch (error) {
        console.error("Error fetching age classes:", error);
      }
    };

    const addAgeClass = async () => {
      try {
        const response = await fetch("http://localhost:5000/age_classes", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(newAgeClass.value),
        });
        if (response.ok) {
          console.log("Age class added successfully!");
          newAgeClass.value = { name: "", min_age: null, max_age: null };
          fetchAgeClasses(); // Refresh list
          fetchLifters(); // Lifters might be re-assigned, refresh them too
        } else {
          const errorData = await response.json();
          console.error("Failed to add age class:", response.status, errorData);
          alert(
            `Failed to add age class: ${errorData.error || response.statusText}`
          );
        }
      } catch (error) {
        console.error("Error adding age class:", error);
        alert("Network error or unexpected error while adding age class.");
      }
    };

    const deleteAgeClass = async (acId) => {
      if (
        !confirm(
          "Are you sure you want to delete this age class? Lifters in this class will be unassigned or re-assigned."
        )
      ) {
        return;
      }
      try {
        const response = await fetch(
          `http://localhost:5000/age_classes/${acId}`,
          {
            method: "DELETE",
          }
        );
        if (response.ok) {
          console.log("Age class deleted successfully!");
          fetchAgeClasses();
          fetchLifters(); // Lifters might be re-assigned, refresh them too
        } else {
          const errorData = await response.json();
          console.error(
            "Failed to delete age class:",
            response.status,
            errorData
          );
          alert(
            `Failed to delete age class: ${
              errorData.error || response.statusText
            }`
          );
        }
      } catch (error) {
        console.error("Error deleting age class:", error);
        alert("Network error or unexpected error while deleting age class.");
      }
    };

    // NEW: Multi-Class Management Functions
    const addAdditionalWeightClass = async (lifterId, wcId) => {
      if (!wcId) return;
      try {
        const response = await fetch(
          `http://localhost:5000/lifters/${lifterId}/add_additional_weight_class`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ weight_class_id: wcId }),
          }
        );
        if (response.ok) {
          console.log("Additional weight class added.");
          fetchLifters(); // Re-fetch lifters to update their displayed classes
        } else {
          const errorData = await response.json();
          alert(
            `Failed to add additional weight class: ${
              errorData.error || response.statusText
            }`
          );
        }
        selectedWeightClassToAdd.value[lifterId] = null; // Reset selection
      } catch (error) {
        console.error("Error adding additional weight class:", error);
        alert("Network error or unexpected error.");
      }
    };

    const removeAdditionalWeightClass = async (lifterId, wcId) => {
      if (!wcId) return;
      if (
        !confirm(
          "Are you sure you want to remove this additional weight class?"
        )
      )
        return;
      try {
        const response = await fetch(
          `http://localhost:5000/lifters/${lifterId}/remove_additional_weight_class`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ weight_class_id: wcId }),
          }
        );
        if (response.ok) {
          console.log("Additional weight class removed.");
          fetchLifters();
        } else {
          const errorData = await response.json();
          alert(
            `Failed to remove additional weight class: ${
              errorData.error || response.statusText
            }`
          );
        }
        selectedWeightClassToRemove.value[lifterId] = null; // Reset selection
      } catch (error) {
        console.error("Error removing additional weight class:", error);
        alert("Network error or unexpected error.");
      }
    };

    const addAdditionalAgeClass = async (lifterId, acId) => {
      if (!acId) return;
      try {
        const response = await fetch(
          `http://localhost:5000/lifters/${lifterId}/add_additional_age_class`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ age_class_id: acId }),
          }
        );
        if (response.ok) {
          console.log("Additional age class added.");
          fetchLifters();
        } else {
          const errorData = await response.json();
          alert(
            `Failed to add additional age class: ${
              errorData.error || response.statusText
            }`
          );
        }
        selectedAgeClassToAdd.value[lifterId] = null; // Reset selection: Corrected to use lifterId
      } catch (error) {
        console.error("Error adding additional age class:", error);
        alert("Network error or unexpected error.");
      }
    };

    const removeAdditionalAgeClass = async (lifterId, acId) => {
      if (!acId) return;
      if (
        !confirm("Are you sure you want to remove this additional age class?")
      )
        return;
      try {
        const response = await fetch(
          `http://localhost:5000/lifters/${lifterId}/remove_additional_age_class`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ age_class_id: acId }),
          }
        );
        if (response.ok) {
          console.log("Additional age class removed.");
          fetchLifters();
        } else {
          const errorData = await response.json();
          alert(
            `Failed to remove additional age class: ${
              errorData.error || response.statusText
            }`
          );
        }
        selectedAgeClassToRemove.value[lifterId] = null; // Reset selection: Corrected to use lifterId
      } catch (error) {
        console.error("Error removing additional age class:", error);
        alert("Network error or unexpected error.");
      }
    };

    // Helper to get weight class name by ID
    const getWeightClassNameById = (id) => {
      const wc = weightClasses.value.find((wc) => wc.id === id);
      return wc ? wc.name : "Unknown Weight Class";
    };

    // Helper to get age class name by ID
    const getAgeClassNameById = (id) => {
      const ac = ageClasses.value.find((ac) => ac.id === id);
      return ac ? ac.name : "Unknown Age Class";
    };

    // Computed properties to filter available classes for adding based on rules
    const availableWeightClassesForAdd = computed(() => (lifter) => {
      if (!lifter.primary_weight_class_id) {
        // If no primary, all are available
        return weightClasses.value.filter(
          (wc) => !lifter.additional_weight_class_ids.includes(wc.id)
        );
      }
      const primaryWc = weightClasses.value.find(
        (wc) => wc.id === lifter.primary_weight_class_id
      );
      if (!primaryWc) return [];

      return weightClasses.value.filter(
        (wc) =>
          wc.id !== lifter.primary_weight_class_id && // Not the primary class
          !lifter.additional_weight_class_ids.includes(wc.id) && // Not already an additional class
          wc.min_weight > primaryWc.min_weight // Must be strictly heavier
      );
    });

    const availableAgeClassesForAdd = computed(() => (lifter) => {
      if (!lifter.primary_age_class_id) {
        // If no primary, all are available
        return ageClasses.value.filter(
          (ac) => !lifter.additional_age_class_ids.includes(ac.id)
        );
      }
      const primaryAc = ageClasses.value.find(
        (ac) => ac.id === lifter.primary_age_class_id
      );
      if (!primaryAc) return [];

      return ageClasses.value.filter(
        (ac) =>
          ac.id !== lifter.primary_age_class_id && // Not the primary class
          !lifter.additional_age_class_ids.includes(ac.id) && // Not already an additional class
          ac.min_age > primaryAc.min_age // Must be strictly older
      );
    });

    const fetchMeetState = async () => {
      try {
        const response = await fetch("http://localhost:5000/meet_state");
        if (response.ok) {
          const data = await response.json();
          currentMeetState.value = data;
          fetchNextLiftsInQueue();
        }
      } catch (error) {
        console.error("Error fetching meet state:", error);
      }
    };

    const setLiftType = async () => {
      try {
        const response = await fetch("http://localhost:5000/meet_state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            current_lift_type: currentMeetState.value.current_lift_type,
            current_attempt_number: 1,
          }),
        });
        if (response.ok) {
          console.log("Lift type updated successfully!");
          fetchMeetState();
        } else {
          const errorData = await response.json();
          console.error("Failed to set lift type:", response.status, errorData);
          alert(
            `Failed to set lift type: ${errorData.error || response.statusText}`
          );
        }
      } catch (error) {
        console.error("Error setting lift type:", error);
        alert("Network error or unexpected error while setting lift type.");
      }
    };

    const advanceAttemptNumber = async () => {
      if (currentMeetState.value.current_attempt_number < 3) {
        try {
          const response = await fetch(
            "http://localhost:5000/meet_state/advance_attempt",
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
            }
          );
          if (response.ok) {
            console.log("Attempt number advanced successfully!");
            fetchMeetState();
          } else {
            const errorData = await response.json();
            console.error(
              "Failed to advance attempt:",
              response.status,
              errorData
            );
            alert(
              `Failed to advance attempt: ${
                errorData.error || response.statusText
              }`
            );
          }
        } catch (error) {
          console.error("Error advancing attempt:", error);
          alert("Network error or unexpected error while advancing attempt.");
        }
      } else {
        alert("Cannot advance past Attempt 3.");
      }
    };

    const fetchRankings = async () => {
      try {
        const response = await fetch("http://localhost:5000/rankings");
        if (response.ok) {
          const data = await response.json();
          rankings.value = data;
        } else {
          console.error("Failed to fetch rankings:", response.statusText);
          rankings.value = {};
        }
      } catch (error) {
        console.error("Error fetching rankings:", error);
        rankings.value = {};
      }
    };

    // NEW: Export data to Excel
    const exportMeetData = async () => {
      exportMessage.value = "Exporting data, please wait...";
      try {
        const response = await fetch("http://localhost:5000/export_meet_data");
        if (response.ok) {
          const data = await response.json();
          exportMessage.value = data.message;
          console.log("Export successful:", data);
        } else {
          const errorData = await response.json();
          exportMessage.value = `Export failed: ${
            errorData.error || response.statusText
          }`;
          console.error("Export failed:", response.status, errorData);
        }
      } catch (error) {
        exportMessage.value = `Network error during export: ${error.message}`;
        console.error("Network error during export:", error);
      } finally {
        setTimeout(() => {
          exportMessage.value = "";
        }, 5000); // Clear message after 5 seconds
      }
    };

    // --- Lifecycle Hooks ---
    onMounted(() => {
      fetchLifters();
      fetchWeightClasses();
      fetchAgeClasses(); // NEW: Fetch age classes on mount
      fetchMeetState();
      fetchCurrentLift();

      // Listen for Socket.IO events
      socket.on("lifter_added", (lifter) => {
        console.log("Lifter added via WS:", lifter);
        fetchLifters();
        fetchNextLiftsInQueue();
      });

      // Also listen for lifter_updated, which happens when additional classes are changed
      socket.on("lifter_updated", (lifter) => {
        console.log("Lifter updated via WS:", lifter);
        fetchLifters(); // Re-fetch all lifters to reflect class changes
      });

      socket.on("active_lift_changed", (lift) => {
        console.log("Active lift changed via WS:", lift);
        fetchCurrentLift();
        fetchNextLiftsInQueue();
      });

      socket.on("lift_updated", (lift) => {
        console.log("Lift updated via WS:", lift);
        if (currentLift.value && currentLift.value.id === lift.id) {
          currentLift.value = lift;
        }
        fetchNextLiftsInQueue();
        fetchRankings();
      });

      socket.on("meet_state_updated", (state) => {
        console.log("Meet state updated via WS:", state);
        currentMeetState.value = state;
        fetchNextLiftsInQueue();
      });
    });

    onUnmounted(() => {
      if (socket) {
        socket.off("lifter_added");
        socket.off("lifter_updated"); // Clean up new listener
        socket.off("active_lift_changed");
        socket.off("lift_updated");
        socket.off("meet_state_updated");
        socket.disconnect();
      }
    });

    // --- Expose to Template ---
    return {
      allLifters,
      currentLift,
      nextLiftsInQueue,
      newLifter,
      weightClasses,
      newWeightClass,
      ageClasses, // Expose new age classes
      newAgeClass, // Expose new age class form data
      currentMeetState,
      rankings,
      exportMessage, // Expose export message

      selectedWeightClassToAdd,
      selectedWeightClassToRemove,
      selectedAgeClassToAdd,
      selectedAgeClassToRemove,

      addLifter,
      setActiveLift,
      formatScore,
      getScoreClass,
      addWeightClass,
      deleteWeightClass,
      fetchAgeClasses, // Expose new functions
      addAgeClass,
      deleteAgeClass,
      addAdditionalWeightClass,
      removeAdditionalWeightClass,
      addAdditionalAgeClass,
      removeAdditionalAgeClass,
      getWeightClassNameById, // Expose new helpers
      getAgeClassNameById,
      availableWeightClassesForAdd, // Expose computed properties
      availableAgeClassesForAdd,

      setLiftType,
      advanceAttemptNumber,
      fetchRankings,
      exportMeetData, // Expose export function
    };
  },
};
</script>

<style scoped>
.organizer-container {
  max-width: 1000px;
  margin: 20px auto;
  padding: 20px;
  background-color: #f0f2f5; /* Lighter background */
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-family: "Inter", sans-serif;
  color: #333;
}

h1 {
  font-size: 2.8em;
  color: #2c3e50; /* Dark blue/grey */
  text-align: center;
  margin-bottom: 30px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

h2 {
  font-size: 1.8em;
  color: #34495e;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 10px;
}

h3 {
  font-size: 1.4em;
  color: #555;
  margin-top: 25px;
  margin-bottom: 15px;
}

section {
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Form Styles */
form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
}

form input,
form select {
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1em;
  width: 100%;
  box-sizing: border-box;
}

form button {
  grid-column: span 2; /* Button spans both columns */
  padding: 12px 20px;
  background-color: #3498db; /* Blue */
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1em;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

form button:hover {
  background-color: #2980b9;
  transform: translateY(-1px);
}

/* Specific form adjustments */
.add-lifter-section form {
  grid-template-columns: 1fr 1fr; /* Two columns for lifter details */
}

.add-lifter-section form input[type="date"] {
  grid-column: span 1; /* Keep date in its own column */
}

.add-lifter-section form input[placeholder*="Opener"] {
  grid-column: span 1; /* Keep openers in two columns */
}

.add-lifter-section form button {
  grid-column: span 2;
}

.add-wc-form,
.add-ac-form {
  grid-template-columns: repeat(
    auto-fit,
    minmax(150px, 1fr)
  ); /* Flexible columns */
}

.add-wc-form button,
.add-ac-form button {
  grid-column: span full; /* Button spans all columns */
}

/* Meet Control Section */
.meet-control-section {
  text-align: center;
}

.lift-type-selector label {
  font-size: 1.1em;
  margin-right: 10px;
  color: #555;
}

.lift-type-selector select {
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #ddd;
  font-size: 1em;
  background-color: #f9f9f9;
}

.current-type-display {
  margin-top: 15px;
  font-size: 1.2em;
  color: #2c3e50;
}

.current-type-display strong {
  color: #e74c3c; /* Red for emphasis */
}

.attempt-control {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #e0e0e0;
}

.attempt-control h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #34495e;
}

.attempt-control button {
  padding: 10px 20px;
  background-color: #f39c12; /* Orange */
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1em;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.attempt-control button:hover:not(:disabled) {
  background-color: #e67e22;
  transform: translateY(-1px);
}

.attempt-control button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

/* Data Export Section */
.data-export-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.data-export-section .export-btn {
  background-color: #2ecc71; /* Green */
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1em;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.data-export-section .export-btn:hover {
  background-color: #27ae60;
  transform: translateY(-1px);
}

.export-message {
  margin-top: 15px;
  font-weight: bold;
  color: #3498db; /* Blue */
}

/* Current Lift Display */
.current-lift {
  background-color: #ecf0f1; /* Light grey */
  border: 1px solid #bdc3c7;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
}

.current-lift h3 {
  color: #2c3e50;
  margin-top: 0;
  margin-bottom: 10px;
}

.current-lift p {
  font-size: 1.1em;
  margin-bottom: 8px;
}

.current-lift .scores {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
  font-size: 1em;
}

.current-lift .scores span {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: bold;
  color: white;
  min-width: 80px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.score-good {
  background-color: #28a745;
} /* Green */
.score-bad {
  background-color: #dc3545;
} /* Red */
.score-pending {
  background-color: #ffc107;
  color: #333;
} /* Yellow */

.current-lift .overall-result {
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 15px;
}

.current-lift .overall-result span {
  padding: 8px 15px;
  border-radius: 8px;
  color: white;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

/* Upcoming Lifts Queue */
.upcoming-lifts ul {
  list-style: none;
  padding: 0;
}

.upcoming-lifts li {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1em;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.upcoming-lifts button {
  padding: 8px 15px;
  background-color: #1abc9c; /* Turquoise */
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.upcoming-lifts button:hover {
  background-color: #16a085;
  transform: translateY(-1px);
}

.next-lift-btn {
  display: block;
  width: auto; /* Adjust width to content */
  margin: 20px auto 0; /* Center button */
  padding: 12px 25px;
  background-color: #2980b9; /* Darker blue */
  font-size: 1.1em;
}

.next-lift-btn:hover {
  background-color: #2c3e50;
}

/* All Lifters Section */
.all-lifters-section ul {
  list-style: decimal;
  padding-left: 25px;
}

.all-lifters-section li {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 8px;
  font-size: 1em;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.all-lifters-section li:last-child {
  border-bottom: none;
}

.all-lifters-section li strong {
  color: #2c3e50;
}

/* Weight Class Management / Age Class Management */
.class-list {
  list-style: none;
  padding: 0;
}

.class-list li {
  background-color: #f9f9f9;
  border: 1px solid #eee;
  padding: 10px;
  margin-bottom: 8px;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.95em;
}

.class-list .delete-btn {
  background-color: #e74c3c; /* Red */
  padding: 6px 12px;
  font-size: 0.85em;
}

.class-list .delete-btn:hover {
  background-color: #c0392b;
}

/* Lifter Multi-Class Actions (new styles) */
.lifter-class-actions {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #ddd;
}

.lifter-class-actions details {
  background-color: #eceff1; /* Lighter background for expandable section */
  border: 1px solid #cfd8dc;
  border-radius: 8px;
  padding: 10px;
  margin-top: 10px;
}

.lifter-class-actions summary {
  font-weight: bold;
  cursor: pointer;
  color: #34495e;
}

.class-selector-group {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap; /* Allow wrapping on smaller screens */
}

.class-selector-group select {
  flex-grow: 1;
  min-width: 150px;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #bdc3c7;
}

.class-selector-group button {
  padding: 8px 12px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.2s ease;
}

.class-selector-group button:hover:not(:disabled) {
  opacity: 0.9;
}

.class-selector-group button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.class-selector-group button:first-of-type {
  /* Add button */
  background-color: #2ecc71; /* Green */
  color: white;
}

.class-selector-group button:last-of-type {
  /* Remove button */
  background-color: #e74c3c; /* Red */
  color: white;
}

/* Meet Rankings Section */
.meet-rankings-section {
  text-align: center;
}

.meet-rankings-section .fetch-rankings-btn {
  padding: 10px 20px;
  background-color: #f39c12; /* Orange */
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.1em;
  margin-bottom: 20px;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.meet-rankings-section .fetch-rankings-btn:hover {
  background-color: #e67e22;
  transform: translateY(-1px);
}

.weight-class-rankings {
  margin-top: 30px;
  background-color: #ecf0f1;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.weight-class-rankings h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.6em;
}

.weight-class-rankings table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

.weight-class-rankings th,
.weight-class-rankings td {
  border: 1px solid #bdc3c7;
  padding: 12px;
  text-align: left;
  font-size: 0.95em;
}

.weight-class-rankings th {
  background-color: #34495e;
  color: white;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.weight-class-rankings tbody tr:nth-child(even) {
  background-color: #f5f7f9;
}

.weight-class-rankings tbody tr:hover {
  background-color: #e0e0e0;
}

.weight-class-rankings td strong {
  color: #27ae60; /* Green for total */
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .organizer-container {
    padding: 15px;
    margin: 10px auto;
  }

  h1 {
    font-size: 2.2em;
    margin-bottom: 20px;
  }

  h2 {
    font-size: 1.6em;
    margin-bottom: 15px;
  }

  form {
    grid-template-columns: 1fr; /* Stack inputs on small screens */
  }

  form button {
    grid-column: span 1;
  }

  .add-lifter-section form input[type="date"],
  .add-lifter-section form input[placeholder*="Opener"] {
    grid-column: span 1;
  }

  .current-lift .scores {
    flex-direction: column;
    gap: 10px;
  }

  .current-lift .scores span {
    min-width: unset;
    width: 100%;
  }

  .weight-class-rankings table,
  .weight-class-rankings thead,
  .weight-class-rankings tbody,
  .weight-class-rankings th,
  .weight-class-rankings td,
  .weight-class-rankings tr {
    display: block;
  }

  .weight-class-rankings thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }

  .weight-class-rankings tr {
    border: 1px solid #bdc3c7;
    margin-bottom: 10px;
    border-radius: 8px;
    overflow: hidden;
  }

  .weight-class-rankings td {
    border: none;
    border-bottom: 1px solid #eee;
    position: relative;
    padding-left: 50%;
    text-align: right;
  }

  .weight-class-rankings td:before {
    position: absolute;
    top: 6px;
    left: 6px;
    width: 45%;
    padding-right: 10px;
    white-space: nowrap;
    text-align: left;
    font-weight: bold;
    color: #555;
  }

  .weight-class-rankings td:nth-of-type(1):before {
    content: "Rank:";
  }
  .weight-class-rankings td:nth-of-type(2):before {
    content: "Lifter:";
  }
  .weight-class-rankings td:nth-of-type(3):before {
    content: "Squat:";
  }
  .weight-class-rankings td:nth-of-type(4):before {
    content: "Bench:";
  }
  .weight-class-rankings td:nth-of-type(5):before {
    content: "Deadlift:";
  }
  .weight-class-rankings td:nth-of-type(6):before {
    content: "Total:";
  }

  .weight-class-rankings td:last-child {
    border-bottom: none;
  }

  .class-selector-group {
    flex-direction: column;
    gap: 5px;
  }

  .class-selector-group select,
  .class-selector-group button {
    width: 100%;
  }
}
</style>
