<template>
  <div class="organizer-view container mx-auto p-4">
    <h1 class="text-3xl font-bold mb-6 text-center">Organizer Dashboard</h1>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-semibold mb-4">Meet State</h2>
      <div v-if="meetState" class="mb-4">
        <p>
          <strong class="font-medium">Current State:</strong>
          {{ meetState.current_state }}
        </p>
        <p>
          <strong class="font-medium">Selected Lifter:</strong>
          {{ meetState.selected_lifter_name || "None" }} (ID:
          {{ meetState.selected_lifter_id || "N/A" }})
        </p>
        <p>
          <strong class="font-medium">Selected Lift:</strong>
          {{ meetState.selected_lift_type || "None" }} (Attempt:
          {{ meetState.selected_attempt_number || "N/A" }})
        </p>
        <p>
          <strong class="font-medium">Barbell Weight:</strong>
          {{ meetState.barbell_weight || "N/A" }} kg
        </p>
      </div>
      <div class="space-y-2">
        <button
          @click="updateMeetState('pre_meet')"
          class="btn-primary-outline"
        >
          Set Pre-Meet
        </button>
        <button
          @click="updateMeetState('active')"
          class="btn-primary-outline ml-2"
        >
          Set Active
        </button>
        <button
          @click="updateMeetState('post_meet')"
          class="btn-primary-outline ml-2"
        >
          Set Post-Meet
        </button>
      </div>
    </div>

    <div v-if="currentLift" class="mb-8 p-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-semibold mb-4">Currently Lifting</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p>
            <strong class="font-medium">Lifter:</strong>
            {{ currentLift.lifter_name }} (#{{
              currentLift.lifter_id_number
            }})
          </p>
          <p>
            <strong class="font-medium">Lift Type:</strong>
            {{ currentLift.lift_type }}
          </p>
          <p>
            <strong class="font-medium">Attempt:</strong>
            {{ currentLift.attempt_number }}
          </p>
          <p>
            <strong class="font-medium">Declared Weight:</strong>
            {{ currentLift.declared_weight }} kg
          </p>
          <p>
            <strong class="font-medium">Rack Height:</strong>
            {{ currentLift.rack_height }}
          </p>
        </div>
        <div>
          <p>
            <strong class="font-medium">Status:</strong>
            <span
              :class="{
                'text-green-600': currentLift.status === 'SUCCESS',
                'text-red-600': currentLift.status === 'FAIL',
                'text-yellow-600': currentLift.status === 'PENDING',
              }"
            >
              {{ currentLift.status }}
            </span>
          </p>
          <p>
            <strong class="font-medium">Score:</strong>
            {{ currentLift.score }}
          </p>
          <p>
            <strong class="font-medium">Time Remaining:</strong>
            {{ formatTime(currentLift.time_remaining) }}
          </p>
          <p>
            <strong class="font-medium">Barbell Weight Display:</strong>
            {{ currentLift.barbell_weight_display }} kg
          </p>
        </div>
      </div>

      <div class="mt-6 flex flex-wrap gap-3">
        <button @click="markLift(true)" class="btn-success">Mark Success</button>
        <button @click="markLift(false)" class="btn-danger">Mark Fail</button>
        <button @click="skipLift()" class="btn-secondary">Skip Lift</button>
        <button @click="fetchNextLift()" class="btn-primary">Next Lift</button>
        <button @click="resetLiftTimer()" class="btn-secondary-outline">
          Reset Timer
        </button>
      </div>
      <div class="mt-4">
        <label for="newBarbellWeight" class="block text-sm font-medium text-gray-700">Set Barbell Weight:</label>
        <div class="flex mt-1">
          <input type="number" id="newBarbellWeight" v-model.number="newBarbellWeight"
            class="form-input flex-grow mr-2" placeholder="Enter weight in kg" />
          <button @click="setBarbellWeight()" class="btn-primary-outline">
            Set Weight
          </button>
        </div>
      </div>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-semibold mb-4">Next Lifts in Queue</h2>
      <div v-if="nextLiftsInQueue && nextLiftsInQueue.length > 0">
        <div v-for="lift in nextLiftsInQueue" :key="lift.lift_id"
          class="border-b border-gray-200 py-2 last:border-b-0 flex justify-between items-center">
          <div>
            <p>
              <strong class="font-medium">Lifter:</strong>
              {{ lift.lifter_name }} (#{{ lift.lifter_id_number }})
            </p>
            <p>
              <strong class="font-medium">Lift Type:</strong>
              {{ lift.lift_type }}
            </p>
            <p>
              <strong class="font-medium">Declared Weight:</strong>
              {{ lift.declared_weight }} kg
            </p>
            <p>
              <strong class="font-medium">Attempt:</strong>
              {{ lift.attempt_number }}
            </p>
          </div>
          <button @click="setActiveLift(lift.lift_id)" class="btn-primary-outline">
            Activate
          </button>
        </div>
      </div>
      <p v-else class="text-gray-500">No upcoming lifts in the queue.</p>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-semibold mb-4">Lifter Management</h2>
      <form @submit.prevent="addLifter" class="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label for="lifterName" class="form-label">Name:</label>
          <input type="text" id="lifterName" v-model="newLifter.name" required class="form-input" />
        </div>
        <div>
          <label for="lifterID" class="form-label">Lifter ID Number:</label>
          <input type="text" id="lifterID" v-model="newLifter.lifter_id_number" required class="form-input" />
        </div>
        <div>
          <label for="gender" class="form-label">Gender:</label>
          <select id="gender" v-model="newLifter.gender" required class="form-select">
            <option value="">Select Gender</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>
        <div>
          <label for="birthdate" class="form-label">Birthdate:</label>
          <input type="date" id="birthdate" v-model="newLifter.birthdate" required class="form-input" />
        </div>
        <div>
          <label for="weightClass" class="form-label">Weight Class:</label>
          <select id="weightClass" v-model="newLifter.weight_class_id" class="form-select">
            <option :value="null">No Weight Class</option>
            <option v-for="wc in weightClasses" :key="wc.weight_class_id" :value="wc.weight_class_id">
              {{ wc.name }} ({{ wc.min_weight }}kg - {{ wc.max_weight }}kg)
            </option>
          </select>
        </div>
        <div>
          <label for="ageClass" class="form-label">Age Class:</label>
          <select id="ageClass" v-model="newLifter.age_class_id" class="form-select">
            <option :value="null">No Age Class</option>
            <option v-for="ac in ageClasses" :key="ac.age_class_id" :value="ac.age_class_id">
              {{ ac.name }} ({{ ac.min_age }}-{{ ac.max_age }} years)
            </option>
          </select>
        </div>
        <div class="md:col-span-2 lg:col-span-3 flex justify-end">
          <button type="submit" class="btn-primary">Add Lifter</button>
        </div>
      </form>

      <h3 class="text-xl font-semibold mb-3">All Lifters</h3>
      <div class="overflow-x-auto">
        <table class="min-w-full bg-white border border-gray-200">
          <thead>
            <tr>
              <th class="py-2 px-4 border-b">ID</th>
              <th class="py-2 px-4 border-b">Name</th>
              <th class="py-2 px-4 border-b">Gender</th>
              <th class="py-2 px-4 border-b">Birthdate</th>
              <th class="py-2 px-4 border-b">Age</th>
              <th class="py-2 px-4 border-b">Weight Class</th>
              <th class="py-2 px-4 border-b">Age Class</th>
              <th class="py-2 px-4 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="lifter in allLifters" :key="lifter.lifter_id" class="hover:bg-gray-50">
              <td class="py-2 px-4 border-b">{{ lifter.lifter_id_number }}</td>
              <td class="py-2 px-4 border-b">{{ lifter.name }}</td>
              <td class="py-2 px-4 border-b">{{ lifter.gender }}</td>
              <td class="py-2 px-4 border-b">{{ lifter.birthdate }}</td>
              <td class="py-2 px-4 border-b">{{ lifter.age }}</td>
              <td class="py-2 px-4 border-b">
                {{ lifter.weight_class_name || "N/A" }}
              </td>
              <td class="py-2 px-4 border-b">
                {{ lifter.age_class_name || "N/A" }}
              </td>
              <td class="py-2 px-4 border-b">
                <button @click="deleteLifter(lifter.lifter_id)" class="btn-danger-sm">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-semibold mb-4">Weight Class Management</h2>
      <form @submit.prevent="addWeightClass" class="mb-6 flex space-x-4 items-end">
        <div>
          <label for="wcName" class="form-label">Name:</label>
          <input type="text" id="wcName" v-model="newWeightClass.name" required class="form-input" />
        </div>
        <div>
          <label for="wcMin" class="form-label">Min Weight (kg):</label>
          <input type="number" id="wcMin" v-model.number="newWeightClass.min_weight" required class="form-input"
            step="0.01" />
        </div>
        <div>
          <label for="wcMax" class="form-label">Max Weight (kg):</label>
          <input type="number" id="wcMax" v-model.number="newWeightClass.max_weight" required class="form-input"
            step="0.01" />
        </div>
        <button type="submit" class="btn-primary">Add Weight Class</button>
      </form>

      <h3 class="text-xl font-semibold mb-3">All Weight Classes</h3>
      <div class="overflow-x-auto">
        <table class="min-w-full bg-white border border-gray-200">
          <thead>
            <tr>
              <th class="py-2 px-4 border-b">Name</th>
              <th class="py-2 px-4 border-b">Min Weight (kg)</th>
              <th class="py-2 px-4 border-b">Max Weight (kg)</th>
              <th class="py-2 px-4 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="wc in weightClasses" :key="wc.weight_class_id" class="hover:bg-gray-50">
              <td class="py-2 px-4 border-b">{{ wc.name }}</td>
              <td class="py-2 px-4 border-b">{{ wc.min_weight }}</td>
              <td class="py-2 px-4 border-b">{{ wc.max_weight }}</td>
              <td class="py-2 px-4 border-b">
                <button @click="deleteWeightClass(wc.weight_class_id)" class="btn-danger-sm">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="mb-8 p-6 bg-white rounded-lg shadow-md">
      <h2 class="text-2xl font-semibold mb-4">Age Class Management</h2>
      <form @submit.prevent="addAgeClass" class="mb-6 flex space-x-4 items-end">
        <div>
          <label for="acName" class="form-label">Name:</label>
          <input type="text" id="acName" v-model="newAgeClass.name" required class="form-input" />
        </div>
        <div>
          <label for="acMin" class="form-label">Min Age (years):</label>
          <input type="number" id="acMin" v-model.number="newAgeClass.min_age" required class="form-input" />
        </div>
        <div>
          <label for="acMax" class="form-label">Max Age (years):</label>
          <input type="number" id="acMax" v-model.number="newAgeClass.max_age" required class="form-input" />
        </div>
        <button type="submit" class="btn-primary">Add Age Class</button>
      </form>

      <h3 class="text-xl font-semibold mb-3">All Age Classes</h3>
      <div class="overflow-x-auto">
        <table class="min-w-full bg-white border border-gray-200">
          <thead>
            <tr>
              <th class="py-2 px-4 border-b">Name</th>
              <th class="py-2 px-4 border-b">Min Age (years)</th>
              <th class="py-2 px-4 border-b">Max Age (years)</th>
              <th class="py-2 px-4 border-b">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ac in ageClasses" :key="ac.age_class_id" class="hover:bg-gray-50">
              <td class="py-2 px-4 border-b">{{ ac.name }}</td>
              <td class="py-2 px-4 border-b">{{ ac.min_age }}</td>
              <td class="py-2 px-4 border-b">{{ ac.max_age }}</td>
              <td class="py-2 px-4 border-b">
                <button @click="deleteAgeClass(ac.age_class_id)" class="btn-danger-sm">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const BACKEND_API_URL =
  process.env.VUE_APP_BACKEND_API_URL || "http://localhost:5000";

const meetState = ref(null);
const currentLift = ref(null);
const nextLiftsInQueue = ref([]);
const newBarbellWeight = ref(null);

const allLifters = ref([]);
const newLifter = ref({
  name: "",
  lifter_id_number: "",
  gender: "",
  birthdate: "",
  weight_class_id: null,
  age_class_id: null,
});

const weightClasses = ref([]);
const newWeightClass = ref({ name: "", min_weight: null, max_weight: null });

const ageClasses = ref([]);
const newAgeClass = ref({ name: "", min_age: null, max_age: null });

// Utility to format time
const formatTime = (seconds) => {
  if (typeof seconds !== "number" || isNaN(seconds)) {
    return "00:00";
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes.toString().padStart(2, "0")}:${remainingSeconds
    .toString()
    .padStart(2, "0")}`;
};

// --- API Calls ---

const fetchMeetState = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/meet_state`);
    const data = await response.json();
    meetState.value = data;
  } catch (error) {
    // console.error("Error fetching meet state:", error);
  }
};

