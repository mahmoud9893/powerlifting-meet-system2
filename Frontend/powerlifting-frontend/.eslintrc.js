module.exports = {
  root: true,
  env: {
    node: true
  },
  extends: [
    "plugin:vue/vue3-essential",
    "eslint:recommended",
    "plugin:prettier/recommended" // Ensure Prettier is integrated
  ],
  parserOptions: {
    parser: "@babel/eslint-parser",
    requireConfigFile: false // For @babel/eslint-parser in Vue CLI 5
  },
  rules: {
    "no-console": process.env.NODE_ENV === "production" ? "warn" : "off",
    "no-debugger": process.env.NODE_ENV === "production" ? "warn" : "off",
    // --- Prettier/Formatting Rules Relaxation ---
    "prettier/prettier": [
      "error",
      {
        htmlWhitespaceSensitivity: "ignore", // This helps with line breaks in HTML
        endOfLine: "lf", // Ensure consistent line endings
        singleQuote: false, // Use double quotes where appropriate
        trailingComma: "none", // Explicitly set to 'none' if that's what Netlify's Prettier prefers for these cases
        printWidth: 120, // Increase printWidth to reduce forced line breaks
        arrowParens: "always" // (a) => {} vs a => {}
      }
    ],
    // --- Unused Variables Rule Adjustment ---
    // Configure no-unused-vars to ignore variables starting with an underscore
    "no-unused-vars": [
      "warn",
      {
        argsIgnorePattern: "^_", // Ignore arguments that start with an underscore
        varsIgnorePattern: "^_", // Ignore variables that start with an underscore
        caughtErrorsIgnorePattern: "^_" // Ignore caught errors that start with an underscore
      }
    ],
    // --- Disable problematic Vue-specific formatting rules ---
    "vue/html-self-closing": "off",
    "vue/singleline-html-element-content-newline": "off",
    "vue/multiline-html-element-content-newline": "off",
    "vue/html-indent": "off",
    "vue/max-attributes-per-line": "off", // <-- THIS IS THE CRITICAL CHANGE
    "vue/html-closing-bracket-newline": [
      "error",
      {
        singleline: "never",
        multiline: "always"
      }
    ],
    "vue/html-closing-bracket-spacing": [
      "error",
      {
        startTag: "never",
        endTag: "never",
        selfClosingTag: "always"
      }
    ]
  }
};
