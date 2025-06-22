// vue.config.js
module.exports = {
  // This will instruct webpack-dev-server to add 'Access-Control-Allow-Origin'
  // to allow other origins to fetch resources during local development.
  // This setting does NOT affect production builds for Netlify.
  // For production, CORS must be configured on your backend.
  devServer: {
    headers: { "Access-Control-Allow-Origin": "*" }
  },

  // Configure linting for production build
  chainWebpack: config => {
    // Disable ESLint enforcement for production builds
    // This will prevent ESLint errors from breaking the build process
    config.module
      .rule('eslint')
      .use('eslint-loader')
      .tap(options => {
        options.emitWarning = true; // Emit warnings instead of errors
        options.failOnError = false; // Do not fail build on ESLint errors
        options.failOnWarning = false; // Do not fail build on ESLint warnings
        return options;
      });
  }
};