const updateMeetState = async (state) => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/set_meet_state`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state: state }),
    });
    if (response.ok) {
      // console.log(`Meet state set to ${state}`);
      fetchMeetState(); // Refresh state
    } else {
      const errorData = await response.json();
      // console.error(
      //   "Failed to update meet state:",
      //   response.status,
      //   errorData
      // );
      alert(
        `Failed to update meet state: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error updating meet state:", error);
    alert("Network error or unexpected error while updating meet state.");
  }
};

const fetchLifters = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters`);
    const data = await response.json();
    allLifters.value = data;
    // Initialize selection states for new lifters
  } catch (error) {
    // console.error("Error fetching lifters:", error);
  }
};

const fetchCurrentLift = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/current_lift`);
    if (response.ok) {
      const data = await response.json();
      currentLift.value = data;
    } else if (response.status === 404) {
      currentLift.value = null; // No current lift
    }
  } catch (error) {
    // console.error("Error fetching current lift:", error);
  }
};

const fetchNextLiftsInQueue = async () => {
  try {
    // Trigger backend queue logic (if any specific endpoint for this)
    // await fetch(`${BACKEND_API_URL}/next_lift_in_queue`); // This was removed in previous iteration, assuming it's not needed as a separate call

    const allLiftsResponse = await fetch(`${BACKEND_API_URL}/lifts`);
    if (allLiftsResponse.ok) {
      const allLifts = await allLiftsResponse.json();
      nextLiftsInQueue.value = allLifts.filter(
        (lift) => lift.status === "PENDING"
      ); // Filter for pending lifts
    } else {
      // console.error(
      //   "Failed to fetch all lifts:",
      //   allLiftsResponse.status,
      //   await allLiftsResponse.json()
      // );
      nextLiftsInQueue.value = [];
    }
  } catch (error) {
    // console.error("Error fetching next lifts in queue:", error);
  }
};

