import js from "@eslint/js";
import globals from "globals";
import unusedImports from "eslint-plugin-unused-imports";
import vuePlugin from "eslint-plugin-vue";
import vueParser from "vue-eslint-parser";

export default [
  {
    ignores: [
      "coverage/**",
      "dist/**",
      "node_modules/**",
      "playwright-report/**",
      "test-results/**",
    ],
  },
  js.configs.recommended,
  ...vuePlugin.configs["flat/essential"],
  {
    files: ["**/*.vue"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        extraFileExtensions: [".vue"],
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "unused-imports": unusedImports,
    },
    rules: {
      "no-console": "off",
      "no-debugger": "error",
      "no-unused-vars": "off",
      "vue/multi-word-component-names": "off",
    },
  },
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "unused-imports": unusedImports,
    },
    rules: {
      "no-console": "off",
      "no-debugger": "error",
      "no-unused-vars": "off",
      "unused-imports/no-unused-imports": "error",
    },
  },
  {
    files: [
      "**/e2e/**/*.js",
      "**/scripts/**/*.mjs",
      "**/tests/**/*.js",
      "*.js",
    ],
    rules: {
      "unused-imports/no-unused-vars": [
        "error",
        {
          args: "after-used",
          argsIgnorePattern: "^_",
          ignoreRestSiblings: true,
          vars: "all",
          varsIgnorePattern: "^_",
        },
      ],
    },
  },
];
