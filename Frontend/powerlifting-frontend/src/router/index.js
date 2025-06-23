import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import OrganizerView from "../views/OrganizerView.vue";
import PublicDisplayView from "../views/PublicDisplayView.vue";
// Remove the direct import: import JudgesView from '../views/JudgesView.vue'

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView
  },
  {
    path: "/organizer",
    name: "organizer",
    component: OrganizerView
  },
  {
    path: "/display", // Confirmed path for consistency
    name: "display",
    component: PublicDisplayView
  },
  {
    // Judge App Route - Using dynamic import for lazy loading
    path: "/judge",
    name: "judge",
    component: () => import('../views/JudgesView.vue') // This is the key change!
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;