const addLifter = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newLifter.value),
    });
    if (response.ok) {
      const addedLifter = await response.json();
      // console.log("Lifter added successfully:", addedLifter);
      newLifter.value = {
        name: "",
        lifter_id_number: "",
        gender: "",
        birthdate: "",
        weight_class_id: null,
        age_class_id: null,
      };
      fetchLifters(); // Refresh list
    } else {
      const errorData = await response.json();
      // console.error("Failed to add lifter:", response.status, errorData);
      alert(
        `Failed to add lifter: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error adding lifter (network or unexpected):", error);
    alert("Network error or unexpected error while adding lifter.");
  }
};

const setActiveLift = async (liftId) => {
  try {
    const payload = liftId ? { lift_id: liftId } : {};
    const response = await fetch(`${BACKEND_API_URL}/set_active_lift`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (response.ok) {
      const activatedLift = await response.json();
      // console.log("Lift activated:", activatedLift);
      fetchCurrentLift();
      fetchNextLiftsInQueue();
    } else {
      const errorData = await response.json();
      // console.error(
      //   "Failed to set active lift:",
      //   response.status,
      //   errorData
      // );
      alert(
        `Failed to set active lift: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error setting active lift:", error);
    alert("Network error or unexpected error while setting active lift.");
  }
};

