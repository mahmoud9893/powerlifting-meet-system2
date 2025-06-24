    // frontend/powerlifting-frontend/vue.config.js
    // Create this file if it doesn't exist, or modify it if it does.

    const { defineConfig } = require('@vue/cli-service');

    module.exports = defineConfig({
      transpileDependencies: true,
      // IMPORTANT: Set publicPath to '/' for correct asset loading on Netlify.
      // This ensures assets like /js/app.js are requested from the root of the deployed site.
      publicPath: '/', 
      // Other configurations can go here if needed.
    });
    