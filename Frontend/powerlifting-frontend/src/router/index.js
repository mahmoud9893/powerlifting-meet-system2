import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import OrganizerView from "../views/OrganizerView.vue";
import PublicDisplayView from "../views/PublicDisplayView.vue";
import JudgeView from "../views/JudgeView.vue"; // Corrected path after moving the file

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/organizer",
    name: "organizer",
    component: OrganizerView,
  },
  {
    path: "/public",
    name: "public",
    component: PublicDisplayView,
  },
  {
    // Judge App Route
    path: "/judge",
    name: "judge",
    component: JudgeView,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