const markLift = async (isSuccess) => {
  if (!currentLift.value) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/mark_lift`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lift_id: currentLift.value.lift_id,
        status: isSuccess ? "SUCCESS" : "FAIL",
      }),
    });
    if (response.ok) {
      // console.log(`Lift marked as ${isSuccess ? "Success" : "Fail"}`);
      fetchCurrentLift(); // Refresh current lift status
      fetchNextLiftsInQueue(); // Refresh queue
    } else {
      const errorData = await response.json();
      // console.error("Failed to mark lift:", response.status, errorData);
      alert(`Failed to mark lift: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    // console.error("Error marking lift:", error);
    alert("Network error or unexpected error while marking lift.");
  }
};

const skipLift = async () => {
  if (!currentLift.value) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/skip_lift`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lift_id: currentLift.value.lift_id }),
    });
    if (response.ok) {
      // console.log("Lift skipped.");
      fetchCurrentLift(); // Clear current lift
      fetchNextLiftsInQueue(); // Refresh queue
    } else {
      const errorData = await response.json();
      // console.error("Failed to skip lift:", response.status, errorData);
      alert(`Failed to skip lift: ${errorData.error || response.statusText}`);
    }
  } catch (error) {
    // console.error("Error skipping lift:", error);
    alert("Network error or unexpected error while skipping lift.");
  }
};

const fetchNextLift = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/next_lift`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (response.ok) {
      // console.log("Next lift fetched.");
      fetchCurrentLift(); // Update current lift
      fetchNextLiftsInQueue(); // Update queue
    } else {
      const errorData = await response.json();
      // console.error("Failed to fetch next lift:", response.status, errorData);
      alert(
        `Failed to fetch next lift: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error fetching next lift:", error);
    alert("Network error or unexpected error while fetching next lift.");
  }
};

const resetLiftTimer = async () => {
  if (!currentLift.value) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/reset_lift_timer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lift_id: currentLift.value.lift_id }),
    });
    if (response.ok) {
      // console.log("Lift timer reset.");
      fetchCurrentLift(); // Refresh current lift data to show updated timer
    } else {
      const errorData = await response.json();
      // console.error("Failed to reset timer:", response.status, errorData);
      alert(
        `Failed to reset timer: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error resetting timer:", error);
    alert("Network error or unexpected error while resetting timer.");
  }
};

const setBarbellWeight = async () => {
  if (newBarbellWeight.value === null || isNaN(newBarbellWeight.value)) {
    alert("Please enter a valid weight.");
    return;
  }
  try {
    const response = await fetch(`${BACKEND_API_URL}/set_barbell_weight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weight: newBarbellWeight.value }),
    });
    if (response.ok) {
      // console.log("Barbell weight set successfully.");
      newBarbellWeight.value = null; // Clear input
      fetchMeetState(); // Refresh meet state to show new barbell weight
      fetchCurrentLift(); // Refresh current lift if it relies on barbell weight
    } else {
      const errorData = await response.json();
      // console.error(
      //   "Failed to set barbell weight:",
      //   response.status,
      //   errorData
      // );
      alert(
        `Failed to set barbell weight: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error setting barbell weight:", error);
    alert("Network error or unexpected error while setting barbell weight.");
  }
};

const deleteLifter = async (lifterId) => {
  if (!confirm("Are you sure you want to delete this lifter?")) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/lifters/${lifterId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      // console.log("Lifter deleted successfully!");
      fetchLifters(); // Refresh list
      fetchNextLiftsInQueue(); // Lifter might be in queue
      fetchCurrentLift(); // Lifter might be current
    } else {
      const errorData = await response.json();
      // console.error("Failed to delete lifter:", response.status, errorData);
      alert(
        `Failed to delete lifter: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error deleting lifter:", error);
    alert("Network error or unexpected error while deleting lifter.");
  }
};

const fetchWeightClasses = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/weight_classes`);
    const data = await response.json();
    weightClasses.value = data;
  } catch (error) {
    // console.error("Error fetching weight classes:", error);
  }
};

const addWeightClass = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/weight_classes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newWeightClass.value),
    });
    if (response.ok) {
      // console.log("Weight class added successfully!");
      newWeightClass.value = {
        name: "",
        min_weight: null,
        max_weight: null,
      };
      fetchWeightClasses(); // Refresh list
    } else {
      const errorData = await response.json();
      // console.error(
      //   "Failed to add weight class:",
      //   response.status,
      //   errorData
      // );
      alert(
        `Failed to add weight class: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error adding weight class:", error);
    alert("Network error or unexpected error while adding weight class.");
  }
};

const deleteWeightClass = async (weightClassId) => {
  if (!confirm("Are you sure you want to delete this weight class?")) return;
  try {
    const response = await fetch(
      `${BACKEND_API_URL}/weight_classes/${weightClassId}`,
      {
        method: "DELETE",
      }
    );
    if (response.ok) {
      // console.log("Weight class deleted successfully!");
      fetchWeightClasses();
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      // console.error(
      //   "Failed to delete weight class:",
      //   response.status,
      //   errorData
      // );
      alert(
        `Failed to delete weight class: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error deleting weight class:", error);
    alert("Network error or unexpected error while deleting weight class.");
  }
};

