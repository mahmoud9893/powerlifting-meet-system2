    <template>
      <nav class="p-4 bg-gray-900 text-white flex justify-center space-x-6 text-xl shadow-lg font-semibold sticky top-0 z-50">
        <router-link to="/" class="hover:text-teal-400 transition-colors duration-200">Home</router-link>
        <router-link to="/organizer" class="hover:text-teal-400 transition-colors duration-200">Organizer</router-link>
        <router-link to="/display" class="hover:text-teal-400 transition-colors duration-200">Public Display</router-link>
        <router-link to="/judge" class="hover:text-teal-400 transition-colors duration-200">Judge Panel</router-link>
      </nav>
      <router-view />
    </template>

    <style>
    /* Global styles for the entire app.
       Ensure these are minimal and don't conflict with Tailwind or component-specific styles.
       Vue CLI might also import a base CSS file, ensure that doesn't conflict.
    */
    body {
        /* These are set in public/index.html now to ensure they apply globally */
        /* font-family: 'Inter', sans-serif; */
        /* background-color: #020617; */
        /* color: #f8fafc; */
    }

    /* Basic styling for router links in nav */
    nav a.router-link-exact-active {
      color: #38b2ac; /* Tailwind 'teal-400' equivalent */
      /* Add any other active link styles here, e.g., border-bottom */
    }
    </style>
    