const fetchAgeClasses = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes`);
    const data = await response.json();
    ageClasses.value = data;
  } catch (error) {
    // console.error("Error fetching age classes:", error);
  }
};

const addAgeClass = async () => {
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newAgeClass.value),
    });
    if (response.ok) {
      // console.log("Age class added successfully!");
      newAgeClass.value = { name: "", min_age: null, max_age: null };
      fetchAgeClasses(); // Refresh list
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      // console.error("Failed to add age class:", response.status, errorData);
      alert(
        `Failed to add age class: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error adding age class:", error);
    alert("Network error or unexpected error while adding age class.");
  }
};

const deleteAgeClass = async (ageClassId) => {
  if (!confirm("Are you sure you want to delete this age class?")) return;
  try {
    const response = await fetch(`${BACKEND_API_URL}/age_classes/${ageClassId}`, {
      method: "DELETE",
    });
    if (response.ok) {
      // console.log("Age class deleted successfully!");
      fetchAgeClasses();
      fetchLifters(); // Lifters might be re-assigned, refresh them too
    } else {
      const errorData = await response.json();
      // console.error(
      //   "Failed to delete age class:",
      //   response.status,
      //   errorData
      // );
      alert(
        `Failed to delete age class: ${errorData.error || response.statusText}`
      );
    }
  } catch (error) {
    // console.error("Error deleting age class:", error);
    alert("Network error or unexpected error while deleting age class.");
  }
};

onMounted(() => {
  fetchMeetState();
  fetchCurrentLift();
  fetchNextLiftsInQueue();
  fetchLifters();
  fetchWeightClasses();
  fetchAgeClasses();

  // Set up polling for real-time updates
  setInterval(fetchMeetState, 3000); // Poll every 3 seconds
  setInterval(fetchCurrentLift, 1000); // Poll every 1 second for current lift
  setInterval(fetchNextLiftsInQueue, 5000); // Poll every 5 seconds for queue
});
</script>

<style scoped>
/* Base styling for containers */
.container {
  max-width: 1200px;
}

/* Button Styling */
.btn-primary {
  @apply bg-blue-600 text-white px-5 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

.btn-primary-outline {
  @apply bg-white text-blue-600 border border-blue-600 px-5 py-2 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

.btn-success {
  @apply bg-green-600 text-white px-5 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

.btn-danger {
  @apply bg-red-600 text-white px-5 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

.btn-secondary {
  @apply bg-gray-600 text-white px-5 py-2 rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

.btn-secondary-outline {
  @apply bg-white text-gray-600 border border-gray-600 px-5 py-2 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

.btn-danger-sm {
  @apply bg-red-500 text-white px-3 py-1 text-sm rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition duration-150 ease-in-out;
}

/* Form element styling */
.form-label {
  @apply block text-sm font-medium text-gray-700 mb-1;
}

.form-input,
.form-select {
  @apply mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm;
}
</style>